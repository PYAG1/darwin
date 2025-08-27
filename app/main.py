from typing import Union
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware 

from .api.v1 import auth, chat  # Added chat import
from .utils.response import error_response

app = FastAPI(title="Analyst Agent API", version="1.0.0")

# Static files
STATIC_DIR = Path("static")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(chat.router, prefix="/api/v1/chat")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")


@app.get("/chat")
def chat_page():
    return FileResponse("static/index.html")



@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_content = error_response(
        message=str(exc.detail),
        data=None
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_content
    )