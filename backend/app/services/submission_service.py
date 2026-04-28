from app.engine.evaluators.code_evaluator import evaluate_code
from app.engine.evaluators.dissertative_evaluator import evaluate_dissertative
from app.engine.evaluators.multiple_choice_evaluator import evaluate_multiple_choice


def evaluate_submission(question_type: str, payload: dict) -> dict:
    if question_type == "code":
        return evaluate_code(payload["code"])
    if question_type == "dissertative":
        return evaluate_dissertative(payload["answer"], payload["rubric"])
    if question_type == "multiple_choice":
        return evaluate_multiple_choice(payload["answer"], payload["expected"])
    raise ValueError(f"Tipo de questão desconhecido: {question_type}")
