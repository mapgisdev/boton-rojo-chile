"""
src/training/validation/metrics.py — Métricas científicas de evaluación y verificación para BR-HR.

Implementa métricas de discriminación, calibración, destreza y concentración territorial.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)


def compute_binary_metrics(y_true: np.ndarray, y_pred_binary: np.ndarray) -> Dict[str, float]:
    """Calcula métricas de contingencia estándar (POD, FAR, CSI, Precisión, Recall, F1)."""
    yt = np.asarray(y_true, dtype=int)
    yp = np.asarray(y_pred_binary, dtype=int)

    tn, fp, fn, tp = confusion_matrix(yt, yp, labels=[0, 1]).ravel()

    pod = tp / (tp + fn) if (tp + fn) > 0 else 0.0  # Probability of Detection / Recall
    far = fp / (tp + fp) if (tp + fp) > 0 else 0.0  # False Alarm Ratio
    csi = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0  # Critical Success Index
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    f1 = 2 * (precision * pod) / (precision + pod) if (precision + pod) > 0 else 0.0

    return {
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "pod": round(float(pod), 4),
        "far": round(float(far), 4),
        "csi": round(float(csi), 4),
        "precision": round(float(precision), 4),
        "f1": round(float(f1), 4),
        "accuracy": round(float(accuracy), 4),
    }


def compute_probabilistic_metrics(y_true: np.ndarray,
                                  y_prob: np.ndarray,
                                  sample_weight: Optional[np.ndarray] = None) -> Dict[str, float]:
    """Calcula métricas probabilísticas (PR-AUC, ROC-AUC, Brier Score)."""
    yt = np.asarray(y_true, dtype=int)
    yp = np.clip(np.asarray(y_prob, dtype=float), 0.0, 1.0)

    try:
        roc_auc = float(roc_auc_score(yt, yp, sample_weight=sample_weight))
    except ValueError:
        roc_auc = 0.5

    try:
        pr_auc = float(average_precision_score(yt, yp, sample_weight=sample_weight))
    except ValueError:
        pr_auc = 0.0

    brier = float(brier_score_loss(yt, yp, sample_weight=sample_weight))

    return {
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 6),
    }


def compute_territorial_concentration(y_true: np.ndarray,
                                      y_score: np.ndarray) -> Dict[str, float]:
    """Calcula el % de igniciones capturadas en el top 5 %, 10 % y 20 % del territorio con mayor riesgo."""
    yt = np.asarray(y_true, dtype=int)
    ys = np.asarray(y_score, dtype=float)

    total_fires = yt.sum()
    if total_fires == 0:
        return {"top_5pct_fires": 0.0, "top_10pct_fires": 0.0, "top_20pct_fires": 0.0}

    n_samples = len(ys)
    order = np.argsort(-ys)
    y_sorted = yt[order]

    k5 = max(1, int(n_samples * 0.05))
    k10 = max(1, int(n_samples * 0.10))
    k20 = max(1, int(n_samples * 0.20))

    top_5 = y_sorted[:k5].sum() / total_fires * 100.0
    top_10 = y_sorted[:k10].sum() / total_fires * 100.0
    top_20 = y_sorted[:k20].sum() / total_fires * 100.0

    return {
        "top_5pct_fires": round(float(top_5), 2),
        "top_10pct_fires": round(float(top_10), 2),
        "top_20pct_fires": round(float(top_20), 2),
    }
