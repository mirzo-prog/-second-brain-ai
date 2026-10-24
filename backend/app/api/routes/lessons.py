from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import datetime

from app.core.database import get_db
from app.models.entities import Course, Module, Lesson, LearningSession
from app.schemas.schemas import LessonResponse, LessonUpdate, LessonProgressUpdate, LessonCreate

router = APIRouter(prefix="/lessons", tags=["Lessons"])

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

@router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")

    # Update last_accessed_at for both lesson and course
    now = utcnow()
    lesson.last_accessed_at = now
    if not lesson.status or lesson.status == "not_started":
        lesson.status = "in_progress"
    course = db.query(Course).filter(Course.id == lesson.course_id).first()
    if course:
        course.updated_at = now

    # Also log or update session
    db.commit()
    db.refresh(lesson)
    return lesson

@router.put("/{lesson_id}", response_model=LessonResponse)
def update_lesson(lesson_id: int, payload: LessonUpdate, db: Session = Depends(get_db)):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(lesson, field, val)
    lesson.updated_at = utcnow()
    
    db.commit()
    db.refresh(lesson)
    return lesson

@router.put("/{lesson_id}/progress", response_model=LessonResponse)
def update_lesson_progress(lesson_id: int, payload: LessonProgressUpdate, db: Session = Depends(get_db)):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")

    now = utcnow()
    lesson.is_completed = payload.is_completed
    if payload.status:
        lesson.status = payload.status
    elif payload.is_completed:
        lesson.status = "mastered"
    else:
        lesson.status = "in_progress"

    lesson.last_accessed_at = now
    lesson.updated_at = now

    # Update course timestamp
    course = db.query(Course).filter(Course.id == lesson.course_id).first()
    if course:
        course.updated_at = now

    db.commit()
    db.refresh(lesson)
    return lesson

@router.post("", response_model=LessonResponse, status_code=201)
def create_lesson(module_id: int, payload: LessonCreate, db: Session = Depends(get_db)):
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Модуль не найден")

    count = db.query(Lesson).filter(Lesson.module_id == module_id).count()
    lesson = Lesson(
        module_id=module_id,
        course_id=module.course_id,
        title=payload.title,
        description=payload.description,
        content_markdown=payload.content_markdown or f"# {payload.title}\n\nСодержание урока...",
        order_index=payload.order_index if payload.order_index > 0 else count,
        estimated_minutes=payload.estimated_minutes
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson

@router.delete("/{lesson_id}", status_code=204)
def delete_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    db.delete(lesson)
    db.commit()
    return None
