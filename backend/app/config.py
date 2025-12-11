from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    
    # Encryption
    ENCRYPTION_KEY: str
    
    # Google Drive
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # OAuth Redirect URI (for production, use your domain)
    OAUTH_REDIRECT_URI: str = "http://localhost:80/oauth-callback.html"
    
    # Superadmin
    SUPERADMIN_EMAIL: str
    SUPERADMIN_PASSWORD: str
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
