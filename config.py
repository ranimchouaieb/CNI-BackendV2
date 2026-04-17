from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    env: str = "development"
    app_base_url: str = "http://localhost:8000"
    allowed_origins: list[str] = []

    model_config = {"env_file": ".env"}


settings = Settings()
