import uuid
from typing import Generic, TypeVar
from pydantic import BaseModel


T = TypeVar("T")


class DeleteResponse(BaseModel):
    deleted_id: uuid.UUID
    message: str = "Resource deleted successfully"


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool
    
    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        skip: int = 0,
        limit: int = 50,
    ) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total,
        )
