import uuid
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Checker
from src.schemas.checker_crud import CheckerCreate, CheckerUpdate


async def create_checker(
    db: AsyncSession, 
    data: CheckerCreate,
    file_path: str,
    module_name: str,
) -> Checker:
    checker = Checker(
        name=data.name,
        description=data.description,
        file_path=file_path,
        module_name=module_name,
    )
    db.add(checker)
    await db.commit()
    await db.refresh(checker)
    return checker


async def get_checker(db: AsyncSession, checker_id: uuid.UUID) -> Checker | None:
    result = await db.execute(select(Checker).where(Checker.id == checker_id))
    return result.scalar_one_or_none()


async def get_checker_by_name(db: AsyncSession, name: str) -> Checker | None:
    result = await db.execute(select(Checker).where(Checker.name == name))
    return result.scalar_one_or_none()


async def list_checkers(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 50
) -> list[Checker]:
    result = await db.execute(
        select(Checker).order_by(Checker.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def count_checkers(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(Checker.id)))
    return result.scalar() or 0


async def update_checker(
    db: AsyncSession, 
    checker: Checker, 
    data: CheckerUpdate
) -> Checker:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(checker, field, value)
    await db.commit()
    await db.refresh(checker)
    return checker


async def delete_checker(db: AsyncSession, checker_id: uuid.UUID) -> bool:
    from src.models import Game
    
    checker = await get_checker(db, checker_id)
    if checker:
        # Check if any games use this checker
        result = await db.execute(
            select(Game).where(Game.checker_id == checker_id).limit(1)
        )
        if result.scalar_one_or_none():
            raise ValueError("Cannot delete checker: it is in use by one or more games")
        
        await db.delete(checker)
        await db.commit()
        return True
    return False


async def validate_checker_syntax(file_path: str) -> tuple[bool, str]:
    import ast
    try:
        with open(file_path, "r") as f:
            source = f.read()
        ast.parse(source)
        return True, "Syntax is valid"
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except FileNotFoundError:
        return False, "Checker file not found"
