from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.users import RoleDbModel, UsersDbModel
import uuid


async def create_role(db: AsyncSession, name: str, description: str) -> None:
    # Проверяем, существует ли уже роль с таким именем
    result = await db.execute(select(RoleDbModel).where(RoleDbModel.name == name))
    role = result.scalars().first()
    
    # Если роль уже существует, просто возвращаемся из функции
    if role:
        print(f"Role '{name}' already exists.")
        return role
    
    # Если роль не существует, создаем новую
    role = RoleDbModel(name=name, description=description)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def get_role_by_id(db: AsyncSession, role_id: uuid.UUID) -> RoleDbModel:
    result = await db.execute(select(RoleDbModel).where(RoleDbModel.id == role_id))
    return result.scalars().first()


async def get_role_by_name(db: AsyncSession, name: str) -> RoleDbModel:
    result = await db.execute(select(RoleDbModel).where(RoleDbModel.name == name))
    return result.scalars().first()

async def update_role(db: AsyncSession, role_id: uuid.UUID, **kwargs) -> RoleDbModel:
    result = await db.execute(select(RoleDbModel).where(RoleDbModel.id == role_id))
    role = result.scalars().first()
    if role:
        for key, value in kwargs.items():
            setattr(role, key, value)
        await db.commit()
        return role
    return None

async def delete_role(db: AsyncSession, role_id: uuid.UUID) -> bool:
    result = await db.execute(select(RoleDbModel).where(RoleDbModel.id == role_id))
    role = result.scalars().first()
    if role:
        await db.delete(role)
        await db.commit()
        return True
    return False

async def get_role_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> RoleDbModel | None:
    # Прежде всего, извлекаем пользователя по его ID
    result = await db.execute(select(UsersDbModel).where(UsersDbModel.id == user_id))
    user = result.scalars().first()
    
    # Если пользователь найден, извлекаем его роль
    if user:
        role_result = await db.execute(select(RoleDbModel).where(RoleDbModel.id == user.role_id))
        role = role_result.scalars().first()
        return role
    
    return None

async def get_all_roles(db: AsyncSession) -> list[RoleDbModel]:
    result = await db.execute(select(RoleDbModel))
    roles = result.scalars().all()
    return roles