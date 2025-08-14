from typing import Union

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from api.v1 import auth
from utils.response import error_response

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1/auth")



@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # This will use your standardized format with is_success=False
    error_content = error_response(
        message=str(exc.detail),
        data=None
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_content
    )