from app.llm.semantic_extractor import extract_metadata_from_prompt


def analyze_exercise_prompt(prompt: str) -> dict:
    return extract_metadata_from_prompt(prompt)
