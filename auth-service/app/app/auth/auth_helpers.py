# Import necessary modules and classes
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.encryption_facade import EncryptionFacade
from app.auth.encryption_repository import KeyStorageRepositoryFactory
from app.auth.login_history_repository import LoginHistoryRepositoryFactory
from app.auth.token_repository import RefreshTokenRepositoryFactory
from app.auth.token_strategy import AccessTokenStrategy, RefreshTokenStrategy
from app.auth.user_repository import UserRepositoryFactory
from app.core.config import settings
from app.exceptions.exceptions import (
    get_database_error_exception,
    get_incorrect_credentials_exception,
    get_token_validation_exception,
    get_user_already_exists,
    get_user_not_found_exception,
)
from app.schemas.user import UserCreate, UserGet, UserLoginPasswordUpdate


async def get_client_details(request: Request):
    client_host = request.client.host
    user_agent = request.headers.get("User-Agent")
    return {"ip": client_host, "user_agent": user_agent}


async def register_new_user(db: AsyncSession, user_data: UserCreate) -> str:
    user_repo = await UserRepositoryFactory(db).get_repository()
    user = await user_repo.get_user_by_email_or_login(user_data.login)
    if user:
        raise get_user_already_exists("User with this login already exists")
    user = await user_repo.get_user_by_email_or_login(user_data.email)
    if user:
        raise get_user_already_exists("User with this email already exists")

    encryption_facade = EncryptionFacade()
    generated_keys = await encryption_facade.generate_keys()
    encrypted_password = await encryption_facade.encrypt_data(
        user_data.password, generated_keys["session_key"]
    )

    # Создание и сохранение нового пользователя в базу данных
    new_user = await user_repo.create_user(
        {
            "login": user_data.login,
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "encrypted_password": encrypted_password,
        }
    )
    if not new_user:
        raise get_database_error_exception()

    keys_repo = await KeyStorageRepositoryFactory(db).get_repository()
    new_keys = await keys_repo.save_keys(
        user_id=new_user.id,
        private_key=generated_keys["private_key"].export_key(),
        public_key=generated_keys["public_key"].export_key(),
        encrypted_session_key=generated_keys["encrypted_session_key"],
    )
    if not new_keys:
        raise get_database_error_exception()

    login_history_repo = LoginHistoryRepositoryFactory(db).get_repository()
    await login_history_repo.create_login_history(
        user_id=new_user.id, ip="127.0.0.1", user_agent="test"
    )
    return new_user.id


async def authenticate_user(
    db: AsyncSession, email_or_login: str, password: str
) -> Optional[UserGet]:
    user_repo = await UserRepositoryFactory(db).get_repository()
    user = await user_repo.get_user_by_email_or_login(email_or_login)
    if not user:
        raise get_user_not_found_exception()
    # инициализировать encryption_repository
    encryption_repository = await KeyStorageRepositoryFactory(db).get_repository()
    # получим ключи
    user_keys = await encryption_repository.get_keys(user.id)
    if not user_keys:
        # to do : только восстановление через смену пароля
        raise get_incorrect_credentials_exception()

    encryption_facade = EncryptionFacade()
    private_key = await encryption_facade.import_rsa_key(user_keys.private_key)

    decrypted_session_key = await encryption_facade.decrypt_session_key(
        user_keys.encrypted_session_key, private_key
    )
    decrypted_password = await encryption_facade.decrypt_data(
        user.encrypted_password, decrypted_session_key
    )

    # Compare the provided password with the decrypted password
    if decrypted_password != password:
        # Handle authentication failure
        raise get_incorrect_credentials_exception()

    login_history_repo = LoginHistoryRepositoryFactory(db).get_repository()
    await login_history_repo.create_login_history(
        user.id, ip="127.0.0.1", user_agent="test"
    )

    return UserGet.from_orm(user)


