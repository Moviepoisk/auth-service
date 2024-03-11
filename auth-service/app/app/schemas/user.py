from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    login: str
    first_name: str
    last_name: str
    email: str


class UserCreate(UserBase):
    password: str


class UserGet(UserBase):
    id: UUID

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    user_id: UUID
    role_id: UUID


class UserPasswordUpdate(BaseModel):
    id: UUID
    password: str
