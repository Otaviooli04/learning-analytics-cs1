"""Valida o pipeline com provas REAIS (Moodle/CodeRunner export, Turma 1).

Extrai o código submetido por questão de uma amostra de PDFs, roda análise
estática (tree-sitter) + dinâmica (Docker GCC) + heurísticas, e mede eficiência
e qualidade. Faz clustering de uma questão entre os alunos.

Uso: python tools/analyze_real_provas.py [n_amostra] [--no-docker]
"""
import os
import re
import sys
import time
import glob
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fitz  # pymupdf
import numpy as np

from app.engine.static_analyzer import extract_control_flow
from app.engine.heuristics import classify_error

PROVAS_DIR = "/mnt/c/Users/otavi/Desktop/Provas Fundamentos/Provas-T1"

GLYPH_OK = ""    # ✓ caso passou
GLYPH_FAIL = ""  # ✗ caso falhou
# marcadores que encerram a tabela de testes (veredito / solução do autor / rodapé)
_STOP_WORDS = ("Histórico", "Passo", "Estado", "Pontos", "Seu", "Passou",
               "Testing", "Show/hide", "Notas", "Mostrar", "Esconder")


def extract_submissions(pdf_path: str) -> dict:
    """Retorna {qnum: codigo_final} extraído do histórico do PDF."""
    doc = fitz.open(pdf_path)
    txt = "".join(p.get_text() for p in doc)
    doc.close()

    # divide por "Questão N" e pega o último Enviar:/Salvou: de cada bloco
    parts = re.split(r"Quest[ãa]o\s+(\d+)", txt)
    # parts = [pre, num1, bloco1, num2, bloco2, ...]
    out = {}
    for i in range(1, len(parts) - 1, 2):
        qnum = parts[i]
        block = parts[i + 1]
        codes = re.findall(
            r"(?:Enviar|Salvou):\s*(#include.*?)(?:Incorreto|Incompleto|Correto|Parcial)",
            block, re.S,
        )
        if not codes:
            codes = re.findall(r"(#include\s*<stdio\.h>.*?return\s+0;\s*\})", block, re.S)
        if codes:
            # versão mais completa (evita pegar um "Salvou" truncado); normaliza
            # espaços e RE-INSERE newline após #include — o histórico do PDF achata
            # as quebras de linha, o que quebraria a diretiva de pré-processador.
            code = max(codes, key=len)
            code = re.sub(r"\s+", " ", code).strip()
            code = re.sub(r'(#include\s*[<"][^>"]*[>"])', r"\1\n", code)
            out.setdefault(qnum, code)
    return out


def _join_tokens(toks: list) -> str:
    """Junta tokens (y, x, palavra) preservando linhas: agrupa por y, ordena por x.

    Para saídas multi-linha (matrizes) reconstrói cada linha pela coordenada Y
    e mantém a ordem das colunas pela coordenada X.
    """
    if not toks:
        return ""
    lines = {}
    for y, x, wd in toks:
        lines.setdefault(round(y), []).append((x, wd))
    return "\n".join(
        " ".join(wd for _, wd in sorted(lines[y]))
        for y in sorted(lines)
    )


def _parse_tables_on_page(words: list) -> list:
    """Extrai casos das tabelas Input/Esperado/Got de UMA página via geometria.

    Em vez de linearizar o texto (que mistura as 3 colunas), usa as coordenadas X
    dos cabeçalhos para separar Input | Esperado | Got, e o X dos glifos ✓/✗ na
    margem esquerda para delimitar cada linha de teste. Lida com float, string
    (aprovado/reprovado), entrada multivalor e saída multi-linha (matriz).

    Retorna [{"input", "expected", "got", "passed", "y"}].
    """
    rows_out = []
    for hw in [w for w in words if w[4] == "Input"]:
        hy = hw[1]
        same = [w for w in words if abs(w[1] - hy) < 3]
        esp = next((w for w in same if w[4] in ("Esperado", "Resultado") and w[0] > hw[0]), None)
        got = next((w for w in same if w[4] == "Got" and w[0] > hw[0]), None)
        if not (esp and got):
            continue
        b1 = esp[0] - 8       # fronteira input | esperado
        b2 = got[0] - 8       # fronteira esperado | got
        x_glyph = hw[0] - 8   # tokens à esquerda disto = glifo de margem (início de linha)

        body = sorted((w for w in words if w[1] > hy + 4), key=lambda w: (round(w[1], 1), w[0]))
        cur = None
        for x0, y0, x1, y1, word, *_ in body:
            if any(word.startswith(s) for s in _STOP_WORDS) or "▼" in word or "▸" in word:
                break  # fim da tabela: veredito / solução do autor / gutter de código
            if word in (GLYPH_OK, GLYPH_FAIL) and x0 < x_glyph:
                if cur:
                    rows_out.append(cur)
                cur = {"passed": word == GLYPH_OK, "in": [], "esp": [], "got": [], "y": y0}
                continue
            if cur is None or word in (GLYPH_OK, GLYPH_FAIL):
                continue  # ignora glifo de fechamento à direita
            bucket = "in" if x0 < b1 else "esp" if x0 < b2 else "got"
            cur[bucket].append((y0, x0, word))
        if cur:
            rows_out.append(cur)

    for r in rows_out:
        # input via stdin é delimitado por espaço — achata em uma linha (também
        # deduplica casos onde o PDF quebrou a entrada em duas linhas). Já a saída
        # esperada/got preserva as linhas (matrizes, valores multi-linha).
        r["input"] = " ".join(
            wd for _, _, wd in sorted(r.pop("in"), key=lambda t: (round(t[0]), t[1])))
        r["expected"] = _join_tokens(r.pop("esp"))
        r["got"] = _join_tokens(r.pop("got"))
    # input de teste é sempre numérico (n, ints/floats, matrizes) — rejeita linhas
    # contaminadas por rodapé que escaparam do corte por _STOP_WORDS.
    return [r for r in rows_out
            if r["expected"] and re.fullmatch(r"[\d\s.\-]+", r["input"])]


