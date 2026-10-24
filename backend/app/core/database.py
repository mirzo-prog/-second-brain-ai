from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger("second_brain.database")

DATABASE_URL = f"sqlite:///{settings.DB_PATH.resolve()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.SQL_DEBUG
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.models.entities import Base, Profile, Setting
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize SQLite FTS5 table for RAG full-text keyword search
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts USING fts5(
                chunk_id UNINDEXED,
                document_id UNINDEXED,
                content,
                title,
                section_name,
                tokenize='unicode61'
            );
        """))
        conn.commit()

    # Seed default profile and system settings if not present
    db = SessionLocal()
    try:
        if not db.query(Profile).first():
            profile = Profile(name="Пользователь")
            db.add(profile)
        
        default_settings = [
            ("gemini_api_key", "", "API ключ Google Gemini"),
            ("gemini_model", "gemini-2.5-flash", "Используемая модель Gemini"),
            ("ollama_base_url", "http://127.0.0.1:11434", "URL локального Ollama сервера"),
            ("ollama_model", "llama3:latest", "Модель Ollama"),
            ("active_provider", "gemini", "Активный ИИ-провайдер: gemini или ollama"),
            ("default_learning_mode", "free", "Режим по умолчанию: free, my_materials_plus_ai, only_my_materials"),
            ("theme", "dark", "Тема оформления"),
        ]
        for key, val, desc in default_settings:
            existing = db.query(Setting).filter(Setting.key == key).first()
            if not existing:
                db.add(Setting(key=key, value=val, description=desc))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error during init_db: {e}")
    finally:
        db.close()
