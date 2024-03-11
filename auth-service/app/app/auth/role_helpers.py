from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import RoleDbModel
from app.auth.role_repository import RoleRepositoryFactory
from app.auth.user_repository import UserRepositoryFactory
from app.auth.auth_helpers import get_current_session_user
from app.infrastructure.db.database import get_session
from app.schemas.user import UserCreate
from app.schemas.role import RoleGet, RoleCreate, RoleUpdate
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from uuid import UUID

OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="v1/tokens")

async def get_current_session_user_role(
        db: AsyncSession = Depends(get_session),
        token: str = Depends(OAUTH2_SCHEME)
) -> Optional[RoleDbModel]:
    user = await get_current_session_user(db, token)
    if not user:
        return None
    role_repo = RoleRepositoryFactory(db).get_repository()
    role = await role_repo.get_role_by_user_id(user.id)
    return role


def role_required(allowed_roles: list[str]):
    async def role_checker(
        role: Optional[RoleGet] = Depends(get_current_session_user_role),
    ):
        if not role or role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
    return role_checker

async def set_user_role(db : AsyncSession, user_id: UUID, role_id: UUID)-> Optional[UserCreate]:
    role_repo = RoleRepositoryFactory(db).get_repository()
    user_repo = UserRepositoryFactory(db).get_repository()

    # Fetch the user to ensure it exists
    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Fetch the current role to ensure it exists
    role = await role_repo.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Update the user's role

    updated_user = await user_repo.update_user(user_id=user.id, role_id=role.id)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role update failed")

    return updated_user

async def create_role(db : AsyncSession, role_data: RoleCreate)-> Optional[RoleGet]:
    role_repo = RoleRepositoryFactory(db).get_repository()
    
    # Fetch the new role to ensure it not exists
    role = await role_repo.get_role_by_name(role_data.name)
    if role:
        return None
    # Create new Role
    role = await role_repo.create_role(name=role_data.name, description=role_data.description)
    if not role:
        return None

    return role

async def delete_role(db: AsyncSession, role_id: UUID)-> Optional[RoleGet]:
    role_repo = RoleRepositoryFactory(db).get_repository()
    role = await role_repo.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    await role_repo.delete_role(role_id)
    return role

async def update_role(db: AsyncSession, role_id: UUID, role_data: RoleUpdate)-> Optional[RoleGet]:
    role_repo = RoleRepositoryFactory(db).get_repository()
    role = await role_repo.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    await role_repo.update_role(role_id, role_data)
    return role

async def get_all_roles(db: AsyncSession) -> list[RoleGet]:
    role_repo = RoleRepositoryFactory(db).get_repository()
    roles = await role_repo.get_all_roles()
    roles_list = [RoleGet.from_orm(role) for role in roles]  # Преобразование в Pydantic объекты
    return roles_list