import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.models.entities import Document, DocumentChunk, CourseDocument
from app.services.document_parser import DocumentParser

logger = logging.getLogger("second_brain.rag")

class RAGService:
    def __init__(self, db: Session):
        self.db = db

    def index_document(self, document_id: int) -> int:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Документ не найден")

        file_path = Path(document.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Файл {document.filename} не найден на диске")

        # Parse chunks
        parsed_chunks = DocumentParser.parse_file(file_path, document.file_type)

        # Clear existing chunks for this document
        self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        self.db.execute(text("DELETE FROM document_chunks_fts WHERE document_id = :doc_id"), {"doc_id": document_id})
        self.db.commit()

        # Insert new chunks into SQLite table and FTS5 index
        for idx, pc in enumerate(parsed_chunks):
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=idx,
                content=pc.content,
                page_number=pc.page_number,
                section_name=pc.section_name or "Раздел",
                char_start=pc.char_start,
                char_end=pc.char_end
            )
            self.db.add(chunk)
            self.db.flush()

            self.db.execute(text("""
                INSERT INTO document_chunks_fts (chunk_id, document_id, content, title, section_name)
                VALUES (:chunk_id, :doc_id, :content, :title, :section)
            """), {
                "chunk_id": chunk.id,
                "doc_id": document_id,
                "content": pc.content,
                "title": document.title,
                "section": pc.section_name or ""
            })

        document.is_indexed = True
        self.db.commit()
        return len(parsed_chunks)

    def search(
        self,
        query: str,
        course_id: Optional[int] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        clean_q = re.sub(r'[^\w\sа-яА-ЯёЁ]', ' ', query).strip()
        words = [w for w in clean_q.split() if len(w) > 1]
        if not words:
            return []

        # Prepare FTS5 prefix match: "word1* OR word2*"
        fts_query = " OR ".join(f'"{w}"*' for w in words[:6])

        # If course_id is provided, limit search to documents attached to this course
        filter_sql = ""
        params: Dict[str, Any] = {"query": fts_query, "limit": limit}

        if course_id:
            filter_sql = """
                AND fts.document_id IN (
                    SELECT document_id FROM course_documents WHERE course_id = :course_id
                )
            """
            params["course_id"] = course_id

        sql = f"""
            SELECT 
                fts.chunk_id,
                fts.document_id,
                fts.content,
                fts.title,
                fts.section_name,
                dc.page_number,
                bm25(document_chunks_fts) as rank
            FROM document_chunks_fts fts
            LEFT JOIN document_chunks dc ON dc.id = fts.chunk_id
            WHERE document_chunks_fts MATCH :query
            {filter_sql}
            ORDER BY rank
            LIMIT :limit
        """

        try:
            results = self.db.execute(text(sql), params).fetchall()
        except Exception as e:
            logger.warning(f"FTS5 query failed: {e}")
            return []

        snippets = []
        for row in results:
            snippets.append({
                "chunk_id": row[0],
                "document_id": row[1],
                "content": row[2],
                "doc_title": row[3],
                "section": row[4],
                "page": row[5],
                "score": float(row[6]) if row[6] is not None else 0.0
            })
        return snippets

    def delete_document(self, document_id: int):
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        # Delete FTS index entries
        self.db.execute(text("DELETE FROM document_chunks_fts WHERE document_id = :doc_id"), {"doc_id": document_id})
        
        # Delete file on disk
        try:
            file_path = Path(doc.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete document file {doc.file_path}: {e}")

        self.db.delete(doc)
        self.db.commit()
