from app.engine.document_parser import parse_document
from app.engine.semantic_extractor import extract_exam_structure


def process_exam_upload(file_bytes: bytes, filename: str) -> dict:
    raw_text = parse_document(file_bytes, filename)
    structure = extract_exam_structure(raw_text)
    return {"raw_text": raw_text, "structure": structure}
