from __future__ import annotations

from collections import Counter
from enum import Enum
from typing import List, Optional

import numpy as np
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder
from scipy.sparse import hstack, issparse
from sqlalchemy.orm import Session, joinedload
from umap import UMAP

from app.models.orm import QuestionCluster, Submission

MIN_SUBMISSIONS = 3


class FeatureStrategy(str, Enum):
    TFIDF = "tfidf"
    TFIDF_NGRAM = "tfidf_ngram"
    TFIDF_CATEGORY = "tfidf_category"
    TFIDF_BEHAVIORAL = "tfidf_behavioral"


class ClusteringResult:
    def __init__(
        self,
        clusters: list[dict],
        scatter: list[dict],
        silhouette: Optional[float],
        strategy: FeatureStrategy,
    ):
        self.clusters = clusters
        self.scatter = scatter
        self.silhouette = silhouette
        self.strategy = strategy


def cluster_question(
    question_id: int,
    db: Session,
    strategy: FeatureStrategy = FeatureStrategy.TFIDF,
) -> ClusteringResult | None:
    submissions: List[Submission] = (
        db.query(Submission)
        .options(joinedload(Submission.test_results))
        .filter(Submission.question_id == question_id)
        .all()
    )

    if len(submissions) < MIN_SUBMISSIONS:
        return None

    codes = [s.code or "" for s in submissions]
    ast_lists = [s.ast_structures or [] for s in submissions]

    features = _build_features(codes, ast_lists, submissions, strategy)

    n = len(submissions)
    n_components_cluster = min(5, n - 1)
    n_neighbors = min(15, n - 1)
    umap_init = "random" if n < 10 else "spectral"

    umap_cluster = UMAP(
        n_components=n_components_cluster,
        n_neighbors=n_neighbors,
        random_state=42,
        min_dist=0.0,
        init=umap_init,
    )
    umap_viz = UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        random_state=42,
        init=umap_init,
    )

    embedded_cluster = umap_cluster.fit_transform(features)
    embedded_viz = umap_viz.fit_transform(features)

    labels = HDBSCAN(min_cluster_size=2).fit_predict(embedded_cluster)

    silhouette = _compute_silhouette(embedded_cluster, labels)

    _persist_results(submissions, labels, embedded_viz, question_id, db)

    return _build_result(submissions, labels, embedded_viz, silhouette, strategy)


# ---------------------------------------------------------------------------
# Feature builders
# ---------------------------------------------------------------------------

def _build_features(
    codes: list[str],
    ast_lists: list[list[str]],
    submissions: List[Submission],
    strategy: FeatureStrategy,
) -> np.ndarray:
    if strategy == FeatureStrategy.TFIDF:
        return _build_tfidf(codes, ast_lists)
    if strategy == FeatureStrategy.TFIDF_NGRAM:
        return _build_tfidf_ngram(codes, ast_lists)
    if strategy == FeatureStrategy.TFIDF_CATEGORY:
        return _build_tfidf_category(codes, ast_lists, submissions)
    if strategy == FeatureStrategy.TFIDF_BEHAVIORAL:
        return _build_tfidf_behavioral(codes, ast_lists, submissions)
    return _build_tfidf(codes, ast_lists)


def _build_tfidf(codes: list[str], ast_lists: list[list[str]]) -> np.ndarray:
    tfidf = TfidfVectorizer(
        analyzer="word", token_pattern=r"[a-zA-Z_][a-zA-Z0-9_]*"
    )
    matrix = tfidf.fit_transform(codes)
    onehot = MultiLabelBinarizer().fit_transform(ast_lists)
    return _dense(hstack([matrix, onehot]))


def _build_tfidf_ngram(codes: list[str], ast_lists: list[list[str]]) -> np.ndarray:
    tfidf = TfidfVectorizer(
        analyzer="word",
        token_pattern=r"[a-zA-Z_][a-zA-Z0-9_]*",
        ngram_range=(1, 2),
    )
    matrix = tfidf.fit_transform(codes)
    onehot = MultiLabelBinarizer().fit_transform(ast_lists)
    return _dense(hstack([matrix, onehot]))


def _build_tfidf_category(
    codes: list[str],
    ast_lists: list[list[str]],
    submissions: List[Submission],
) -> np.ndarray:
    tfidf = TfidfVectorizer(
        analyzer="word", token_pattern=r"[a-zA-Z_][a-zA-Z0-9_]*"
    )
    matrix = tfidf.fit_transform(codes)
    onehot_ast = MultiLabelBinarizer().fit_transform(ast_lists)
    onehot_cat = _category_onehot(submissions)
    return np.hstack([_dense(hstack([matrix, onehot_ast])), onehot_cat]).astype(np.float32)


