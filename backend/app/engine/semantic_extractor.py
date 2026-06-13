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
- "required_functions": funções que o enunciado EXIGE que o aluno implemente (lista vazia se a questão não pede funções específicas)

Cada item de "required_functions" é um objeto com:
- "name": nome exato da função exigida (string)
- "param_count": número de parâmetros exigidos (inteiro), ou null se o enunciado não especificar
- "return_type": tipo de retorno em C exigido, ex: "int", "float", "void", "char" (string), ou null se não especificado
- "requires_recursion": true SOMENTE se o enunciado exigir explicitamente que a função seja recursiva, false caso contrário
- "requires_pointer_param": true SOMENTE se o enunciado exigir passagem por referência / ponteiro (ex: "altere o valor", "por referência", "usando ponteiros"), false caso contrário

Regras para "required_functions":
- Extraia apenas funções que o enunciado obriga o aluno a CRIAR (ex: "implemente uma função fatorial", "crie a função int soma(int a, int b)").
- NÃO inclua funções de biblioteca (printf, scanf, malloc, etc.) nem a função main.
- Se a assinatura aparecer no enunciado (ex: "int soma(int a, int b)"), preencha name, param_count e return_type a partir dela.
- Na dúvida sobre param_count ou return_type, use null em vez de adivinhar.
- requires_recursion e requires_pointer_param só são true quando o enunciado pede isso de forma explícita.

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
    data = json.loads(text)

    # O modelo às vezes ignora o invólucro e devolve a lista de questões direto;
    # normaliza para sempre retornar {"questions": [...]}.
    if isinstance(data, list):
        return {"questions": data}
    if isinstance(data, dict) and "questions" not in data:
        return {"questions": []}
    return data
