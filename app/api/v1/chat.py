
import json
import uuid
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from google.genai.types import Part, Content, Blob
from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.genai import types

from app.agent.analyst_agent.agent import root_agent
from app.db import SessionLocal
from app.models import User
from app.utils.auth import verify_access_token
from app.utils.response import success_response, error_response

router = APIRouter()

# Store active sessions
active_sessions: Dict[str, LiveRequestQueue] = {}

APP_NAME = "Analyst Agent Chat"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(token: str, db: Session = Depends(get_db)):
    """Get current user from JWT token"""
    try:
        # You'll need to implement verify_access_token in your auth utils
        payload = verify_access_token(token)
        user_email = payload.get("sub")
        if user_email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.email == user_email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


async def start_agent_session(user_id: str):
    """Starts an agent session"""
    
    # Create a Runner
    runner = InMemoryRunner(
        app_name=APP_NAME,
        agent=root_agent,
    )

    # Create a Session
    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
    )

    # Set response modality to TEXT only
    run_config = RunConfig(
        response_modalities=["TEXT"],
        session_resumption=types.SessionResumptionConfig()
    )

    # Create a LiveRequestQueue for this session
    live_request_queue = LiveRequestQueue()

    # Start agent session
    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    return live_events, live_request_queue


async def agent_to_client_sse(live_events):
    """Agent to client communication via SSE"""
    async for event in live_events:
        # If the turn complete or interrupted, send it
        if event.turn_complete or event.interrupted:
            message = {
                "type": "control",
                "turn_complete": event.turn_complete,
                "interrupted": event.interrupted,
            }
            yield f"data: {json.dumps(message)}\n\n"
            print(f"[AGENT TO CLIENT]: {message}")
            continue

        # Read the Content and its first Part
        part: Part = (
            event.content and event.content.parts and event.content.parts[0]
        )
        if not part:
            continue

        # If it's text and a partial text, send it
        if part.text and event.partial:
            message = {
                "type": "text",
                "mime_type": "text/plain",
                "data": part.text,
                "partial": True
            }
            yield f"data: {json.dumps(message)}\n\n"
            print(f"[AGENT TO CLIENT]: text/plain: {message}")
        
        # If it's completed text, send it
        elif part.text and not event.partial:
            message = {
                "type": "text", 
                "mime_type": "text/plain",
                "data": part.text,
                "partial": False
            }
            yield f"data: {json.dumps(message)}\n\n"
            print(f"[AGENT TO CLIENT]: text/plain complete: {message}")


@router.get("/stream/{user_id}")
async def chat_stream_endpoint(user_id: str):
    """SSE endpoint for agent to client communication"""
    
    # Start agent session
    live_events, live_request_queue = await start_agent_session(user_id)

    # Store the request queue for this user
    active_sessions[user_id] = live_request_queue

    print(f"Client {user_id} connected via SSE")

    def cleanup():
        live_request_queue.close()
        if user_id in active_sessions:
            del active_sessions[user_id]
        print(f"Client {user_id} disconnected from SSE")

    async def event_generator():
        try:
            async for data in agent_to_client_sse(live_events):
                yield data
        except Exception as e:
            print(f"Error in SSE stream: {e}")
            error_message = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_message)}\n\n"
        finally:
            cleanup()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.post("/send/{user_id}")
async def send_message_endpoint(user_id: str, request: Request):
    """HTTP endpoint for client to agent communication"""

    # Get the live request queue for this user
    live_request_queue = active_sessions.get(user_id)
    if not live_request_queue:
        return error_response(message="Session not found. Please connect to the stream first.")

    # Parse the message
    message = await request.json()
    mime_type = message.get("mime_type", "text/plain")
    data = message.get("data", "")

    try:
        # Send the message to the agent (text only)
        if mime_type == "text/plain":
            content = Content(role="user", parts=[Part.from_text(text=data)])
            live_request_queue.send_content(content=content)
            print(f"[CLIENT TO AGENT]: {data}")
        else:
            return error_response(message=f"Mime type not supported: {mime_type}. Only text/plain is supported.")

        return success_response(message="Message sent successfully")
        
    except Exception as e:
        print(f"Error sending message: {e}")
        return error_response(message=f"Failed to send message: {str(e)}")


@router.post("/start-session")
async def start_session_endpoint(request: Request):
    """Start a new chat session"""
    body = await request.json()
    
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    try:
        # Pre-initialize the session
        _, live_request_queue = await start_agent_session(session_id)
        
        # Store it temporarily (will be replaced when streaming starts)
        active_sessions[session_id] = live_request_queue
        
        return success_response(
            data={
                "session_id": session_id,
                "stream_url": f"/api/v1/chat/stream/{session_id}",
                "send_url": f"/api/v1/chat/send/{session_id}"
            },
            message="Chat session started successfully"
        )
        
    except Exception as e:
        print(f"Error starting session: {e}")
        return error_response(message=f"Failed to start session: {str(e)}")


@router.delete("/end-session/{user_id}")
async def end_session_endpoint(user_id: str):
    """End a chat session"""
    
    live_request_queue = active_sessions.get(user_id)
    if not live_request_queue:
        return error_response(message="Session not found")
    
    try:
        # Close the session
        live_request_queue.close()
        del active_sessions[user_id]
        
        return success_response(message="Session ended successfully")
        
    except Exception as e:
        print(f"Error ending session: {e}")
        return error_response(message=f"Failed to end session: {str(e)}")


@router.get("/active-sessions")
async def get_active_sessions():
    """Get list of active chat sessions"""
    return success_response(
        data={
            "active_sessions": list(active_sessions.keys()),
            "count": len(active_sessions)
        },
        message="Active sessions retrieved successfully"
    )
