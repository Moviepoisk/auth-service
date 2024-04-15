# from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # default values for local development
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    # SUPER_ADMIN_LOGIN: str
    # SUPER_ADMIN_PASSWORD: str
    # SUPER_ADMIN_EMAIL: str
    # SUPER_ADMIN_FIRST_NAME: str
    # SUPER_ADMIN_LAST_NAME: str

    # # Определение имен и описаний ролей
    # SUPER_ADMIN_ROLE_NAME: str
    # SUPER_ADMIN_ROLE_DESCRIPTION: str

    # ADMIN_ROLE_NAME: str
    # ADMIN_ROLE_DESCRIPTION: str

    # USER_ROLE_NAME: str
    # USER_ROLE_DESCRIPTION: str

    # SUBSCRIBER_ROLE_NAME: str
    # SUBSCRIBER_ROLE_DESCRIPTION: str

    # GUEST_ROLE_NAME: str
    # GUEST_ROLE_DESCRIPTION: str

    # # sequrity settings jwt
    JWT_SECRET_KEY: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:"
            f"{self.DB_PASSWORD}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def database_url_async(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:"
            f"{self.DB_PASSWORD}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
