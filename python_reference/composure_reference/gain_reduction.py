# Mirrors 03_Compression/06_gain_reduction.jsfx-inc

from typing import Tuple

from .constants import MAX_CURVE_INPUT_DB, MAX_GR_DB, MIN_DETECTOR_DB_FLOOR
from .core_math import clamp
from .graph_lut import GraphAndLUT


def calculate_gain_reduction_from_db(
    graph: GraphAndLUT,
    detector_level_db: float,
    input_offset_db: float,
    strength_multiplier: float,
) -> Tuple[float, float, int]:
    """
    Returns (target_gr_db, target_gr_db_before_strength, gr_processing_skipped 0|1)
    """
    curve_input_db = clamp(detector_level_db + input_offset_db, MIN_DETECTOR_DB_FLOOR, MAX_CURVE_INPUT_DB)

    if curve_input_db < graph.comp_curve_min_threshold_db:
        return 0.0, 0.0, 1

    target_output_db = graph.lookup_compression_lut(curve_input_db)
    target_gr_db_before_strength = target_output_db - curve_input_db
    target_gr_db = target_gr_db_before_strength * strength_multiplier
    target_gr_db = max(-MAX_GR_DB, min(MAX_GR_DB, target_gr_db))
    return target_gr_db, target_gr_db_before_strength, 0
