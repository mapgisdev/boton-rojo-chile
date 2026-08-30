"""
Módulo de modelos de riesgo de incendios (M1 BR-CAL, M2 P-IGN, M3 P-GF).
"""
from src.training.models.br_calibrated import (
    compute_empirical_pi_matrix,
    evaluate_model_on_split,
    optimize_thresholds_on_validation,
    run_phase_4_recalibration,
)

__all__ = [
    "compute_empirical_pi_matrix",
    "evaluate_model_on_split",
    "optimize_thresholds_on_validation",
    "run_phase_4_recalibration",
]
