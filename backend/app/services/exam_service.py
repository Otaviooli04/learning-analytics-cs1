from collections import Counter
from sqlalchemy.orm import Session
from app.engine.document_parser import parse_document
from app.engine.semantic_extractor import extract_exam_structure
from app.models.orm import Exam, Question, TestCase


def process_exam_upload(file_bytes: bytes, filename: str, db: Session, turma_id=None) -> Exam:
    raw_text = parse_document(file_bytes, filename)
    structure = extract_exam_structure(raw_text)

    exam = Exam(filename=filename, raw_text=raw_text, turma_id=turma_id)
    db.add(exam)
    db.flush()

    for q in structure.get("questions", []):
        db.add(Question(
            exam_id=exam.id,
            number=q["number"],
            statement=q["statement"],
            required_structures=q.get("required_structures", []),
            forbidden_structures=q.get("forbidden_structures", []),
            requires_loop=q.get("requires_loop", False),
        ))

    db.commit()
    db.refresh(exam)
    return exam


def add_test_cases(question_id: int, test_cases: list[dict], db: Session) -> int:
    for tc in test_cases:
        db.add(TestCase(
            question_id=question_id,
            input=tc["input"],
            expected_output=tc["expected_output"],
        ))
    db.commit()
    return len(test_cases)


def get_exam_results(exam: Exam) -> dict:
    questions = []
    for q in exam.questions:
        subs = q.submissions
        error_dist = [
            {"error_category": cat, "count": count}
            for cat, count in Counter(s.error_category for s in subs).most_common()
        ]
        questions.append({
            "question_number": q.number,
            "statement": q.statement,
            "total_submissions": len(subs),
            "passed_count": sum(1 for s in subs if s.all_tests_passed),
            "error_distribution": error_dist,
            "submissions": [
                {
                    "id": s.id,
                    "code": s.code,
                    "all_tests_passed": s.all_tests_passed,
                    "compile_error": s.compile_error or "",
                    "diagnosis": {
                        "error_category": s.error_category,
                        "pedagogical_diagnosis": s.pedagogical_diagnosis,
                        "actionable_feedback": s.actionable_feedback,
                    },
                    "submitted_at": s.submitted_at.isoformat(),
                }
                for s in subs
            ],
        })
    return {
        "exam_id": exam.id,
        "filename": exam.filename,
        "questions": questions,
    }
