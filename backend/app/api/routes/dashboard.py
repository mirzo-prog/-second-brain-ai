from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import datetime

from app.core.database import get_db
from app.models.entities import Course, Lesson, LearningSession, SkillProgress, ReviewSchedule, Note
from app.schemas.schemas import (
    DashboardStatsResponse, CourseSummaryResponse, NoteResponse, LastActiveSessionResponse
)
from app.api.routes.courses import calculate_course_stats
from app.api.routes.sessions import get_last_active_session

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("", response_model=DashboardStatsResponse)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    active_courses = (
        db.query(Course)
        .filter(Course.is_archived == False)
        .order_by(Course.updated_at.desc())
        .all()
    )
    
    courses_summary = []
    total_lessons = 0
    completed_lessons = 0
    total_progress_sum = 0.0

    for c in active_courses:
        stats = calculate_course_stats(c)
        total_lessons += stats["total_lessons"]
        completed_lessons += stats["completed_lessons"]
        total_progress_sum += stats["progress_percentage"]
        courses_summary.append(CourseSummaryResponse(
            id=c.id,
            title=c.title,
            description=c.description,
            target_goal=c.target_goal,
            user_level=c.user_level,
            learning_mode=c.learning_mode,
            is_archived=c.is_archived,
            estimated_hours=c.estimated_hours,
            total_lessons=stats["total_lessons"],
            completed_lessons=stats["completed_lessons"],
            progress_percentage=stats["progress_percentage"],
            created_at=c.created_at,
            updated_at=c.updated_at
        ))

    avg_progress = (total_progress_sum / len(active_courses)) if active_courses else 0.0

    # Total study time from sessions
    total_seconds = db.query(func.coalesce(func.sum(LearningSession.duration_seconds), 0)).scalar() or 0
    total_minutes = total_seconds // 60

    # Weak skills (status == 'needs_practice' or confidence_level < 50.0)
    weak_skills_count = (
        db.query(SkillProgress)
        .filter((SkillProgress.status == "needs_practice") | (SkillProgress.confidence_level < 50.0))
        .count()
    )

    # Reviews due today
    now = datetime.datetime.now(datetime.timezone.utc)
    due_reviews_count = (
        db.query(ReviewSchedule)
        .filter(ReviewSchedule.is_completed == False)
        .filter(ReviewSchedule.scheduled_date <= now)
        .count()
    )

    # Last active session
    last_active = get_last_active_session(db)

    # Dynamic AI recommendations based on real progress
    recommendations = []
    if not active_courses:
        recommendations.append("Создайте свой первый курс, чтобы начать путь в Second Brain AI.")
    else:
        if due_reviews_count > 0:
            recommendations.append(f"У вас запланировано {due_reviews_count} повторений для закрепления памяти.")
        if weak_skills_count > 0:
            recommendations.append(f"Обратите внимание на {weak_skills_count} навыков, требующих дополнительной практики.")
        if completed_lessons == 0:
            recommendations.append("Начните с первого вводного урока, чтобы запустить серию обучения.")
        else:
            recommendations.append("Отличный темп! Закрепите пройденный материал практическим заданием.")

    # Recent notes
    recent_notes_db = (
        db.query(Note)
        .order_by(desc(Note.updated_at))
        .limit(5)
        .all()
    )
    recent_notes = [NoteResponse.model_validate(n) for n in recent_notes_db]

    return DashboardStatsResponse(
        active_courses_count=len(active_courses),
        total_lessons_count=total_lessons,
        completed_lessons_count=completed_lessons,
        average_progress=round(avg_progress, 1),
        total_study_minutes=total_minutes,
        weak_skills_count=weak_skills_count,
        due_reviews_count=due_reviews_count,
        last_active=last_active,
        active_courses=courses_summary,
        ai_recommendations=recommendations,
        recent_notes=recent_notes
    )
