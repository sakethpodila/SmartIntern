from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    JSEARCH_API_KEY: str = os.getenv('JSEARCH_API_KEY')
    JSEARCH_BASE_URL: str = os.getenv('JSEARCH_BASE_URL')
    class Config:
        env_file = '.env'
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    # cACHED settings instance
    return Settings()