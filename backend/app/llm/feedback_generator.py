import json
import re

from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY


def generate_cluster_insights(question_statement: str, clusters: list[dict]) -> list[dict]:
    """Gera um insight pedagógico por cluster em UMA única chamada ao Gemini.

    Cada item de `clusters` precisa de cluster_id, size, dominant_error e
    representative_code. O batching mantém o nº de requisições em 1 por questão
    (em vez de uma por cluster), reduzindo latência e risco de rate-limit (429).
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")
    if not clusters:
        return []

    client = genai.Client(api_key=GEMINI_API_KEY)

    blocos = "\n\n".join(
        f"""[Cluster {c["cluster_id"]}] — erro predominante: {c["dominant_error"]}; {c["size"]} aluno(s)
Código representativo:
```c
{c["representative_code"]}
```"""
        for c in clusters
    )

    prompt = f"""
Você é um assistente pedagógico especializado em ensino de programação introdutória em C.

Enunciado da questão:
{question_statement}

Abaixo estão grupos de alunos com padrões de erro similares. Para CADA grupo, gere um insight pedagógico conciso para o professor contendo:
- o que esse grupo de alunos errou ou não compreendeu;
- uma sugestão de intervenção didática.
Seja direto e objetivo. Máximo 4 frases por grupo.

{blocos}

Retorne APENAS um JSON: uma lista de objetos, um por grupo, no formato
{{"cluster_id": <int>, "insight": "<texto>"}}.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    parsed = _parse_insights(response.text)
    by_id = {item.get("cluster_id"): item.get("insight", "") for item in parsed}

    return [
        {
            "cluster_id": c["cluster_id"],
            "size": c["size"],
            "dominant_error": c["dominant_error"],
            "insight": by_id.get(c["cluster_id"], "").strip(),
        }
        for c in clusters
    ]


def _parse_insights(text: str) -> list[dict]:
    """Parsing defensivo: o modelo às vezes embrulha em ```json``` ou devolve
    {"insights": [...]} em vez da lista crua."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []
    if isinstance(data, dict):
        for key in ("insights", "clusters", "data"):
            if isinstance(data.get(key), list):
                return data[key]
        return []
    if isinstance(data, list):
        return data
    return []