def extract_testcases(pdf_path: str) -> dict:
    """Retorna {qnum: [{"input","expected","passed","clean"}, ...]} via geometria.

    Mapeia cada tabela à questão cujo cabeçalho 'Questão N' a precede na ordem de
    leitura (carrega o número entre páginas). `clean=True` quando a linha passou e
    expected==got (alta confiança); casos ambíguos (ex.: matriz mal-alinhada) ficam
    com clean=False para serem filtrados a jusante.
    """
    doc = fitz.open(pdf_path)
    out = {}
    cur_q = None
    for page in doc:
        words = page.get_text("words")  # (x0,y0,x1,y1,palavra,bloco,linha,nº)
        events = []  # (y, "q", num) e (y, "table", row)
        for x0, y0, x1, y1, word, *_ in words:
            if word == "Questão":
                # o número fica logo à direita, ligeiramente acima (estilo superscript)
                num = next((w[4] for w in words if abs(w[1] - y0) < 8
                            and 0 < w[0] - x0 < 60 and w[4].isdigit()), None)
                if num:
                    events.append((y0, "q", num))
        for r in _parse_tables_on_page(words):
            events.append((r["y"], "table", r))
        for _, kind, payload in sorted(events, key=lambda e: e[0]):
            if kind == "q":
                cur_q = payload
            elif cur_q is not None:
                clean = payload["passed"] and payload["expected"] == payload["got"]
                out.setdefault(cur_q, []).append({
                    "input": payload["input"],
                    "expected": payload["expected"],
                    "passed": payload["passed"],
                    "clean": clean,
                })
    doc.close()
    return out


