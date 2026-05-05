from __future__ import annotations

from collections import Counter
from typing import List

import numpy as np
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from scipy.sparse import hstack, issparse
from sqlalchemy.orm import Session
from umap import UMAP

from app.models.orm import QuestionCluster, Submission

MIN_SUBMISSIONS = 3


class ClusteringResult:
    def __init__(self, clusters: list[dict], scatter: list[dict]):
        self.clusters = clusters
        self.scatter = scatter


def cluster_question(question_id: int, db: Session) -> ClusteringResult | None:
    submissions: List[Submission] = (
        db.query(Submission).filter(Submission.question_id == question_id).all()
    )

    if len(submissions) < MIN_SUBMISSIONS:
        return None

    codes = [s.code or "" for s in submissions]
    ast_lists = [s.ast_structures or [] for s in submissions]

    features = _build_features(codes, ast_lists)

    umap_cluster = UMAP(n_components=5, random_state=42, min_dist=0.0)
    umap_viz = UMAP(n_components=2, random_state=42)

    embedded_cluster = umap_cluster.fit_transform(features)
    embedded_viz = umap_viz.fit_transform(features)

    labels = HDBSCAN(min_cluster_size=2).fit_predict(embedded_cluster)

    _persist_results(submissions, labels, embedded_viz, question_id, db)

    return _build_result(submissions, labels, embedded_viz)


def _build_features(codes: list[str], ast_lists: list[list[str]]):
    tfidf = TfidfVectorizer(analyzer="word", token_pattern=r"[a-zA-Z_][a-zA-Z0-9_]*")
    tfidf_matrix = tfidf.fit_transform(codes)

    mlb = MultiLabelBinarizer()
    onehot = mlb.fit_transform(ast_lists)

    combined = hstack([tfidf_matrix, onehot])
    if issparse(combined):
        combined = combined.toarray()
    return combined.astype(np.float32)


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

        qc = QuestionCluster(
            question_id=question_id,
            cluster_label=int(label),
            size=len(indices),
            dominant_error=dominant_error,
            representative_submission_id=submissions[representative].id,
        )
        db.add(qc)

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

    return ClusteringResult(clusters=list(clusters.values()), scatter=scatter)
