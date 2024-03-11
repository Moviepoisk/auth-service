# Import necessary modules and classes
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.exceptions.exceptions import (
    get_incorrect_credentials_exception,
    get_token_validation_exception,
    get_user_not_found_exception,
    get_user_already_exists,
    get_database_error_exception,
)
from app.schemas.user import UserCreate, UserGet

from app.auth.encryption_strategy import RSAEncryptor, AESEncryptor, EncryptedMessage
from app.auth.user_repository import UserRepositoryFactory
from app.auth.encryption_repository import KeyStorageRepositoryFactory
from app.auth.encryption_strategy import (
    RSAKeyPairGenerator,
    get_session_key_async,
    RSAEncryptor,
    AESEncryptor,
)
from app.auth.token_strategy import AccessTokenStrategy, RefreshTokenStrategy
from app.auth.token_repository import RefreshTokenRepositoryFactory
from Crypto.PublicKey import RSA
from datetime import timedelta, datetime
import json
from app.core.config import settings
from fastapi import HTTPException


async def register_new_user(db: AsyncSession, user_data: UserCreate) -> str:
    user_repo = UserRepositoryFactory(db).get_repository()
    user = await user_repo.get_user_by_email_or_login(user_data.login)
    if user:
        raise get_user_already_exists("User with this login already exists")
    user = await user_repo.get_user_by_email_or_login(user_data.email)
    if user:
        raise get_user_already_exists("User with this email already exists")

    session_key = await get_session_key_async()
    key_generator = RSAKeyPairGenerator()
    session_key_encryptor = RSAEncryptor()
    data_encryptor = AESEncryptor()

    # генерим ключи
    private_key, public_key = await key_generator.generate_key_pair()

    # Шифрование сессионного ключа публичным ключом
    encrypted_session_key = await session_key_encryptor.encrypt_session_key(
        session_key, public_key
    )

    # Шифрование пароля пользователя сессионным ключом
    encrypted_password_message = await data_encryptor.encrypt(
        user_data.password, session_key
    )

    # Сериализация encrypted_password_message в JSON
    encrypted_password = json.dumps(
        {
            "nonce": encrypted_password_message.nonce.hex(),
            "digest": encrypted_password_message.digest.hex(),
            "message": encrypted_password_message.message.hex(),
        }
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

    # исключение в случае неудачи
    if not new_user:
        raise get_database_error_exception()

    keys_repo = KeyStorageRepositoryFactory(db).get_repository()

    # Сохраняем ключи
    new_keys = await keys_repo.save_keys(
        user_id=new_user.id,
        private_key=private_key.export_key(),
        public_key=public_key.export_key(),
        encrypted_session_key=encrypted_session_key,
    )
    if not new_keys:
        raise get_database_error_exception()

    return new_user.id


async def authenticate_user(
    db: AsyncSession, email_or_login: str, password: str
) -> Optional[UserGet]:
    user_repo = UserRepositoryFactory(db).get_repository()
    user = await user_repo.get_user_by_email_or_login(email_or_login)
    if not user:
        raise get_user_not_found_exception()

    # инициализировать encryption_repository
    encryption_repository = KeyStorageRepositoryFactory(db).get_repository()
    # получим ключи
    user_keys = await encryption_repository.get_keys(user.id)
    if not user_keys:
        # to do : только восстановление через смену пароля
        raise get_incorrect_credentials_exception()

    # Import and decode the user's private RSA key
    private_key = RSA.import_key(user_keys.private_key)

    # Initialize RSAEncryptor and AESEncryptor instances
    rsa_encryptor = RSAEncryptor()
    aes_encryptor = AESEncryptor()

    # Decrypt the encrypted session key using the user's private key
    decrypted_session_key = await rsa_encryptor.decrypt_session_key(
        user_keys.encrypted_session_key, private_key
    )

    # Load the encrypted password data and create an EncryptedMessage instance
    encrypted_password_data = json.loads(user.encrypted_password)
    encrypted_message = EncryptedMessage(
        nonce=bytes.fromhex(encrypted_password_data["nonce"]),
        digest=bytes.fromhex(encrypted_password_data["digest"]),
        message=bytes.fromhex(encrypted_password_data["message"]),
    )

    # Decrypt the encrypted password using the decrypted session key
    decrypted_password = await aes_encryptor.decrypt(
        encrypted_message, decrypted_session_key
    )

    # Compare the provided password with the decrypted password
    if decrypted_password != password:
        # Handle authentication failure
        raise get_incorrect_credentials_exception()

    return UserGet.from_orm(user)


async def create_access_and_refresh_tokens(db: AsyncSession, login: str):
    # Assuming you have a method to get the user by login
    user_repo = UserRepositoryFactory(db).get_repository()
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
    tokens_repo = RefreshTokenRepositoryFactory(db).get_repository()
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

    user_repo = UserRepositoryFactory(db).get_repository()
    # Получаем из базы данных пользователя с указанным логином
    user = await user_repo.get_user_by_email_or_login(acesss_token_verefied.login)
    if not user:
        raise get_user_not_found_exception()

    # Получаем refresh токен текущего пользователя
    tokens_repo = RefreshTokenRepositoryFactory(db).get_repository()
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

    user_repo = UserRepositoryFactory(db).get_repository()
    # Получаем из базы данных пользователя с указанным логином
    user = await user_repo.get_user_by_email_or_login(acesss_token_verefied.login)
    if not user:
        raise get_user_not_found_exception()
    return UserGet.from_orm(user)
