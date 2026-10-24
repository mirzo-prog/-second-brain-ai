from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import datetime
from typing import Dict, Any, List

from app.core.database import get_db
from app.models.entities import Course, Lesson, LearningSession, SkillProgress, Submission, ReviewSchedule, Note

router = APIRouter(prefix="/statistics", tags=["Statistics & Analytics"])

@router.get("/summary")
def get_statistics_summary(db: Session = Depends(get_db)):
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # 1. Daily study minutes for the last 14 days
    daily_stats = []
    for i in range(13, -1, -1):
        day = (now - datetime.timedelta(days=i)).date()
        day_start = datetime.datetime.combine(day, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
        day_end = datetime.datetime.combine(day, datetime.time.max).replace(tzinfo=datetime.timezone.utc)
        
        sec = db.query(func.coalesce(func.sum(LearningSession.duration_seconds), 0)).filter(
            LearningSession.started_at >= day_start,
            LearningSession.started_at <= day_end
        ).scalar() or 0
        
        daily_stats.append({
            "date": day.strftime("%d.%m"),
            "minutes": sec // 60
        })

    # 2. Skills breakdown
    status_labels = {
        "mastered": ("Освоено", "#10b981"),
        "learning": ("Изучается", "#3b82f6"),
        "needs_practice": ("Требует практики", "#f59e0b"),
        "needs_review": ("Повторение", "#ec4899"),
        "not_started": ("Не начато", "#64748b")
    }
    skill_counts = (
        db.query(SkillProgress.status, func.count(SkillProgress.id))
        .group_by(SkillProgress.status)
        .all()
    )
    counts_map = {st: cnt for st, cnt in skill_counts}
    
    skills_breakdown = []
    for st, (label, color) in status_labels.items():
        skills_breakdown.append({
            "status": st,
            "name": label,
            "value": counts_map.get(st, 0),
            "color": color
        })

    # 3. Practice & Submissions metrics
    total_submissions = db.query(Submission).count()
    correct_submissions = db.query(Submission).filter(Submission.is_correct == True).count()
    accuracy = (correct_submissions / total_submissions * 100.0) if total_submissions > 0 else 0.0

    # 4. Totals
    total_courses = db.query(Course).count()
    completed_courses = 0
    all_courses = db.query(Course).all()
    for c in all_courses:
        if c.lessons and all(l.is_completed for l in c.lessons):
            completed_courses += 1

    total_lessons = db.query(Lesson).count()
    completed_lessons = db.query(Lesson).filter(Lesson.is_completed == True).count()
    total_study_seconds = db.query(func.coalesce(func.sum(LearningSession.duration_seconds), 0)).scalar() or 0
    total_notes = db.query(Note).count()
    completed_reviews = db.query(ReviewSchedule).filter(ReviewSchedule.is_completed == True).count()

    return {
        "daily_study_time": daily_stats,
        "skills_breakdown": skills_breakdown,
        "accuracy_percentage": round(accuracy, 1),
        "total_submissions": total_submissions,
        "total_courses": total_courses,
        "completed_courses": completed_courses,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "total_study_hours": round(total_study_seconds / 3600.0, 1),
        "total_notes": total_notes,
        "completed_reviews": completed_reviews
    }
