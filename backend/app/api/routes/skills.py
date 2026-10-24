from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import datetime

from app.core.database import get_db
from app.models.entities import Skill, SkillProgress, SkillRelationship
from app.schemas.schemas import SkillResponse, SkillCreate, SkillProgressUpdate

router = APIRouter(prefix="/skills", tags=["Skills Tracker"])

def seed_default_skills_if_empty(db: Session):
    if db.query(Skill).count() == 0:
        default_skills = [
            ("Linux: Основы терминала", "Навигация, базовые команды pwd, ls, cd", "Linux", []),
            ("Linux: Файловая система и права", "Разбор прав rwx, chmod, chown, структуры каталогов", "Linux", ["Linux: Основы терминала"]),
            ("Linux: Bash и автоматизация", "Написание bash-скриптов, переменных, циклов и пайплайнов", "Linux", ["Linux: Файловая система и права"]),
            ("C++: Базовый синтаксис", "Переменные, типы данных, операторы cin/cout", "C++", []),
            ("C++: Управляющие конструкции", "Ветвления if/else, switch, циклы for/while", "C++", ["C++: Базовый синтаксис"]),
            ("C++: Функции и модульность", "Сигнатуры функций, передача по ссылке и значению", "C++", ["C++: Управляющие конструкции"]),
            ("C++: Указатели и работа с памятью", "Адресация, операторы &, *, динамическая память new/delete", "C++", ["C++: Функции и модульность"]),
            ("C++: ООП и классы", "Инкапсуляция, конструкторы, деструкторы, наследование", "C++", ["C++: Указатели и работа с памятью"]),
            ("Алгоритмы: Сортировки и поиск", "Бинарный поиск, быстрая сортировка, сложность O(n)", "Компьютерные науки", ["C++: Управляющие конструкции"])
        ]
        created_map = {}
        for name, desc, cat, prereqs in default_skills:
            skill = Skill(name=name, description=desc, category=cat, prerequisites_json=json.dumps(prereqs))
            db.add(skill)
            db.flush()
            created_map[name] = skill.id
            
            # Progress record
            prog = SkillProgress(skill_id=skill.id, status="not_started", confidence_level=0.0)
            db.add(prog)

        # Create relationships
        for name, _, _, prereqs in default_skills:
            tgt_id = created_map[name]
            for p in prereqs:
                if p in created_map:
                    rel = SkillRelationship(source_skill_id=created_map[p], target_skill_id=tgt_id, relation_type="depends_on")
                    db.add(rel)

        db.commit()

@router.get("", response_model=List[SkillResponse])
def get_skills(db: Session = Depends(get_db)):
    seed_default_skills_if_empty(db)
    skills = db.query(Skill).all()
    results = []
    for s in skills:
        p = s.progress or SkillProgress(status="not_started", confidence_level=0.0)
        prereqs = json.loads(s.prerequisites_json or "[]")
        results.append(SkillResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            category=s.category,
            status=p.status,
            confidence_level=p.confidence_level,
            last_practiced_at=p.last_practiced_at,
            next_review_at=p.next_review_at,
            prerequisites=prereqs
        ))
    return results

@router.get("/graph")
def get_skill_graph(db: Session = Depends(get_db)):
    seed_default_skills_if_empty(db)
    skills = db.query(Skill).all()
    relationships = db.query(SkillRelationship).all()

    status_colors = {
        "mastered": "#10b981", # Emerald
        "learning": "#3b82f6", # Blue
        "needs_practice": "#f59e0b", # Amber
        "needs_review": "#ec4899", # Pink
        "not_started": "#475569" # Slate
    }

    nodes = []
    # Layout positions simply in columns based on category/index
    cat_counts = {}
    for s in skills:
        cat = s.category
        idx = cat_counts.get(cat, 0)
        cat_counts[cat] = idx + 1
        
        col = 0
        if cat == "Linux":
            col = 0
        elif cat == "C++":
            col = 1
        else:
            col = 2

        x = 50 + col * 320
        y = 50 + idx * 130

        p = s.progress
        status = p.status if p else "not_started"
        conf = p.confidence_level if p else 0.0

        nodes.append({
            "id": str(s.id),
            "data": {
                "label": s.name,
                "category": s.category,
                "status": status,
                "confidence": conf,
                "color": status_colors.get(status, "#475569")
            },
            "position": {"x": x, "y": y},
            "type": "default"
        })

    edges = []
    for r in relationships:
        edges.append({
            "id": f"e{r.source_skill_id}-{r.target_skill_id}",
            "source": str(r.source_skill_id),
            "target": str(r.target_skill_id),
            "animated": True,
            "style": {"stroke": "#6366f1", "strokeWidth": 2}
        })

    return {"nodes": nodes, "edges": edges}

@router.put("/{skill_id}/progress", response_model=SkillResponse)
def update_skill_progress(skill_id: int, payload: SkillProgressUpdate, db: Session = Depends(get_db)):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Навык не найден")

    prog = db.query(SkillProgress).filter(SkillProgress.skill_id == skill_id).first()
    now = datetime.datetime.now(datetime.timezone.utc)
    if not prog:
        prog = SkillProgress(skill_id=skill_id, status=payload.status, confidence_level=payload.confidence_level, last_practiced_at=now)
        db.add(prog)
    else:
        prog.status = payload.status
        prog.confidence_level = payload.confidence_level
        prog.last_practiced_at = now
        prog.updated_at = now

    db.commit()
    db.refresh(skill)

    prereqs = json.loads(skill.prerequisites_json or "[]")
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        category=skill.category,
        status=prog.status,
        confidence_level=prog.confidence_level,
        last_practiced_at=prog.last_practiced_at,
        next_review_at=prog.next_review_at,
        prerequisites=prereqs
    )