async def create_access_and_refresh_tokens(db: AsyncSession, login: str):
    # Assuming you have a method to get the user by login
    user_repo = await UserRepositoryFactory(db).get_repository()
    user = await user_repo.get_user_by_email_or_login(login)
    if not user:
        raise get_user_not_found_exception()

    access_token_strategy = AccessTokenStrategy()
    refresh_token_strategy = RefreshTokenStrategy()

    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    refresh_token_expires = timedelta(days=settings.jwt_refresh_token_expire_days)
    refresh_token_expires_at = datetime.utcnow() + refresh_token_expires

    access_token = await access_token_strategy.create_token(
        data={"sub": login}, expires_delta=access_token_expires
    )

    refresh_token = await refresh_token_strategy.create_token(
        data={"sub": login}, expires_delta=refresh_token_expires
    )

    # Сохраняем токены в базу данных
    tokens_repo = await RefreshTokenRepositoryFactory(db).get_repository()
    await tokens_repo.delete_refresh_token(user.id)
    await tokens_repo.create_refresh_token(
        user_id=user.id, token=access_token, expires_at=refresh_token_expires_at
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def refresh_user_tokens(refresh_token: str, db: AsyncSession):
    # TODO проверить какой тип токена нужно проверять, access или refresh
    # изменить название метода на более понятное
    # Верифицируем refresh токен
    refresh_token_strategy = RefreshTokenStrategy()
    refresh_token_verefied = await refresh_token_strategy.verify_token(refresh_token)
    if not refresh_token_verefied:
        raise get_token_validation_exception()

    refresh_token_updated = await create_access_and_refresh_tokens(
        db, refresh_token_verefied.login
    )

    return refresh_token_updated


async def revoke_refresh_token(db: AsyncSession, acesss_token: str):
    access_token_strategy = AccessTokenStrategy()
    # Верифицируем access токен текущей сессии
    acesss_token_verefied = await access_token_strategy.verify_token(acesss_token)
    if not acesss_token_verefied:
        raise get_token_validation_exception()

    user_repo = await UserRepositoryFactory(db).get_repository()
    # Получаем из базы данных пользователя с указанным логином
    user = await user_repo.get_user_by_email_or_login(acesss_token_verefied.login)
    if not user:
        raise get_user_not_found_exception()

    # Получаем refresh токен текущего пользователя
    tokens_repo = await RefreshTokenRepositoryFactory(db).get_repository()
    refresh_token_db = await tokens_repo.get_refresh_token_by_user_id(user.id)
    if refresh_token_db:
        await tokens_repo.revoke_refresh_token(refresh_token_db.id)
    return {"message": "Refresh token revoked"}


async def get_current_session_user(db: AsyncSession, acesss_token: str):
    access_token_strategy = AccessTokenStrategy()
    # Верифицируем access токен текущей сессии
    acesss_token_verefied = await access_token_strategy.verify_token(acesss_token)
    if not acesss_token_verefied:
        raise HTTPException(status_code=401, detail="Invalid access token")

    user_repo = await UserRepositoryFactory(db).get_repository()
    # Получаем из базы данных пользователя с указанным логином
    user = await user_repo.get_user_by_email_or_login(acesss_token_verefied.login)
    if not user:
        raise get_user_not_found_exception()
    return UserGet.from_orm(user)


async def update_user_login_and_password(
    db: AsyncSession, user_update: UserLoginPasswordUpdate, token: str
) -> UserGet:
    acces_token_strategy = AccessTokenStrategy()
    refresh_token_strategy = RefreshTokenStrategy()

    access_token = await acces_token_strategy.verify_token(token)
    if not access_token:
        # TODO не авторизован exception
        raise get_user_not_found_exception()
    
    user_repo = await UserRepositoryFactory(db).get_repository()
    refresh_token_repo = await RefreshTokenRepositoryFactory(db).get_repository()

    # Получаем пользователя по ID которого будем обновлять
    user = await user_repo.get_user_by_email_or_login(access_token.login)
    if not user:
        raise get_user_not_found_exception()
    # проверяем форму с новыми данными
    new_user = await user_repo.get_user_by_email_or_login(user_update.login)
    if new_user:
        raise get_user_already_exists("User with this login already exists")

    encryption_facade = EncryptionFacade()
    generated_keys = await encryption_facade.generate_keys()
    encrypted_password = await encryption_facade.encrypt_data(
        user_update.password, generated_keys["session_key"]
    )

    # критически важная зона!
    # TODO проверить работу db перед обновлением данных
    # Обновляем логин и зашифрованный пароль пользователя
    updated_user = await user_repo.update_user(
        user.id, login=user_update.login, encrypted_password=encrypted_password
    )
    keys_repo = await KeyStorageRepositoryFactory(db).get_repository()
    await keys_repo.delete_keys(user.id)
    # Обновляем ключи шифрования пользователя
    new_keys = await keys_repo.save_keys(
        user_id=user.id,
        private_key=generated_keys["private_key"].export_key(),
        public_key=generated_keys["public_key"].export_key(),
        encrypted_session_key=generated_keys["encrypted_session_key"],
    )
    if not new_keys:
        raise get_database_error_exception()
    # TODO обновить сессионные ключи

    # Возвращаем обновленные данные пользователя
    updated_user = await user_repo.get_user_by_id(user.id)

    login_history_repo = LoginHistoryRepositoryFactory(db).get_repository()
    await login_history_repo.create_login_history(
        user_id=user.id, ip="127.0.0.1", user_agent="test"
    )

    return UserGet.from_orm(updated_user)


async def get_login_history(db: AsyncSession, token: str):
    access_token = await AccessTokenStrategy().verify_token(token)
    if not access_token:
        raise get_user_not_found_exception()
    user_repo = await UserRepositoryFactory(db).get_repository()
    user = await user_repo.get_user_by_email_or_login(access_token.login)
    if not user:
        raise get_user_not_found_exception()

    login_history_repo = LoginHistoryRepositoryFactory(db).get_repository()
    login_history = await login_history_repo.get_login_history_by_user_id(user.id)
    return login_history
