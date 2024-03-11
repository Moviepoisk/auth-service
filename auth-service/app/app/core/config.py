from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # default values for local development
    db_host: str = Field('0.0.0.0', env="AUTH_DB_HOST")
    db_port: int = Field(5434, env="AUTH_DB_PORT")
    db_user: str = Field('devuser', env="AUTH_DB_USER")
    db_password: str = Field('changeme', env="AUTH_DB_PASSWORD")
    db_name: str = Field('devdb', env="A_NAME")
    redis_host: str = Field('0.0.0.0', env="AUTH_REDIS_HOST")
    redis_port: int = Field(6379, env="AUTH_REDIS_PORT")
    super_admin_login: str = Field('super_admin', env="AUTH_SUPER_USER_LOGIN")
    super_admin_password: str = Field('changeme', env="AUTH_SUPER_USER_PASSWORD")
    super_admin_email: str = Field('super_admin@localhost', env="AUTH_SUPER_USER_EMAIL")
    super_admin_first_name: str = Field('Super', env="AUTH_SUPER_USER_FIRST_NAME")
    super_admin_last_name: str = Field('Admin', env="AUTH_SUPER_USER_LAST_NAME")

    #Определение имен и описаний ролей
    super_admin_role_name: str = Field("super_admin", env="SUPER_ADMIN_ROLE_NAME")
    super_admin_role_description: str = Field("Role with all permissions.", env="SUPER_ADMIN_ROLE_DESCRIPTION")

    admin_role_name: str = Field("admin", env="ADMIN_ROLE_NAME")
    admin_role_description: str = Field("Role with access to admin level functionalities.", env="ADMIN_ROLE_DESCRIPTION")

    user_role_name: str = Field("user", env="USER_ROLE_NAME")
    user_role_description: str = Field("Standard user role with basic access rights.", env="USER_ROLE_DESCRIPTION")

    subscriber_role_name: str = Field("subscriber", env="SUBSCRIBER_ROLE_NAME")
    subscriber_role_description: str = Field("Role for users with subscription.", env="SUBSCRIBER_ROLE_DESCRIPTION")

    guest_role_name: str = Field("guest", env="GUEST_ROLE_NAME")
    guest_role_description: str = Field("Role for unregistered users with minimal access.", env="GUEST_ROLE_DESCRIPTION")

    # sequrity settings jwt
    jwt_access_token_expire_minutes: int = Field(60, env="AUTH_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(7, env="AUTH_REFRESH_TOKEN_EXPIRE_DAYS")
    jwt_secret_key: str = Field('your_secret_key', env="AUTH_JWT_SECRET_KEY")
    jwt_algorithm: str = Field('HS256', env="AUTH_JWT_ALGORITHM")



    @property
    def database_url(self) -> str:
        return (f"postgresql://{self.db_user}:"
                f"{self.db_password}@{self.db_host}:"
                f"{self.db_port}/{self.db_name}")

    @property
    def database_url_async(self) -> str:
        return (f"postgresql+asyncpg://{self.db_user}:"
                f"{self.db_password}@{self.db_host}:"
                f"{self.db_port}/{self.db_name}")

    class Config:
        env_file = "../../.env"


settings = Settings()

