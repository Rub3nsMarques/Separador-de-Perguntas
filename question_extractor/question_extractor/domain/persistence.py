import logging
import json
from typing import Dict, Any
from question_extractor.infra.db import db

logger = logging.getLogger(__name__)

class ExtractionRepository:
    def create_job(self, doc_source_id: str, status: str = "processing") -> int:
        query = """
            INSERT INTO extraction_jobs (doc_source_id, status)
            VALUES (%s, %s)
            RETURNING job_id;
        """
        rows = db.fetch_all(query, (doc_source_id, status))
        if rows:
            return rows[0]['job_id']
        raise RuntimeError("Failed to create job")

    def update_job_status(self, job_id: int, status: str, error_message: str = None) -> None:
        query = """
            UPDATE extraction_jobs
            SET status = %s, error_message = %s, updated_at = NOW()
            WHERE job_id = %s;
        """
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (status, error_message, job_id))
                conn.commit()

    def save_questions(self, job_id: int, questions: list[Dict[str, Any]]) -> None:
        query = """
            INSERT INTO extracted_questions 
            (job_id, question_identifier, status, confidence_score, question_path, alternatives_json, error_note)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                for q in questions:
                    # Construct JSON for alternatives
                    # q['files'] contains "question": path, "A": path, etc.
                    files = q.get('files', {})
                    question_path = files.get('question', '')
                    alternatives = {k: v for k, v in files.items() if k != 'question'}
                    
                    cur.execute(query, (
                        job_id,
                        q.get('question_id'),
                        q.get('status'),
                        q.get('confidence', 100), # Default 100 if extracted
                        str(question_path),
                        json.dumps(alternatives),
                        q.get('error')
                    ))
                conn.commit()

repository = ExtractionRepository()
