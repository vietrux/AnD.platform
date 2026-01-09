import uuid
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Vulnbox
from src.schemas.vulnbox import VulnboxCreate, VulnboxUpdate


async def create_vulnbox(
    db: AsyncSession, 
    data: VulnboxCreate,
    path: str,
) -> Vulnbox:
    vulnbox = Vulnbox(
        name=data.name,
        description=data.description,
        path=path,
    )
    db.add(vulnbox)
    await db.commit()
    await db.refresh(vulnbox)
    return vulnbox


async def get_vulnbox(db: AsyncSession, vulnbox_id: uuid.UUID) -> Vulnbox | None:
    result = await db.execute(select(Vulnbox).where(Vulnbox.id == vulnbox_id))
    return result.scalar_one_or_none()


async def get_vulnbox_by_name(db: AsyncSession, name: str) -> Vulnbox | None:
    result = await db.execute(select(Vulnbox).where(Vulnbox.name == name))
    return result.scalar_one_or_none()


async def list_vulnboxes(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 50
) -> list[Vulnbox]:
    result = await db.execute(
        select(Vulnbox).order_by(Vulnbox.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def count_vulnboxes(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(Vulnbox.id)))
    return result.scalar() or 0


async def update_vulnbox(
    db: AsyncSession, 
    vulnbox: Vulnbox, 
    data: VulnboxUpdate
) -> Vulnbox:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vulnbox, field, value)
    await db.commit()
    await db.refresh(vulnbox)
    return vulnbox


async def set_vulnbox_docker_image(
    db: AsyncSession, 
    vulnbox: Vulnbox, 
    docker_image: str
) -> Vulnbox:
    vulnbox.docker_image = docker_image
    await db.commit()
    await db.refresh(vulnbox)
    return vulnbox


async def delete_vulnbox(db: AsyncSession, vulnbox_id: uuid.UUID) -> bool:
    from src.models import Game
    
    vulnbox = await get_vulnbox(db, vulnbox_id)
    if vulnbox:
        # Check if any games use this vulnbox
        result = await db.execute(
            select(Game).where(Game.vulnbox_id == vulnbox_id).limit(1)
        )
        if result.scalar_one_or_none():
            raise ValueError("Cannot delete vulnbox: it is in use by one or more games")
        
        await db.delete(vulnbox)
        await db.commit()
        return True
    return False

