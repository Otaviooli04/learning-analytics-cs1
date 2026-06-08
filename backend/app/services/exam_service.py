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
            required_functions=q.get("required_functions", []),
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
                    "matricula": s.matricula,
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


def get_exam_students(exam: Exam) -> dict:
    # latest submission per (matricula, question_number)
    student_map: dict[str, dict[str, object]] = {}
    for q in exam.questions:
        for s in q.submissions:
            name = s.matricula
            if not name:
                continue
            if name not in student_map:
                student_map[name] = {}
            prev = student_map[name].get(q.number)
            if prev is None or s.id > prev.id:
                student_map[name][q.number] = s

    question_numbers = [q.number for q in exam.questions]
    students = []
    for name in sorted(student_map.keys()):
        q_subs = student_map[name]
        questions_status = []
        for q in exam.questions:
            s = q_subs.get(q.number)
            questions_status.append({
                "question_number": q.number,
                "submission_id": s.id if s else None,
                "passed": s.all_tests_passed if s else None,
                "error_category": (s.error_category or "") if s else None,
            })
        answered = sum(1 for qs in questions_status if qs["submission_id"] is not None)
        passed = sum(1 for qs in questions_status if qs["passed"])
        students.append({
            "matricula": name,
            "questions": questions_status,
            "answered_count": answered,
            "passed_count": passed,
            "total_questions": len(question_numbers),
        })

    return {"question_numbers": question_numbers, "students": students}


def get_student_detail(exam: Exam, matricula: str) -> dict:
    best: dict[str, tuple] = {}
    for q in exam.questions:
        for s in q.submissions:
            name = s.matricula
            if name != matricula:
                continue
            prev = best.get(q.number)
            if prev is None or s.id > prev[1].id:
                best[q.number] = (q, s)

    submissions = []
    for q in exam.questions:
        if q.number in best:
            _, s = best[q.number]
            submissions.append({
                "question_number": q.number,
                "statement": q.statement,
                "submission_id": s.id,
                "code": s.code,
                "all_tests_passed": s.all_tests_passed,
                "compile_error": s.compile_error or "",
                "error_category": s.error_category or "",
                "pedagogical_diagnosis": s.pedagogical_diagnosis or "",
                "actionable_feedback": s.actionable_feedback or "",
                "submitted_at": s.submitted_at.isoformat(),
                "test_results": [
                    {"input": tr.input, "expected_output": tr.expected_output,
                     "actual_output": tr.actual_output, "passed": tr.passed}
                    for tr in s.test_results
                ],
            })
        else:
            submissions.append({
                "question_number": q.number,
                "statement": q.statement,
                "submission_id": None,
                "code": None,
                "all_tests_passed": None,
                "compile_error": "",
                "error_category": "",
                "pedagogical_diagnosis": "",
                "actionable_feedback": "",
                "submitted_at": None,
                "test_results": [],
            })

    answered = sum(1 for s in submissions if s["submission_id"] is not None)
    passed = sum(1 for s in submissions if s["all_tests_passed"])
    return {
        "matricula": matricula,
        "total_questions": len(exam.questions),
        "answered_count": answered,
        "passed_count": passed,
        "submissions": submissions,
    }
