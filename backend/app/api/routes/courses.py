from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.models.entities import Course, Module, Lesson
from app.schemas.schemas import (
    CourseCreate, CourseUpdate, CourseSummaryResponse, CourseDetailResponse,
    ModuleCreate, ModuleResponse, LessonCreate, LessonResponse
)

router = APIRouter(prefix="/courses", tags=["Courses"])

def calculate_course_stats(course: Course) -> dict:
    total_lessons = len(course.lessons)
    completed_lessons = sum(1 for l in course.lessons if l.is_completed)
    progress = (completed_lessons / total_lessons * 100.0) if total_lessons > 0 else 0.0
    return {
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "progress_percentage": round(progress, 1)
    }

@router.get("", response_model=List[CourseSummaryResponse])
def get_courses(
    include_archived: bool = Query(False),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    query = db.query(Course).filter(Course.user_id == user_id)
    if not include_archived:
        query = query.filter(Course.is_archived == False)
    courses = query.order_by(Course.updated_at.desc()).all()
    
    result = []
    for c in courses:
        stats = calculate_course_stats(c)
        c_dict = {
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "target_goal": c.target_goal,
            "user_level": c.user_level,
            "learning_mode": c.learning_mode,
            "is_archived": c.is_archived,
            "estimated_hours": c.estimated_hours,
            "total_lessons": stats["total_lessons"],
            "completed_lessons": stats["completed_lessons"],
            "progress_percentage": stats["progress_percentage"],
            "created_at": c.created_at,
            "updated_at": c.updated_at
        }
        result.append(CourseSummaryResponse(**c_dict))
    return result

@router.post("", response_model=CourseDetailResponse, status_code=201)
def create_course(
    payload: CourseCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    course = Course(
        user_id=user_id,
        title=payload.title,
        description=payload.description,
        target_goal=payload.target_goal,
        user_level=payload.user_level,
        learning_mode=payload.learning_mode,
        estimated_hours=payload.estimated_hours
    )
    db.add(course)
    db.flush()

    for mod_idx, mod_data in enumerate(payload.modules or []):
        module = Module(
            course_id=course.id,
            title=mod_data.title,
            description=mod_data.description,
            order_index=mod_data.order_index or mod_idx
        )
        db.add(module)
        db.flush()

        for les_idx, les_data in enumerate(mod_data.lessons or []):
            lesson = Lesson(
                course_id=course.id,
                module_id=module.id,
                title=les_data.title,
                description=les_data.description,
                content_markdown=les_data.content_markdown or f"# {les_data.title}\n\nСодержание урока готовится...",
                order_index=les_data.order_index or les_idx,
                estimated_minutes=les_data.estimated_minutes or 20
            )
            db.add(lesson)

    db.commit()
    db.refresh(course)
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

@router.get("/{course_id}", response_model=CourseDetailResponse)
def get_course_detail(
    course_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
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

@router.put("/{course_id}", response_model=CourseSummaryResponse)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(course, field, val)
    course.updated_at = datetime.datetime.now(datetime.timezone.utc)
    
    db.commit()
    db.refresh(course)
    stats = calculate_course_stats(course)
    return CourseSummaryResponse(
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
        created_at=course.created_at,
        updated_at=course.updated_at
    )

@router.delete("/{course_id}", status_code=204)
def delete_course(
    course_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    db.delete(course)
    db.commit()
    return None

@router.post("/{course_id}/modules", response_model=ModuleResponse, status_code=201)
def add_module_to_course(course_id: int, payload: ModuleCreate, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    current_count = db.query(Module).filter(Module.course_id == course_id).count()
    module = Module(
        course_id=course_id,
        title=payload.title,
        description=payload.description,
        order_index=payload.order_index if payload.order_index > 0 else current_count
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module
