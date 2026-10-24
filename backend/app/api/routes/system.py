from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import datetime

from app.core.database import get_db
from app.models.entities import Setting, Profile
from app.schemas.schemas import SettingsResponse, SettingsUpdateRequest, ProfileResponse
from app.core.config import settings as app_settings

router = APIRouter(prefix="/system", tags=["System & Settings"])

@router.get("/profile", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    profile = db.query(Profile).first()
    if not profile:
        profile = Profile(name="Пользователь")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.get("/settings", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    settings_records = db.query(Setting).all()
    data = {s.key: s.value for s in settings_records}

    gemini_key = data.get("gemini_api_key", "")
    db_file = Path(app_settings.DB_PATH)
    db_size = db_file.stat().st_size if db_file.exists() else 0

    backup_dir = Path(app_settings.BACKUPS_PATH)
    backup_count = len(list(backup_dir.glob("*.db"))) if backup_dir.exists() else 0

    return SettingsResponse(
        gemini_api_key_configured=bool(gemini_key and len(gemini_key) > 5),
        gemini_model=data.get("gemini_model", "gemini-2.5-flash"),
        ollama_base_url=data.get("ollama_base_url", "http://127.0.0.1:11434"),
        ollama_model=data.get("ollama_model", "llama3:latest"),
        active_provider=data.get("active_provider", "gemini"),
        default_learning_mode=data.get("default_learning_mode", "free"),
        database_size_bytes=db_size,
        backup_count=backup_count
    )

@router.put("/settings", response_model=SettingsResponse)
def update_settings(payload: SettingsUpdateRequest, db: Session = Depends(get_db)):
    updates = payload.model_dump(exclude_unset=True)
    now = datetime.datetime.now(datetime.timezone.utc)

    for key, val in updates.items():
        if val is not None:
            setting_obj = db.query(Setting).filter(Setting.key == key).first()
            if setting_obj:
                setting_obj.value = str(val)
                setting_obj.updated_at = now
            else:
                db.add(Setting(key=key, value=str(val), updated_at=now))
    
    db.commit()
    return get_settings(db)
