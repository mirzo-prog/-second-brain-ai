from fastapi import APIRouter, HTTPException, BackgroundTasks
import sqlite3
import datetime
from pathlib import Path
from pydantic import BaseModel
from typing import List

from app.core.config import settings

router = APIRouter(prefix="/backup", tags=["Backup"])

class BackupInfo(BaseModel):
    filename: str
    size_bytes: int
    created_at: datetime.datetime

class RestoreRequest(BaseModel):
    filename: str

@router.get("", response_model=List[BackupInfo])
def list_backups():
    backup_dir = Path(settings.BACKUPS_PATH)
    if not backup_dir.exists():
        return []
    
    backups = []
    for f in sorted(backup_dir.glob("backup_*.db"), reverse=True):
        stat = f.stat()
        backups.append(BackupInfo(
            filename=f.name,
            size_bytes=stat.st_size,
            created_at=datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc)
        ))
    return backups

@router.post("/create", response_model=BackupInfo)
def create_backup():
    db_path = Path(settings.DB_PATH)
    if not db_path.exists():
        raise HTTPException(status_code=400, detail="Основная база данных ещё не создана")

    backup_dir = Path(settings.BACKUPS_PATH)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_filepath = backup_dir / backup_filename

    try:
        # Atomic SQLite online backup API
        src_conn = sqlite3.connect(str(db_path.resolve()))
        dst_conn = sqlite3.connect(str(backup_filepath.resolve()))
        src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()

        stat = backup_filepath.stat()
        return BackupInfo(
            filename=backup_filename,
            size_bytes=stat.st_size,
            created_at=datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания резервной копии: {str(e)}")

@router.post("/restore")
def restore_backup(payload: RestoreRequest):
    backup_dir = Path(settings.BACKUPS_PATH)
    backup_filepath = (backup_dir / payload.filename).resolve()

    # Safety check: prevent path traversal
    if not backup_filepath.is_relative_to(backup_dir.resolve()):
        raise HTTPException(status_code=400, detail="Недопустимый путь к файлу")

    if not backup_filepath.exists():
        raise HTTPException(status_code=404, detail="Файл резервной копии не найден")

    # Verify SQLite header
    with open(backup_filepath, "rb") as f:
        header = f.read(16)
        if header != b"SQLite format 3\x00":
            raise HTTPException(status_code=400, detail="Файл не является корректной базой данных SQLite")

    db_path = Path(settings.DB_PATH)
    try:
        # Restore atomically via SQLite backup
        src_conn = sqlite3.connect(str(backup_filepath))
        dst_conn = sqlite3.connect(str(db_path.resolve()))
        src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()
        return {"status": "ok", "message": f"База данных успешно восстановлена из {payload.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка восстановления: {str(e)}")
