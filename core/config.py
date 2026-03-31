# core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WEATHER_API_KEY: str = Field(default="your_api_key_here", env="WEATHER_API_KEY")
    GOOGLE_CLIENT_ID: str = Field(default="", env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="", env="GOOGLE_CLIENT_SECRET")
    GOOGLE_TOKEN_PATH: str = Field(default="credentials/token.json", env="GOOGLE_TOKEN_PATH")
    
    class Config:
        env_file = ".env"

settings = Settings()
