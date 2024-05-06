from uuid import UUID

from pydantic import BaseModel


class UserLogin(BaseModel):
    login: str
    password: str


class UserCreate(BaseModel):
    password: str
    login: str
    first_name: str
    last_name: str
    email: str


class UserGet(BaseModel):
    id: UUID
    login: str
    first_name: str
    last_name: str
    email: str
    
    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    user_id: UUID
    role_id: UUID


class UserLoginPasswordUpdate(BaseModel):  # форма обновления
    login: str
    password: str


class UserLoginPasswordUpdateDb(BaseModel):
    login: str
    encrypted_password: str
