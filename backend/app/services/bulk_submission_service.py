import io
import re
import zipfile
from sqlalchemy.orm import Session
from app.services.submission_service import evaluate_submission


def _extract_question_number(name: str) -> str | None:
    """Extrai número da questão de strings como Q1, Questao2, 1, questão 3."""
    cleaned = name.strip().lower()
    cleaned = re.sub(r'[àáâãä]', 'a', cleaned)
    cleaned = re.sub(r'[çć]', 'c', cleaned)
    cleaned = cleaned.replace(' ', '')
    m = re.search(r'(?:questao|question|q)?(\d+)$', cleaned)
    return m.group(1) if m else None


def _strip_wrapper_folder(names: list[str]) -> list[str]:
    """Remove pasta wrapper se o ZIP tiver uma pasta raiz única."""
    with_slash = [n for n in names if '/' in n]
    if not with_slash:
        return names
    tops = set(n.split('/')[0] for n in with_slash)
    if len(tops) == 1:
        prefix = tops.pop() + '/'
        return [n[len(prefix):] for n in names]
    return names


def process_bulk_zip(zip_bytes: bytes, exam_id: int, fmt: str, db: Session) -> dict:
    """
    fmt='by_student': pastas = aluno, arquivos = Q1.c
    fmt='by_question': pastas = Q1, arquivos = aluno.c
    """
    items = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        raw_names = [n for n in zf.namelist() if not n.endswith('/') and n.lower().endswith('.c')]
        normalized = _strip_wrapper_folder(raw_names)

        for raw_name, norm_name in zip(raw_names, normalized):
            parts = [p for p in norm_name.split('/') if p]
            if len(parts) < 2:
                continue

            if fmt == 'by_student':
                matricula = parts[0].strip()
                filename_stem = parts[-1][:-2]
                question_number = _extract_question_number(filename_stem)
            else:
                folder = parts[0]
                question_number = _extract_question_number(folder)
                matricula = parts[-1][:-2].strip()

            if not question_number:
                items.append({
                    'matricula': matricula,
                    'question': None,
                    'file': norm_name,
                    'status': 'error',
                    'message': 'Não foi possível identificar o número da questão pelo nome do arquivo/pasta.',
                })
                continue

            code = zf.read(raw_name).decode('utf-8', errors='replace')
            try:
                evaluate_submission(exam_id, question_number, code, db, matricula=matricula)
                items.append({
                    'matricula': matricula,
                    'question': question_number,
                    'file': norm_name,
                    'status': 'ok',
                    'message': '',
                })
            except ValueError as e:
                items.append({
                    'matricula': matricula,
                    'question': question_number,
                    'file': norm_name,
                    'status': 'error',
                    'message': str(e),
                })
            except Exception as e:
                items.append({
                    'matricula': matricula,
                    'question': question_number,
                    'file': norm_name,
                    'status': 'error',
                    'message': f'Erro interno: {e}',
                })

    processed = sum(1 for i in items if i['status'] == 'ok')
    errors = sum(1 for i in items if i['status'] == 'error')
    return {
        'total': len(items),
        'processed': processed,
        'errors': errors,
        'items': items,
    }
