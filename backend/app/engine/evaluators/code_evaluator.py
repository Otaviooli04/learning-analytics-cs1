from app.engine.dynamic_analyzer import compile_and_run
from app.engine.static_analyzer import extract_control_flow
from app.engine.heuristics import classify_error, check_structures


def evaluate_code(code: str, test_cases: list = None, required_structures: list = None, forbidden_structures: list = None) -> dict:
    tc = test_cases or []
    req = required_structures or []
    forb = forbidden_structures or []

    dynamic_result = compile_and_run(code, tc)
    static_result = extract_control_flow(code)
    diagnosis = classify_error(dynamic_result, static_result, req, forb)

    structure_check = None
    if dynamic_result["success"]:
        structure_check = check_structures(static_result.get("structures", []), req, forb)

    return {
        "compile_error": dynamic_result.get("compile_error", ""),
        "warnings": dynamic_result.get("warnings", ""),
        "test_results": dynamic_result.get("test_results", []),
        "all_tests_passed": dynamic_result.get("all_tests_passed"),
        "structure_check": structure_check,
        "diagnosis": diagnosis,
        "ast_structures": static_result.get("structures", []),
    }
