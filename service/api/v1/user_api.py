from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

from utils.custom_logger import CustomLogger
import logging

router = APIRouter(prefix='/users', tags=['users'])

logger = CustomLogger(
    name="user_api",
    log_level=logging.INFO,
    format_style="simple"
)

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True

# Mock database
fake_users_db = []

@router.post("/", response_model=User)
async def create_user(user: UserCreate):
    logger.info(f"Creating user: {user.username}")
    user_dict = user.dict()
    user_dict['id'] = len(fake_users_db) + 1
    user_dict['is_active'] = True
    # In a real app, hash the password
    fake_users_db.append(user_dict)
    return user_dict

@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int):
    logger.info(f"Reading user: {user_id}")
    for user in fake_users_db:
        if user['id'] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")
