from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.services.course_generator import CourseGeneratorService
from app.services.lesson_generator import LessonGeneratorService
from app.services.ai_provider import AIProvider
from app.schemas.schemas import CourseDetailResponse, LessonResponse
from app.api.routes.courses import calculate_course_stats

router = APIRouter(prefix="/ai", tags=["AI Generation"])

class GenerateCourseRequest(BaseModel):
    goal: str
    user_level: str = "beginner"
    learning_mode: str = "free"
    target_timeframe: str = "в комфортном темпе"

class GenerateLessonRequest(BaseModel):
    lesson_id: int

@router.post("/generate-course", response_model=CourseDetailResponse)
async def generate_course(
    payload: GenerateCourseRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    if not payload.goal.strip():
        raise HTTPException(status_code=400, detail="Укажите учебную цель")

    service = CourseGeneratorService(db)
    course = await service.generate_course(
        goal=payload.goal,
        user_level=payload.user_level,
        learning_mode=payload.learning_mode,
        target_timeframe=payload.target_timeframe,
        user_id=user_id
    )
    
    stats = calculate_course_stats(course)
    return CourseDetailResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        target_goal=course.target_goal,
        user_level=course.user_level,
        learning_mode=course.learning_mode,
        is_archived=course.is_archived,
        estimated_hours=course.estimated_hours,
        total_lessons=stats["total_lessons"],
        completed_lessons=stats["completed_lessons"],
        progress_percentage=stats["progress_percentage"],
        modules=course.modules,
        created_at=course.created_at,
        updated_at=course.updated_at
    )

@router.post("/generate-lesson", response_model=LessonResponse)
async def generate_lesson(payload: GenerateLessonRequest, db: Session = Depends(get_db)):
    service = LessonGeneratorService(db)
    try:
        await service.generate_lesson_content(lesson_id=payload.lesson_id)
        from app.models.entities import Lesson
        lesson = db.query(Lesson).filter(Lesson.id == payload.lesson_id).first()
        return lesson
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации урока: {str(e)}")

@router.post("/test-connection")
async def test_ai_connection(db: Session = Depends(get_db)):
    provider = AIProvider(db)
    return await provider.test_connection()
