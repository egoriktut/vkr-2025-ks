from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLAMA_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
