from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class TokenBase(BaseModel):
    token_type: str

class AcessToken(TokenBase):
    access_token: str

class RefreshToken(TokenBase):
    refresh_token: str

class Tokens(AcessToken, RefreshToken):
    pass

class AccessTokenData(BaseModel):
    login: Optional[str] = None

class RefreshTokenData(BaseModel):
    login: Optional[str] = None

class RefreshTokenDb(BaseModel):
    id: UUID
    token: str
    user_id: UUID
    expires_at: datetime
    revoked: bool

    class Config:
        from_attributes = True



