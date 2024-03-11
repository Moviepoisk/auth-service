# app.infrastructure.db.crud_users.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.users import UsersDbModel
import uuid

async def create_user(
    db: AsyncSession,
    email: str,
    login: str,
    first_name: str,
    last_name: str,
    encrypted_password: bytes,
    encrypted_session_key: bytes,
    public_key: bytes,
    private_key: bytes,  # Добавлено для тестирования, не рекомендуется хранить в базе данных
    role_id: uuid.UUID | None = None
) -> UsersDbModel:
    new_user = UsersDbModel(
        email=email,
        login=login,
        first_name=first_name,
        last_name=last_name,
        encrypted_password=encrypted_password,
        #encrypted_session_key=encrypted_session_key,
        #public_key=public_key,
        #private_key=private_key,  # Обратите внимание на риски безопасности
        role_id=role_id
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_by_email_or_login(async_session: AsyncSession, identifier: str):
    # Попытка найти пользователя по email
    result = await async_session.execute(select(UsersDbModel).where(UsersDbModel.email == identifier))
    user = result.scalars().first()
    if user:
        return user
    
    # Если пользователь не найден по email, попытка найти по логину
    result = await async_session.execute(select(UsersDbModel).where(UsersDbModel.login == identifier))
    user = result.scalars().first()
    if user:
        return user
    return None

async def get_user_by_id(async_session: AsyncSession, user_id: uuid.UUID) -> UsersDbModel:
    result = await async_session.execute(select(UsersDbModel).where(UsersDbModel.id == user_id))
    user = result.scalars().first()
    return user

async def update_user(
    async_session: AsyncSession,
    user_id: uuid.UUID,
    email: str = None,
    login: str = None,
    first_name: str = None,
    last_name: str = None,
    encrypted_password: str = None,  # предполагается, что это уже зашифрованный пароль
    role_id: uuid.UUID = None
) -> UsersDbModel:
    # Попытка получить пользователя по ID
    user = await async_session.get(UsersDbModel, user_id)
    if user is None:
        return None
    
    # Обновление атрибутов пользователя, если они предоставлены
    if email is not None:
        user.email = email
    if login is not None:
        user.login = login
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if encrypted_password is not None:
        user.encrypted_password = encrypted_password  # Предполагается, что пароль уже зашифрован
    if role_id is not None:
        user.role_id = role_id

    async_session.add(user)
    await async_session.commit()  # Явно выполняем commit изменений
    await async_session.refresh(user)  # Обновляем состояние объекта user в соответствии с базой данных

    return user

async def delete_user(async_session: AsyncSession, user_id: uuid.UUID) -> bool:
    user = await async_session.get(UsersDbModel, user_id)
    if user:
        await async_session.delete(user)
        await async_session.commit()
        return True
    return False

