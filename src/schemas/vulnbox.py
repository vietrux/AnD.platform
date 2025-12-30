import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from src.schemas.common import PaginatedResponse


class VulnboxCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class VulnboxUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class VulnboxResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    path: str
    docker_image: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class VulnboxListResponse(PaginatedResponse[VulnboxResponse]):
    pass
