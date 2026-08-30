"""
src/training/models/calibrator.py — Calibración de Probabilidades y Corrección Case-Control para BR-HR.

Implementa:
1. Ajuste analítico de log-odds por muestreo caso-control (King & Zeng 2001; Manski & Lerman 1977).
2. Calibración empírica Platt (Sigmoide) e Isotónica.
3. Cálculo de curvas de fiabilidad y Expected Calibration Error (ECE).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


def adjust_case_control_odds(p_sample: np.ndarray,
                             sampling_ratio_pos: float = 1.0,
                             sampling_ratio_ctrl: float = 1.0 / 7.0) -> np.ndarray:
    """Ajusta las probabilidades predichas de un modelo entrenado en case-control a la prevalencia real.

    Fórmula analítica de corrección de sesgo de selección (Manski & Lerman 1977):
        logit(p_true) = logit(p_sample) - ln(s1 / s0)
    """
    p = np.clip(np.asarray(p_sample, dtype=float), 1e-7, 1.0 - 1e-7)
    # Logit de la muestra
    logit_sample = np.log(p / (1.0 - p))
    # Ajuste por ratio de selección
    selection_bias = np.log(sampling_ratio_pos / sampling_ratio_ctrl)
    logit_true = logit_sample - selection_bias
    # Probabilidad calibrada en la escala real
    p_true = 1.0 / (1.0 + np.exp(-logit_true))
    return np.clip(p_true, 0.0, 1.0)


def compute_expected_calibration_error(y_true: np.ndarray,
                                      y_prob: np.ndarray,
                                      n_bins: int = 10) -> Dict[str, Any]:
    """Calcula el Expected Calibration Error (ECE) y la tabla de fiabilidad por deciles."""
    yt = np.asarray(y_true, dtype=float)
    yp = np.clip(np.asarray(y_prob, dtype=float), 0.0, 1.0)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    ece = 0.0
    bins_data = []

    for i in range(n_bins):
        low, high = bin_edges[i], bin_edges[i + 1]
        mask = (yp >= low) & (yp < high) if i < n_bins - 1 else (yp >= low) & (yp <= high)
        n_in_bin = int(mask.sum())

        if n_in_bin > 0:
            avg_prob = float(yp[mask].mean())
            true_freq = float(yt[mask].mean())
            bin_err = abs(avg_prob - true_freq)
            ece += (n_in_bin / len(yp)) * bin_err

            bins_data.append({
                "bin_idx": i,
                "bin_low": round(float(low), 3),
                "bin_high": round(float(high), 3),
                "count": n_in_bin,
                "predicted_prob_mean": round(avg_prob, 4),
                "empirical_freq": round(true_freq, 4),
                "calibration_gap": round(bin_err, 4),
            })
        else:
            bins_data.append({
                "bin_idx": i,
                "bin_low": round(float(low), 3),
                "bin_high": round(float(high), 3),
                "count": 0,
                "predicted_prob_mean": round(float(bin_centers[i]), 4),
                "empirical_freq": 0.0,
                "calibration_gap": 0.0,
            })

    return {
        "ece": round(float(ece), 6),
        "n_bins": n_bins,
        "bins_data": bins_data,
    }


class ProbabilityCalibrator:
    """Calibrador compuesto para modelos de riesgo territorial de ignición."""

    def __init__(self, method: str = "isotonic") -> None:
        self.method = method
        self.isotonic: Optional[IsotonicRegression] = None
        self.logistic: Optional[LogisticRegression] = None

    def fit(self, y_score: np.ndarray, y_true: np.ndarray) -> "ProbabilityCalibrator":
        scores = np.asarray(y_score, dtype=float)
        targets = np.asarray(y_true, dtype=int)

        if self.method == "isotonic":
            self.isotonic = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            self.isotonic.fit(scores, targets)
        elif self.method == "platt":
            self.logistic = LogisticRegression()
            self.logistic.fit(scores.reshape(-1, 1), targets)
        return self

    def predict_proba(self, y_score: np.ndarray) -> np.ndarray:
        scores = np.asarray(y_score, dtype=float)
        if self.method == "isotonic" and self.isotonic is not None:
            return np.clip(self.isotonic.predict(scores), 0.0, 1.0)
        elif self.method == "platt" and self.logistic is not None:
            return self.logistic.predict_proba(scores.reshape(-1, 1))[:, 1]
        return np.clip(scores, 0.0, 1.0)
