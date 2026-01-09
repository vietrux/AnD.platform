import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db
from src.schemas import DeleteResponse
from src.schemas.vulnbox import (
    VulnboxCreate,
    VulnboxUpdate,
    VulnboxResponse,
    VulnboxListResponse,
)
from src.services import vulnbox_service, docker_service


router = APIRouter(prefix="/vulnboxes", tags=["vulnboxes"])


@router.post("", response_model=VulnboxResponse, status_code=201)
async def create_vulnbox(
    name: str = Query(..., min_length=1, max_length=100),
    description: str | None = Query(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    existing = await vulnbox_service.get_vulnbox_by_name(db, name)
    if existing:
        raise HTTPException(status_code=400, detail="Vulnbox name already exists")
    
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a ZIP archive")
    
    content = await file.read()
    vulnbox_id = uuid.uuid4()
    vulnbox_path = await docker_service.extract_vulnbox(vulnbox_id, content)
    
    data = VulnboxCreate(name=name, description=description)
    vulnbox = await vulnbox_service.create_vulnbox(db, data, vulnbox_path)
    return vulnbox


@router.get("", response_model=VulnboxListResponse)
async def list_vulnboxes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    vulnboxes = await vulnbox_service.list_vulnboxes(db, skip, limit)
    total = await vulnbox_service.count_vulnboxes(db)
    
    return VulnboxListResponse.create(
        items=[VulnboxResponse.model_validate(v) for v in vulnboxes],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{vulnbox_id}", response_model=VulnboxResponse)
async def get_vulnbox(
    vulnbox_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    vulnbox = await vulnbox_service.get_vulnbox(db, vulnbox_id)
    if not vulnbox:
        raise HTTPException(status_code=404, detail="Vulnbox not found")
    return vulnbox


@router.patch("/{vulnbox_id}", response_model=VulnboxResponse)
async def update_vulnbox(
    vulnbox_id: uuid.UUID,
    data: VulnboxUpdate,
    db: AsyncSession = Depends(get_db),
):
    vulnbox = await vulnbox_service.get_vulnbox(db, vulnbox_id)
    if not vulnbox:
        raise HTTPException(status_code=404, detail="Vulnbox not found")
    
    if data.name:
        existing = await vulnbox_service.get_vulnbox_by_name(db, data.name)
        if existing and existing.id != vulnbox_id:
            raise HTTPException(status_code=400, detail="Vulnbox name already exists")
    
    return await vulnbox_service.update_vulnbox(db, vulnbox, data)


@router.delete("/{vulnbox_id}", response_model=DeleteResponse)
async def delete_vulnbox(
    vulnbox_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    vulnbox = await vulnbox_service.get_vulnbox(db, vulnbox_id)
    if not vulnbox:
        raise HTTPException(status_code=404, detail="Vulnbox not found")
    
    try:
        await vulnbox_service.delete_vulnbox(db, vulnbox_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return DeleteResponse(deleted_id=vulnbox_id)

