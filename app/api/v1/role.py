from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.role_helpers import (
    create_role,
    delete_role,
    get_all_roles,
    role_required,
    update_role,
)
from app.core.config import settings
from app.infrastructure.db.database import get_session
from app.schemas.role import RoleCreate, RoleGet, RoleUpdate

router = APIRouter()


@router.get("/roles", response_model=list[RoleGet])
async def list_roles(
    db: AsyncSession = Depends(get_session)
):
    roles_list = await get_all_roles(db)
    return roles_list


@router.post("/roles", response_model=list[RoleGet])
async def create_new_role_endpoint(
    role_data: RoleCreate = Body(...),
    db: AsyncSession = Depends(get_session),
    _=Depends(role_required([settings.super_admin_role_name])),
):
    new_role = await create_role(db, role_data)
    return new_role


@router.delete("/roles", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role_endpoint(
    role_id: UUID = Body(...),
    db: AsyncSession = Depends(get_session),
    _=Depends(role_required([settings.super_admin_role_name])),
):
    await delete_role(db, role_id)


@router.patch("/roles", response_model=RoleGet)
async def update_role_endpoint(
    role_id: UUID = Body(...),
    new_role_data: RoleUpdate = Body(...),
    db: AsyncSession = Depends(get_session),
    _=Depends(role_required([settings.super_admin_role_name])),
):
    updated_role = await update_role(db, role_id, new_role_data)
    return updated_role
