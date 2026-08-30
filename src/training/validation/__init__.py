"""
Módulo de métricas científicas, validación cruzada y backtesting.
"""
from src.training.validation.metrics import (
    compute_binary_metrics,
    compute_probabilistic_metrics,
    compute_territorial_concentration,
)

__all__ = [
    "compute_binary_metrics",
    "compute_probabilistic_metrics",
    "compute_territorial_concentration",
]
