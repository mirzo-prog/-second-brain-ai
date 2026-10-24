from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
import datetime

from app.core.database import get_db
from app.models.entities import Course, Module, Lesson, LearningSession
from app.schemas.schemas import LastActiveSessionResponse, SessionPingRequest

router = APIRouter(prefix="/sessions", tags=["Sessions"])

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

@router.get("/last-active", response_model=LastActiveSessionResponse)
def get_last_active_session(db: Session = Depends(get_db)):
    # 1. Look for the most recently accessed lesson in an active course
    recent_lesson = (
        db.query(Lesson)
        .join(Course, Course.id == Lesson.course_id)
        .filter(Course.is_archived == False)
        .filter(Lesson.last_accessed_at.isnot(None))
        .order_by(desc(Lesson.last_accessed_at))
        .first()
    )

    if recent_lesson:
        course = db.query(Course).filter(Course.id == recent_lesson.course_id).first()
        
        # If the recent lesson is completed, check if there's a next incomplete lesson
        if recent_lesson.is_completed:
            # Check next lesson in same module or course
            next_lesson = (
                db.query(Lesson)
                .filter(Lesson.course_id == course.id)
                .filter(Lesson.is_completed == False)
                .order_by(Lesson.module_id, Lesson.order_index)
                .first()
            )
            if next_lesson:
                return LastActiveSessionResponse(
                    has_active_session=True,
                    course_id=course.id,
                    course_title=course.title,
                    lesson_id=next_lesson.id,
                    lesson_title=next_lesson.title,
                    last_accessed_at=recent_lesson.last_accessed_at,
                    welcome_message=f"С возвращением! Последний раз вы завершили «{recent_lesson.title}» в курсе «{course.title}». Продолжим с урока «{next_lesson.title}»?"
                )
            else:
                # All lessons in this course completed!
                return LastActiveSessionResponse(
                    has_active_session=True,
                    course_id=course.id,
                    course_title=course.title,
                    lesson_id=recent_lesson.id,
                    lesson_title=recent_lesson.title,
                    last_accessed_at=recent_lesson.last_accessed_at,
                    welcome_message=f"Поздравляем! Вы завершили все уроки курса «{course.title}». Хотите повторить материал или пройти тест?"
                )

        return LastActiveSessionResponse(
            has_active_session=True,
            course_id=course.id,
            course_title=course.title,
            lesson_id=recent_lesson.id,
            lesson_title=recent_lesson.title,
            last_accessed_at=recent_lesson.last_accessed_at,
            welcome_message=f"С возвращением! Вы остановились на уроке «{recent_lesson.title}» в курсе «{course.title}». Продолжим обучение?"
        )

    # 2. Fallback: if no lesson was accessed yet, pick the first lesson of the latest active course
    latest_course = (
        db.query(Course)
        .filter(Course.is_archived == False)
        .order_by(desc(Course.updated_at))
        .first()
    )

    if latest_course and latest_course.lessons:
        first_lesson = (
            db.query(Lesson)
            .filter(Lesson.course_id == latest_course.id)
            .order_by(Lesson.module_id, Lesson.order_index)
            .first()
        )
        if first_lesson:
            return LastActiveSessionResponse(
                has_active_session=True,
                course_id=latest_course.id,
                course_title=latest_course.title,
                lesson_id=first_lesson.id,
                lesson_title=first_lesson.title,
                last_accessed_at=None,
                welcome_message=f"С возвращением! Готовы начать первый урок «{first_lesson.title}» в курсе «{latest_course.title}»?"
            )

    return LastActiveSessionResponse(
        has_active_session=False,
        course_id=None,
        course_title=None,
        lesson_id=None,
        lesson_title=None,
        last_accessed_at=None,
        welcome_message="Добро пожаловать в Second Brain AI! Создайте новый курс или выберите цель обучения."
    )

@router.post("/ping")
def ping_session(payload: SessionPingRequest, db: Session = Depends(get_db)):
    """Records real study time in seconds."""
    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Find existing session for today or create a new one
    session = (
        db.query(LearningSession)
        .filter(
            LearningSession.course_id == payload.course_id,
            LearningSession.started_at >= today_start
        )
        .order_by(desc(LearningSession.started_at))
        .first()
    )

    if not session:
        session = LearningSession(
            course_id=payload.course_id,
            lesson_id=payload.lesson_id,
            started_at=now,
            duration_seconds=payload.seconds
        )
        db.add(session)
    else:
        session.duration_seconds = (session.duration_seconds or 0) + payload.seconds
        session.ended_at = now
        if payload.lesson_id:
            session.lesson_id = payload.lesson_id

    # If lesson_id provided, also update lesson's last_accessed_at
    if payload.lesson_id:
        lesson = db.query(Lesson).filter(Lesson.id == payload.lesson_id).first()
        if lesson:
            lesson.last_accessed_at = now

    db.commit()
    return {"status": "ok", "total_today_seconds": session.duration_seconds}
