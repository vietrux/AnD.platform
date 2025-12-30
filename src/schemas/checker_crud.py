import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from src.schemas.common import PaginatedResponse


class CheckerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class CheckerUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CheckerResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    file_path: str
    module_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class CheckerListResponse(PaginatedResponse[CheckerResponse]):
    pass
