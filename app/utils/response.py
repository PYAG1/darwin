from typing import Any, Dict, Optional, List, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class ResponseModel(BaseModel):
    is_success: bool
    data: Optional[Any] = None
    message: str = ""
    meta: Optional[dict] = {}

def success_response(data: Any = None, message: str = "Success") -> Dict:
    return ResponseModel(
        is_success=True,
        data=data,
        message=message,
    ).model_dump()

def error_response(message: str = "Error", data: Any = None) -> Dict:
    return ResponseModel(
        is_success=False,
        data=data,
        message=message,
    ).model_dump() 

def paginated_response(
    items: List[T], 
    total: int, 
    page: int, 
    page_size: int,
    message: str = "Success"
) -> Dict:
    return ResponseModel(
        is_success=True,
        data=items,
        message=message,
        meta={
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size  # Ceiling division
            }
        }
    ).model_dump()