from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


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
