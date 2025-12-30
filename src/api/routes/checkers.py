import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db, get_settings
from src.schemas import DeleteResponse, MessageResponse
from src.schemas.checker_crud import (
    CheckerCreate,
    CheckerUpdate,
    CheckerResponse,
    CheckerListResponse,
)
from src.services import checker_crud_service


router = APIRouter(prefix="/checkers", tags=["checkers"])


class ValidateResponse(BaseModel):
    valid: bool
    message: str


@router.post("", response_model=CheckerResponse, status_code=201)
async def create_checker(
    name: str = Query(..., min_length=1, max_length=100),
    description: str | None = Query(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    existing = await checker_crud_service.get_checker_by_name(db, name)
    if existing:
        raise HTTPException(status_code=400, detail="Checker name already exists")
    
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="File must be a Python file")
    
    settings = get_settings()
    checker_dir = Path(settings.upload_dir) / "checkers"
    checker_dir.mkdir(parents=True, exist_ok=True)
    
    checker_id = uuid.uuid4()
    checker_path = checker_dir / f"{checker_id}_checker.py"
    content = await file.read()
    checker_path.write_bytes(content)
    
    module_name = f"uploads.checkers.{checker_id}_checker"
    
    data = CheckerCreate(name=name, description=description)
    checker = await checker_crud_service.create_checker(
        db, data, str(checker_path), module_name
    )
    return checker


@router.get("", response_model=CheckerListResponse)
async def list_checkers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    checkers = await checker_crud_service.list_checkers(db, skip, limit)
    total = await checker_crud_service.count_checkers(db)
    
    return CheckerListResponse.create(
        items=[CheckerResponse.model_validate(c) for c in checkers],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{checker_id}", response_model=CheckerResponse)
async def get_checker(
    checker_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    checker = await checker_crud_service.get_checker(db, checker_id)
    if not checker:
        raise HTTPException(status_code=404, detail="Checker not found")
    return checker


@router.patch("/{checker_id}", response_model=CheckerResponse)
async def update_checker(
    checker_id: uuid.UUID,
    data: CheckerUpdate,
    db: AsyncSession = Depends(get_db),
):
    checker = await checker_crud_service.get_checker(db, checker_id)
    if not checker:
        raise HTTPException(status_code=404, detail="Checker not found")
    
    if data.name:
        existing = await checker_crud_service.get_checker_by_name(db, data.name)
        if existing and existing.id != checker_id:
            raise HTTPException(status_code=400, detail="Checker name already exists")
    
    return await checker_crud_service.update_checker(db, checker, data)


@router.delete("/{checker_id}", response_model=DeleteResponse)
async def delete_checker(
    checker_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    checker = await checker_crud_service.get_checker(db, checker_id)
    if not checker:
        raise HTTPException(status_code=404, detail="Checker not found")
    
    await checker_crud_service.delete_checker(db, checker_id)
    return DeleteResponse(deleted_id=checker_id)


@router.post("/{checker_id}/validate", response_model=ValidateResponse)
async def validate_checker(
    checker_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    checker = await checker_crud_service.get_checker(db, checker_id)
    if not checker:
        raise HTTPException(status_code=404, detail="Checker not found")
    
    valid, message = await checker_crud_service.validate_checker_syntax(checker.file_path)
    
    return ValidateResponse(valid=valid, message=message)