def pool_testcases(pdfs: list) -> dict:
    """Monta a suíte oficial por questão juntando as tabelas de todos os alunos.

    A suíte completa aparece nas submissões que passaram em TODOS os casos (linhas
    ✓ com expected==got). Faz dedup por input e prioriza casos 'clean'; mantém a
    versão limpa quando o mesmo input aparece sujo em outra prova.
    """
    by_q_input = {}  # q -> input -> {"expected","clean","passed"}
    for pdf in pdfs:
        for q, cases in extract_testcases(pdf).items():
            slot = by_q_input.setdefault(q, {})
            for c in cases:
                prev = slot.get(c["input"])
                if prev is None or (c["clean"] and not prev["clean"]):
                    slot[c["input"]] = c
    pooled = {}
    for q, slot in by_q_input.items():
        pooled[q] = [
            {"input": c["input"], "expected_output": c["expected"]}
            for c in slot.values()
        ]
    return pooled


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n_sample = int(args[0]) if args else 10
    use_docker = "--no-docker" not in sys.argv

    pdfs = sorted(glob.glob(os.path.join(PROVAS_DIR, "*.pdf")))[:n_sample]
    print(f"Amostra: {len(pdfs)} provas | Docker: {use_docker}\n")

    tc_by_q = pool_testcases(pdfs)
    print("Test cases extraídos por questão:")
    for q in sorted(tc_by_q):
        print(f"  Q{q}: {len(tc_by_q[q])} casos")
        for c in tc_by_q[q]:
            inp = c["input"].replace("\n", " | ")
            exp = c["expected_output"].replace("\n", " / ")
            print(f"      in={inp!r}  ->  esperado={exp!r}")
    print()

    records = []  # {student, q, code, parse_ok, structures, functions, risky, category, t_static, t_dyn}
    t_static_total = 0.0
    t_dyn_total = 0.0

    if use_docker:
        from app.engine.dynamic_analyzer import compile_and_run

    for pdf in pdfs:
        student = os.path.basename(pdf).replace(".pdf", "")
        subs = extract_submissions(pdf)
        for q, code in sorted(subs.items()):
            t0 = time.perf_counter()
            static = extract_control_flow(code)
            t_static = time.perf_counter() - t0
            t_static_total += t_static

            category = None
            t_dyn = 0.0
            tcs = tc_by_q.get(q, [])
            if use_docker:
                t1 = time.perf_counter()
                dyn = compile_and_run(code, tcs)
                t_dyn = time.perf_counter() - t1
                t_dyn_total += t_dyn
                category = classify_error(dyn, static)["error_category"]

            records.append({
                "student": student, "q": q, "code": code,
                "parse_ok": static["parse_ok"],
                "structures": static["structures"],
                "functions": [f["name"] for f in static["functions"]],
                "risky": static["risky_loops"],
                "category": category,
                "tested": bool(tcs),
                "t_static": t_static, "t_dyn": t_dyn,
            })

    # ---------------- RELATÓRIO ----------------
    n = len(records)
    print(f"=== EXTRAÇÃO E ANÁLISE ESTÁTICA ({n} submissões) ===")
    parse_ok = sum(r["parse_ok"] for r in records)
    print(f"parse_ok (compila limpo): {parse_ok}/{n} = {parse_ok/n:.0%}")
    print(f"NÃO compila (parse_ok=False): {n-parse_ok}/{n} = {(n-parse_ok)/n:.0%}")
    com_estrutura = sum(1 for r in records if r["structures"])
    print(f"com estruturas extraídas (mesmo quebrado): {com_estrutura}/{n} = {com_estrutura/n:.0%}")
    com_risco = sum(1 for r in records if r["risky"])
    print(f"com off-by-one detectado: {com_risco}/{n}")
    print(f"\nEFICIÊNCIA estática: {t_static_total/n*1000:.2f} ms/submissão (total {t_static_total:.2f}s)")

    if use_docker:
        print(f"EFICIÊNCIA dinâmica (Docker): {t_dyn_total/n:.2f} s/submissão (total {t_dyn_total:.1f}s)")
        tested = [r for r in records if r["tested"]]
        untested = [r for r in records if not r["tested"]]
        print(f"\n=== CATEGORIAS — questões COM test cases ({len(tested)} subs) ===")
        for cat, c in Counter(r["category"] for r in tested).most_common():
            print(f"  {c:3d}  {cat}")
        print(f"\n=== CATEGORIAS — questões SEM test cases ({len(untested)} subs) ===")
        for cat, c in Counter(r["category"] for r in untested).most_common():
            print(f"  {c:3d}  {cat}")

    # ---------------- CLUSTERING DE UMA QUESTÃO (preferir uma com test cases) ----------------
    by_q = Counter(r["q"] for r in records)
    tested_qs = [q for q in by_q if any(r["tested"] for r in records if r["q"] == q)]
    target_q = max(tested_qs or by_q, key=lambda q: by_q[q])
    q_recs = [r for r in records if r["q"] == target_q]
    print(f"\n=== CLUSTERING — Questão {target_q} ({len(q_recs)} alunos) ===")
    if len(q_recs) >= 5 and use_docker:
        _cluster_real(q_recs)
    else:
        print("  (amostra insuficiente ou sem Docker para categorias)")


def _cluster_real(q_recs):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder
    from sklearn.metrics import silhouette_score
    from scipy.sparse import hstack
    from umap import UMAP
    from hdbscan import HDBSCAN

    codes = [r["code"] for r in q_recs]
    cats = [r["category"] or "?" for r in q_recs]
    n = len(q_recs)

    tfidf = TfidfVectorizer(analyzer="word", token_pattern=r"[a-zA-Z_][a-zA-Z0-9_]*", ngram_range=(1, 2))
    matrix = tfidf.fit_transform(codes)
    onehot_ast = MultiLabelBinarizer().fit_transform([r["structures"] for r in q_recs])
    onehot_cat = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit_transform(
        np.array(cats).reshape(-1, 1))
    feats = np.hstack([hstack([matrix, onehot_ast]).toarray(), onehot_cat]).astype(np.float32)

    t0 = time.perf_counter()
    emb = UMAP(n_components=min(5, n - 1), n_neighbors=min(15, n - 1),
               random_state=42, min_dist=0.0, init="random").fit_transform(feats)
    labels = HDBSCAN(min_cluster_size=2, min_samples=1).fit_predict(emb)
    t_cluster = time.perf_counter() - t0

    n_clusters = len(set(labels) - {-1})
    noise = float(np.mean(labels == -1))
    mask = labels != -1
    sil = None
    if mask.sum() >= 2 and len(set(labels[mask])) >= 2:
        sil = float(silhouette_score(emb[mask], labels[mask]))
    print(f"  clusters={n_clusters} | noise={noise:.0%} | silhouette={sil} | tempo={t_cluster:.2f}s")
    # pseudo-purity via categoria dominante por cluster
    for lab in sorted(set(labels) - {-1}):
        idx = [i for i in range(n) if labels[i] == lab]
        dom = Counter(cats[i] for i in idx).most_common(1)[0]
        print(f"    cluster {lab}: {len(idx)} alunos, erro dominante = {dom[0]} ({dom[1]}/{len(idx)})")


if __name__ == "__main__":
    main()
