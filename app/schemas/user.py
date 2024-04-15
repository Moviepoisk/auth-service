from uuid import UUID

from pydantic import BaseModel


class UserBase(BaseModel):
    login: str
    first_name: str
    last_name: str
    email: str


class UserLogin(BaseModel):
    login: str
    password: str


class UserCreate(UserBase):
    password: str


class UserGet(UserBase):
    id: UUID

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
