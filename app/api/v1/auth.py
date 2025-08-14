from fastapi import APIRouter,Depends,HTTPException
from schemas import UserBase,UserCreate
from sqlalchemy.orm import Session
from models import User
from utils import hash_password,create_access_token
from db import SessionLocal
from utils.response import success_response, error_response
import uuid

router= APIRouter()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/print-user")
def print_user(user: UserBase):
    print(f"Name: {user.username}, Email: {user.email}")
    return {"message": f"Printed user {user.username} with email {user.email}"}

@router.post("/create-user")
def create_user(body:UserCreate, db :Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == body.email).first()
    if db_user:
        raise HTTPException(status_code=409,detail="User with this email already exists")
    
    hashed_password = hash_password(body.password)
    
    # Create new user
    new_user = User(
        id=uuid.uuid4(),
        name=body.username,
        email=body.email,
        password=hashed_password
    )
    
    # Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate token
    token = create_access_token({"sub": body.email})
    
    # Return success response
    return success_response(
        data={
            "user": {
                "id": str(new_user.id),
                "name": new_user.name,
                "email": new_user.email
            },
            "access_token": token,
            "token_type": "bearer"
        },
        message="User created successfully"
    )


