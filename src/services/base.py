"""Base service with common CRUD operations."""

import uuid
from typing import TypeVar, Generic, Type, Any, Sequence
from sqlalchemy import select, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.core.database import Base


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service class with common CRUD operations.
    
    Provides:
    - get: Get single record by ID
    - get_multi: List records with pagination and sorting
    - create: Create new record
    - update: Update existing record
    - delete: Delete record
    - count: Count records with optional filters
    """
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get(
        self, 
        db: AsyncSession, 
        id: uuid.UUID,
    ) -> ModelType | None:
        """Get a single record by ID."""
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> Sequence[ModelType]:
        """
        Get multiple records with pagination, filtering, and sorting.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field:value pairs for filtering
            sort_by: Field name to sort by
            sort_order: 'asc' or 'desc'
        """
        query = select(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.where(getattr(self.model, field) == value)
        
        # Apply sorting
        if sort_by and hasattr(self.model, sort_by):
            order_func = desc if sort_order == "desc" else asc
            query = query.order_by(order_func(getattr(self.model, sort_by)))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: CreateSchemaType,
        extra_data: dict[str, Any] | None = None,
    ) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Pydantic schema with creation data
            extra_data: Additional data to include
        """
        obj_data = obj_in.model_dump()
        if extra_data:
            obj_data.update(extra_data)
        
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        """
        Update an existing record.
        
        Args:
            db: Database session
            db_obj: Existing database object
            obj_in: Pydantic schema or dict with update data
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(
        self, 
        db: AsyncSession, 
        *, 
        id: uuid.UUID,
    ) -> ModelType | None:
        """
        Delete a record by ID.
        
        Returns the deleted object or None if not found.
        """
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        obj = result.scalar_one_or_none()
        
        if obj:
            await db.delete(obj)
            await db.commit()
        
        return obj
    
    async def count(
        self,
        db: AsyncSession,
        *,
        filters: dict[str, Any] | None = None,
    ) -> int:
        """
        Count records with optional filters.
        """
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.where(getattr(self.model, field) == value)
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def exists(
        self,
        db: AsyncSession,
        *,
        filters: dict[str, Any],
    ) -> bool:
        """Check if a record exists with given filters."""
        count = await self.count(db, filters=filters)
        return count > 0
    
    async def bulk_delete(
        self,
        db: AsyncSession,
        *,
        ids: list[uuid.UUID],
    ) -> list[ModelType]:
        """Delete multiple records by IDs."""
        result = await db.execute(
            select(self.model).where(self.model.id.in_(ids))
        )
        objects = list(result.scalars().all())
        
        for obj in objects:
            await db.delete(obj)
        
        await db.commit()
        return objects
