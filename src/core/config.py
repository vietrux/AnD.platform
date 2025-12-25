from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    debug: bool = False
    secret_key: str = "change-this-in-production"
    
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/adg_core"
    
    docker_host: str = "unix:///var/run/docker.sock"
    
    tick_duration_seconds: int = 60
    flag_validity_ticks: int = 5
    flag_secret_key: str = "change-this-hmac-secret-key"
    
    upload_dir: str = "./uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
