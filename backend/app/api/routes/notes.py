from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.models.entities import Note, Course, Lesson
from app.schemas.schemas import NoteCreate, NoteUpdate, NoteResponse

router = APIRouter(prefix="/notes", tags=["Notes"])

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

@router.get("", response_model=List[NoteResponse])
def get_notes(
    course_id: Optional[int] = Query(None),
    lesson_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    query = db.query(Note).filter(Note.user_id == user_id)
    if course_id:
        query = query.filter(Note.course_id == course_id)
    if lesson_id:
        query = query.filter(Note.lesson_id == lesson_id)
    if search:
        s = f"%{search}%"
        query = query.filter((Note.title.ilike(s)) | (Note.content.ilike(s)) | (Note.tags.ilike(s)))
    
    notes = query.order_by(Note.updated_at.desc()).all()
    return [NoteResponse.model_validate(n) for n in notes]

@router.post("", response_model=NoteResponse, status_code=201)
def create_note(
    payload: NoteCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    note = Note(
        user_id=user_id,
        course_id=payload.course_id,
        lesson_id=payload.lesson_id,
        title=payload.title,
        content=payload.content,
        tags=payload.tags or ""
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteResponse.model_validate(note)

@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Заметка не найдена")
    return NoteResponse.model_validate(note)

@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    payload: NoteUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Заметка не найдена")

    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(note, k, v)
    note.updated_at = utcnow()
    db.commit()
    db.refresh(note)
    return NoteResponse.model_validate(note)

@router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Заметка не найдена")
    db.delete(note)
    db.commit()
    return None
