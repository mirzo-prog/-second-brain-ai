from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid
from typing import List, Optional

from app.core.database import get_db
from app.core.config import settings
from app.core.auth import get_current_user_id
from app.models.entities import Document, CourseDocument, Course
from app.schemas.schemas import DocumentResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/documents", tags=["Library & Documents"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md", "markdown", "cpp", "py", "sh", "bash", "png", "jpg", "jpeg"}
MAX_FILE_SIZE = 50 * 1024 * 1024 # 50 MB safety limit

@router.get("", response_model=List[DocumentResponse])
def list_documents(
    course_id: Optional[int] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    query = db.query(Document).filter(Document.user_id == user_id)
    if course_id:
        query = query.join(CourseDocument, CourseDocument.document_id == Document.id).filter(CourseDocument.course_id == course_id)
    
    docs = query.order_by(Document.created_at.desc()).all()
    results = []
    for d in docs:
        results.append(DocumentResponse(
            id=d.id,
            title=d.title,
            filename=d.filename,
            file_type=d.file_type,
            file_size=d.file_size,
            is_indexed=d.is_indexed,
            chunks_count=len(d.chunks),
            attached_courses_count=len(d.course_documents),
            created_at=d.created_at
        ))
    return results

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    course_id: Optional[int] = Form(None),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    # Safety: sanitize and inspect filename
    filename = Path(file.filename).name
    ext = filename.split(".")[-1].lower() if "." in filename else "txt"
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат файла: .{ext}. Допустимы: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Save to disk with unique prefix to avoid collisions
    doc_uuid = uuid.uuid4().hex[:10]
    safe_disk_filename = f"{doc_uuid}_{filename}"
    upload_path = settings.UPLOADS_PATH / safe_disk_filename

    try:
        size = 0
        with open(upload_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=400, detail="Файл превышает лимит размера 50 МБ")
                buffer.write(chunk)
    except Exception as e:
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла: {str(e)}")

    doc_title = title.strip() if title and title.strip() else filename

    doc = Document(
        user_id=user_id,
        title=doc_title,
        filename=filename,
        file_path=str(upload_path.resolve()),
        file_type=ext,
        file_size=size,
        is_indexed=False
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Attach to course if specified
    if course_id:
        course = db.query(Course).filter(Course.id == course_id, Course.user_id == user_id).first()
        if course:
            course_doc = CourseDocument(course_id=course.id, document_id=doc.id)
            db.add(course_doc)
            db.commit()

    # Automatically index document for RAG
    rag_svc = RAGService(db)
    try:
        rag_svc.index_document(doc.id)
    except Exception as e:
        # Non-fatal error during index: file is saved, index can be retried
        pass

    db.refresh(doc)
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        is_indexed=doc.is_indexed,
        chunks_count=len(doc.chunks),
        attached_courses_count=len(doc.course_documents),
        created_at=doc.created_at
    )

@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    rag_svc = RAGService(db)
    rag_svc.delete_document(document_id)
    return None

@router.post("/{document_id}/attach/{course_id}")
def attach_to_course(
    document_id: int,
    course_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user_id).first()
    if not doc or not course:
        raise HTTPException(status_code=404, detail="Документ или курс не найден")

    existing = db.query(CourseDocument).filter(
        CourseDocument.document_id == document_id,
        CourseDocument.course_id == course_id
    ).first()
    if not existing:
        db.add(CourseDocument(document_id=document_id, course_id=course_id))
        db.commit()
    return {"status": "ok", "message": "Документ привязан к курсу"}

@router.delete("/{document_id}/attach/{course_id}")
def detach_from_course(
    document_id: int,
    course_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")
    cd = db.query(CourseDocument).filter(
        CourseDocument.document_id == document_id,
        CourseDocument.course_id == course_id
    ).first()
    if cd:
        db.delete(cd)
        db.commit()
    return {"status": "ok", "message": "Документ отвязан от курса"}

@router.get("/search")
def test_search(
    query: str,
    course_id: Optional[int] = Query(None),
    limit: int = Query(5),
    db: Session = Depends(get_db)
):
    rag_svc = RAGService(db)
    results = rag_svc.search(query=query, course_id=course_id, limit=limit)
    return {"query": query, "count": len(results), "results": results}
