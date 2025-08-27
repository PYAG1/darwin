from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):  # Add BaseModel inheritance
    email: EmailStr
    password: str

class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True  # Changed from orm_mode to from_attributes for Pydantic v2