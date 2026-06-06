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


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n_sample = int(args[0]) if args else 10
    use_docker = "--no-docker" not in sys.argv

    pdfs = sorted(glob.glob(os.path.join(PROVAS_DIR, "*.pdf")))[:n_sample]
    print(f"Amostra: {len(pdfs)} provas | Docker: {use_docker}\n")

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
            if use_docker:
                t1 = time.perf_counter()
                dyn = compile_and_run(code, [])
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
        print("\n=== DISTRIBUIÇÃO DE CATEGORIAS (heurísticas) ===")
        for cat, c in Counter(r["category"] for r in records).most_common():
            print(f"  {c:3d}  {cat}")

    # ---------------- CLUSTERING DE UMA QUESTÃO ----------------
    by_q = Counter(r["q"] for r in records)
    target_q = by_q.most_common(1)[0][0]
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
