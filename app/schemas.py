from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin():
    email:EmailStr
    password:str

class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True