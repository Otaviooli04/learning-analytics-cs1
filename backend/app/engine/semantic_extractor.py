from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY


def extract_exam_structure(raw_text: str) -> dict:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
Você é um analisador de provas de programação introdutória em C.
Leia o texto da prova abaixo e estruture cada questão identificada.

Para cada questão, extraia:
- "number": número ou identificador da questão
- "type": tipo da questão — "code" | "dissertative" | "multiple_choice"
- "statement": enunciado completo da questão

Se o tipo for "code":
  - "required_structures": estruturas de controle exigidas (valores: "If","For","While","DoWhile","Switch")
  - "forbidden_structures": estruturas explicitamente proibidas
  - "requires_loop": true se o enunciado exige laço de repetição
  - "test_cases": lista de {{ "input": "...", "expected_output": "..." }} se houver exemplos no enunciado

Se o tipo for "dissertative":
  - "rubric": critérios de correção extraídos ou inferidos do enunciado

Se o tipo for "multiple_choice":
  - "options": lista de alternativas
  - "expected_answer": letra ou texto da alternativa correta (se indicada)

Texto da prova:
{raw_text}

Retorne apenas o JSON com a chave "questions" contendo a lista de questões.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    import json
    return json.loads(response.text)
