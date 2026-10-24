from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "second_brain.db"
DEFAULT_UPLOADS_DIR = DATA_DIR / "uploads"
DEFAULT_BACKUPS_DIR = DATA_DIR / "backups"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Second Brain AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Storage paths
    DATA_PATH: Path = DATA_DIR
    DB_PATH: Path = DEFAULT_DB_PATH
    UPLOADS_PATH: Path = DEFAULT_UPLOADS_DIR
    BACKUPS_PATH: Path = DEFAULT_BACKUPS_DIR
    
    # Database
    SQL_DEBUG: bool = False
    
    # CORS (restricted to localhost)
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # AI Providers
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama3:latest"
    ACTIVE_PROVIDER: str = "gemini" # gemini or ollama
    
    # Default learning mode: "free", "my_materials_plus_ai", "only_my_materials"
    DEFAULT_LEARNING_MODE: str = "free"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure directories exist
settings.DATA_PATH.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_PATH.mkdir(parents=True, exist_ok=True)
settings.BACKUPS_PATH.mkdir(parents=True, exist_ok=True)
