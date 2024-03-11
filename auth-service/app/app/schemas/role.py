from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class RoleBase(BaseModel):
    name: str
    description: str


class RoleCreate(RoleBase):
    pass


class RoleUpdate(RoleBase):
    id: UUID


class RoleGet(RoleBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
