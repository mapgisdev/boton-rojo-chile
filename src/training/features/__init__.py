"""
Módulo de extracción y ensamblaje de covariables (meteorológicas, topográficas, combustible).
"""
from src.training.features.builder import build_master_fire_h3_dataset, calculate_vpd, enrich_features

__all__ = ["build_master_fire_h3_dataset", "calculate_vpd", "enrich_features"]
