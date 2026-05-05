from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY


def generate_cluster_insights(question_statement: str, clusters: list[dict]) -> list[dict]:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")
    if not clusters:
        return []

    client = genai.Client(api_key=GEMINI_API_KEY)
    results = []

    for cluster in clusters:
        prompt = f"""
Você é um assistente pedagógico especializado em ensino de programação introdutória em C.

Enunciado da questão:
{question_statement}

Código representativo de um grupo de alunos com padrão de erro similar:
```c
{cluster["representative_code"]}
```

Erro predominante identificado automaticamente: {cluster["dominant_error"]}
Tamanho do grupo: {cluster["size"]} aluno(s)

Com base nisso, gere um insight pedagógico conciso para o professor, contendo:
- O que esse grupo de alunos errou ou não compreendeu
- Uma sugestão de intervenção didática

Seja direto e objetivo. Máximo 4 frases.
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="text/plain",
            ),
        )

        results.append({
            "cluster_id": cluster["cluster_id"],
            "size": cluster["size"],
            "dominant_error": cluster["dominant_error"],
            "insight": response.text.strip(),
        })

    return results