def _build_tfidf_behavioral(
    codes: list[str],
    ast_lists: list[list[str]],
    submissions: List[Submission],
) -> np.ndarray:
    tfidf = TfidfVectorizer(
        analyzer="word",
        token_pattern=r"[a-zA-Z_][a-zA-Z0-9_]*",
        ngram_range=(1, 2),
    )
    matrix = tfidf.fit_transform(codes)
    onehot_ast = MultiLabelBinarizer().fit_transform(ast_lists)
    onehot_cat = _category_onehot(submissions)
    behavioral = _behavioral_features(submissions)
    return np.hstack([
        _dense(hstack([matrix, onehot_ast])),
        onehot_cat,
        behavioral,
    ]).astype(np.float32)


def _category_onehot(submissions: List[Submission]) -> np.ndarray:
    cats = np.array([s.error_category or "unknown" for s in submissions]).reshape(-1, 1)
    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    return enc.fit_transform(cats).astype(np.float32)


def _behavioral_features(submissions: List[Submission]) -> np.ndarray:
    rows = []
    for s in submissions:
        compila = 0.0 if s.compile_error else 1.0
        if s.test_results:
            fracao = sum(1 for tr in s.test_results if tr.passed) / len(s.test_results)
        else:
            fracao = 0.0
        rows.append([compila, fracao])
    return np.array(rows, dtype=np.float32)


def _dense(matrix) -> np.ndarray:
    if issparse(matrix):
        matrix = matrix.toarray()
    return matrix.astype(np.float32)


# ---------------------------------------------------------------------------
# Silhouette
# ---------------------------------------------------------------------------

def _compute_silhouette(embedded: np.ndarray, labels: np.ndarray) -> Optional[float]:
    mask = labels != -1
    unique = set(labels[mask])
    if mask.sum() < 2 or len(unique) < 2:
        return None
    return float(silhouette_score(embedded[mask], labels[mask]))


# ---------------------------------------------------------------------------
# Persistência e resultado
# ---------------------------------------------------------------------------

def _persist_results(
    submissions: List[Submission],
    labels: np.ndarray,
    embedded_viz: np.ndarray,
    question_id: int,
    db: Session,
) -> None:
    db.query(QuestionCluster).filter(QuestionCluster.question_id == question_id).delete()

    for sub, label, (x, y) in zip(submissions, labels, embedded_viz):
        sub.cluster_id = int(label)
        sub.umap_x = str(float(x))
        sub.umap_y = str(float(y))

    unique_labels = set(labels) - {-1}
    for label in unique_labels:
        indices = [i for i, l in enumerate(labels) if l == label]
        cluster_subs = [submissions[i] for i in indices]
        dominant_error = _dominant_error(cluster_subs)
        representative = _find_representative(indices, embedded_viz)
        db.add(QuestionCluster(
            question_id=question_id,
            cluster_label=int(label),
            size=len(indices),
            dominant_error=dominant_error,
            representative_submission_id=submissions[representative].id,
        ))

    db.commit()


def _dominant_error(subs: List[Submission]) -> str:
    errors = [s.error_category for s in subs if s.error_category]
    if not errors:
        return "unknown"
    return Counter(errors).most_common(1)[0][0]


def _find_representative(indices: list[int], embedded: np.ndarray) -> int:
    points = embedded[indices]
    centroid = points.mean(axis=0)
    dists = np.linalg.norm(points - centroid, axis=1)
    return indices[int(np.argmin(dists))]


def _build_result(
    submissions: List[Submission],
    labels: np.ndarray,
    embedded_viz: np.ndarray,
    silhouette: Optional[float],
    strategy: FeatureStrategy,
) -> ClusteringResult:
    clusters: dict[int, dict] = {}
    for sub, label in zip(submissions, labels):
        label = int(label)
        if label == -1:
            continue
        if label not in clusters:
            clusters[label] = {
                "cluster_id": label,
                "size": 0,
                "dominant_error": sub.error_category or "unknown",
                "representative_code": None,
                "representative_submission_id": None,
            }
        clusters[label]["size"] += 1

    scatter = [
        {
            "submission_id": sub.id,
            "x": float(x),
            "y": float(y),
            "cluster_id": int(label),
        }
        for sub, label, (x, y) in zip(submissions, labels, embedded_viz)
    ]

    return ClusteringResult(
        clusters=list(clusters.values()),
        scatter=scatter,
        silhouette=silhouette,
        strategy=strategy,
    )
