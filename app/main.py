from typing import Union

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware 

from .api.v1 import auth  # Changed to relative import
from .utils.response import error_response  # Changed to relative import

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(auth.router, prefix="/api/v1/auth")

@app.get("/")
def read_root():
    return {"Hello": "World"}



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