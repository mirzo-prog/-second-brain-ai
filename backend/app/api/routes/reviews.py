from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import datetime
from typing import List

from app.core.database import get_db
from app.models.entities import ReviewSchedule, Exercise, Skill, Lesson
from app.services.spaced_repetition import calculate_sm2

router = APIRouter(prefix="/reviews", tags=["Spaced Repetition Reviews"])

class GradeReviewRequest(BaseModel):
    grade: int # 0 to 5

@router.get("/due")
def get_due_reviews(db: Session = Depends(get_db)):
    now = datetime.datetime.now(datetime.timezone.utc)
    items = (
        db.query(ReviewSchedule)
        .filter(ReviewSchedule.is_completed == False)
        .filter(ReviewSchedule.scheduled_date <= now)
        .all()
    )

    results = []
    for it in items:
        title = f"Повторение: {it.item_type} #{it.item_id}"
        if it.item_type == "exercise":
            ex = db.query(Exercise).filter(Exercise.id == it.item_id).first()
            if ex:
                title = f"Задание: {ex.title}"
        elif it.item_type == "skill":
            sk = db.query(Skill).filter(Skill.id == it.item_id).first()
            if sk:
                title = f"Навык: {sk.name}"
        elif it.item_type == "lesson":
            ls = db.query(Lesson).filter(Lesson.id == it.item_id).first()
            if ls:
                title = f"Урок: {ls.title}"

        results.append({
            "id": it.id,
            "item_type": it.item_type,
            "item_id": it.item_id,
            "title": title,
            "scheduled_date": it.scheduled_date,
            "repetitions": it.repetitions,
            "interval_days": it.interval_days,
            "ease_factor": it.ease_factor
        })
    return results

@router.post("/{review_id}/grade")
def grade_review(review_id: int, payload: GradeReviewRequest, db: Session = Depends(get_db)):
    item = db.query(ReviewSchedule).filter(ReviewSchedule.id == review_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Запись повторения не найдена")

    grade = max(0, min(5, payload.grade))
    new_interval, new_reps, new_ef, next_date = calculate_sm2(
        grade=grade,
        repetitions=item.repetitions,
        ease_factor=item.ease_factor,
        current_interval=item.interval_days
    )

    item.repetitions = new_reps
    item.ease_factor = new_ef
    item.interval_days = new_interval
    item.scheduled_date = next_date
    item.is_completed = (grade >= 3)
    item.updated_at = datetime.datetime.now(datetime.timezone.utc)

    db.commit()
    return {
        "status": "ok",
        "next_review_date": next_date,
        "interval_days": new_interval,
        "repetitions": new_reps
    }
