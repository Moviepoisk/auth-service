from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LoginHistoryGet(BaseModel):
    id: UUID | None = Field(
        default=None, description="Уникальный идентификатор истории входа"
    )
    ip: str = Field(..., description="IP-адрес пользователя")
    user_agent: str = Field(..., description="User-Agent пользователя")
    created_at: datetime | None = Field(
        default=None, description="Дата и время создания записи"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": "d550a0d2-23d2-4a68-bd1f-3b6e7b1e55e1",
                "ip": "192.168.1.1",
                "user_agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                + " (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            }
        }
