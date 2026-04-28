from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY
from app.models.schemas import ExerciseMetadata


def extract_metadata_from_prompt(enunciado: str) -> dict:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada. Defina a variável de ambiente antes de usar este módulo.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    Você é um analisador semântico de exercícios de programação em C para turmas introdutórias (CS1).
    Leia o enunciado abaixo e extraia as exigências estruturais de controle de fluxo.

    Regras de extração:
    - "requires_loop": true se o enunciado exige explicitamente ou implicitamente um laço de repetição.
    - "required_structures": lista com as estruturas obrigatórias mencionadas. Valores válidos: "If", "For", "While", "DoWhile", "Switch".
    - "forbidden_structures": lista com estruturas que o enunciado proíbe explicitamente.
    - Se nenhuma estrutura for mencionada, retorne listas vazias.

    Enunciado: {enunciado}
    """

    response = client.models.generate_content(
        model="",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExerciseMetadata,
        ),
    )

    return response.parsed.model_dump()
