
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.auth.role_helpers import create_role, set_user_role
from app.auth.auth_helpers import register_new_user
from app.schemas.role import RoleCreate
from app.schemas.user import UserCreate
from app.auth.user_repository import UserRepositoryFactory
from app.auth.role_repository import RoleRepositoryFactory

# создание базовых ролей
async def create_roles(db: AsyncSession) -> None:
    roles = [
        RoleCreate(name=settings.super_admin_role_name, description=settings.super_admin_role_description),
        RoleCreate(name=settings.admin_role_name, description=settings.admin_role_description),
        RoleCreate(name=settings.user_role_name, description=settings.user_role_description),
        RoleCreate(name=settings.subscriber_role_name, description=settings.subscriber_role_description),
        RoleCreate(name=settings.guest_role_name, description=settings.guest_role_description),
    ]
    role_repo = RoleRepositoryFactory(db).get_repository()
    for role_data in roles:
        role = await role_repo.get_role_by_name(role_data.name)
        if not role:
            await create_role(db, role_data)

# создание суперпользователя
async def create_superuser(db: AsyncSession) -> None:
    super_admin_data = UserCreate(
        first_name=settings.super_admin_first_name,
        last_name=settings.super_admin_last_name,
        login=settings.super_admin_login,
        email=settings.super_admin_email,
        password=settings.super_admin_password
    )
    user_repo = UserRepositoryFactory(db).get_repository()
    user = await user_repo.get_user_by_email_or_login(super_admin_data.login)
    role_repo = RoleRepositoryFactory(db).get_repository()
    role = await role_repo.get_role_by_name(settings.super_admin_role_name)
    if not user:
        await register_new_user(db, super_admin_data)
    if user.role_id is None and role:
        await set_user_role(db, user.id, role.id)
