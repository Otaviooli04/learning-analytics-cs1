from app.engine.dynamic_analyzer import compile_c_code
from app.engine.static_analyzer import extract_control_flow
from app.engine.heuristics import classify_error


def evaluate_code(code: str) -> dict:
    dynamic_result = compile_c_code(code)
    static_result = extract_control_flow(code)
    diagnosis = classify_error(dynamic_result, static_result)
    return {
        "dynamic": dynamic_result,
        "static": static_result,
        "diagnosis": diagnosis,
    }
