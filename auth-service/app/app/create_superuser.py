from typing import List
import typer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_helpers import register_new_user
from app.auth.role_helpers import create_role, set_user_role
from app.auth.role_repository import RoleRepositoryFactory
from app.auth.user_repository import UserRepositoryFactory
from app.core.config import settings
from app.schemas.role import RoleCreate
from app.schemas.user import UserCreate

app = typer.Typer()


@app.command()
def create_superuser():
    """
    Create superuser.
    """
    with AsyncSession() as db:
        typer.echo("Creating superuser...")
        super_admin_data = UserCreate(
            first_name=settings.super_admin_first_name,
            last_name=settings.super_admin_last_name,
            login=settings.super_admin_login,
            email=settings.super_admin_email,
            password=settings.super_admin_password,
        )
        create_roles(db, settings.roles)
        create_superuser_helper(db, super_admin_data)
        typer.echo("Superuser created successfully!")


def create_roles(db: AsyncSession, roles: List[RoleCreate]) -> None:
    """
    Create roles if they don't exist.
    """
    role_repo = RoleRepositoryFactory(db).get_repository()
    for role_data in roles:
        role = role_repo.get_role_by_name(role_data.name)
        if not role:
            create_role(db, role_data)


def create_superuser_helper(db: AsyncSession, super_admin_data: UserCreate) -> None:
    """
    Helper function to create superuser.
    """
    user_repo = UserRepositoryFactory(db).get_repository()
    user = user_repo.get_user_by_email_or_login(super_admin_data.login)
    role_repo = RoleRepositoryFactory(db).get_repository()
    role = role_repo.get_role_by_name(settings.super_admin_role_name)
    if not user:
        register_new_user(db, super_admin_data)
    if user.role_id is None and role:
        set_user_role(db, user.id, role.id)


if __name__ == "__main__":
    app()
