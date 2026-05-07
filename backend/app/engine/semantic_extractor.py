from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY


def extract_exam_structure(raw_text: str) -> dict:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
Você é um analisador de provas de programação introdutória em C.
Leia o texto da prova abaixo e extraia apenas as questões de programação (que pedem ao aluno para escrever código C).
Ignore questões dissertativas, de múltipla escolha ou teóricas.

Para cada questão de código, extraia:
- "number": número ou identificador da questão (string)
- "type": sempre "code"
- "statement": enunciado completo da questão
- "required_structures": estruturas de controle exigidas — valores possíveis: "If","For","While","DoWhile","Switch" (lista vazia se não especificado)
- "forbidden_structures": estruturas explicitamente proibidas (lista vazia se não houver)
- "requires_loop": true se o enunciado exige laço de repetição, false caso contrário

Texto da prova:
{raw_text}

Retorne apenas o JSON com a chave "questions" contendo a lista de questões de código.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    import json
    import re
    text = response.text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)
