# Mirrors the non-UI audio path in 03_Compression/09_audio_processing_chain.jsfx-inc,
# 02_InputProcessing/01_dsp_utils.jsfx-inc (limiter), and Composure.jsfx slider scaling.
# Omitted for this reference build: HP/LP filters, lookahead buffer, sidechain, mid/side, harmonics.

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .constants import (
    LIMITER_SCALE,
    MAX_DETECTOR_DB,
    MAX_DETECTOR_LINEAR,
    MAX_GR_DB,
    MIN_DETECTOR_LEVEL,
    MIN_DETECTOR_DB_FLOOR,
)
from .core_math import clamp, db_to_linear, linear_to_db, tanh_jsfx
from .envelope import EnvelopeEngine, EnvelopeParams
from .gain_reduction import calculate_gain_reduction_from_db
from .graph_lut import GraphAndLUT


@dataclass
class ComposureParams:
    """Subset of Composure sliders used by this reference chain."""

    attack: float = 1000.0
    attack_curve: float = 0.0
    release_ms: float = 100.0
    release_curve: float = 0.0
    hold_ms: float = 0.0
    strength: float = 100.0
    rms_size_ms: float = 0.0
    rms_normalization: float = 0.0
    detection_mode: float = 1.0
    lookahead_ms: float = 0.0
    input_offset_db: float = 0.0
    makeup_gain_db: float = 0.0
    brickwall_limiter: float = 1.0
    prog_release_mode: float = 0.0
    prog_release_inverse: float = 0.0
    prog_release_blend: float = 0.0
    input_level_threshold_db: float = -20.0
    gr_blend_threshold_reduction_db: float = 6.0
    gr_blend_threshold_addition_db: float = 6.0
    rate_change_sensitivity_db: float = 3.0
    rate_change_threshold_modifier: float = 1.0

    def envelope_params(self) -> EnvelopeParams:
        return EnvelopeParams(
            attack=self.attack,
            attack_curve=self.attack_curve,
            release_ms=self.release_ms,
            release_curve=self.release_curve,
            hold_ms=self.hold_ms,
            strength=self.strength,
            prog_release_mode=self.prog_release_mode,
            prog_release_inverse=self.prog_release_inverse,
            prog_release_blend=self.prog_release_blend,
            input_level_threshold_db=self.input_level_threshold_db,
            gr_blend_threshold_addition_db=self.gr_blend_threshold_addition_db,
            gr_blend_threshold_reduction_db=self.gr_blend_threshold_reduction_db,
            rate_change_sensitivity_db=self.rate_change_sensitivity_db,
            rate_change_threshold_modifier=self.rate_change_threshold_modifier,
        )


class ComposureReferenceChain:
    """
    Mono-in/mono-out reference processor (detector = |x| with optional RMS).
    """

    def __init__(self, srate: float = 44100.0) -> None:
        self.srate = srate
        self.graph = GraphAndLUT()
        self.env = EnvelopeEngine()
        self.params = ComposureParams()
        self.makeup_gain_linear = 1.0
        self.strength_multiplier = 1.0

        self.rms_max = 0.5
        self.peak_for_normalize_smooth = 0.0
        self.rms_smoothed_squared = 0.0
        self.rms_smoothing_coeff = 0.0
        self.rms_smoothing_one_minus = 1.0

        self.limiter_prev = 0.0
        self.limiter_tanh_norm = 1.0 / tanh_jsfx(0.95)

        self.final_prev = 0.0

        self._recording = False
        self._trace: Optional[Dict[str, List[float]]] = None

        self._update_derived_params()
        self.env.sync_coefficients(self.params.envelope_params(), self.srate)

    def _update_derived_params(self) -> None:
        self.strength_multiplier = self.params.strength / 100.0
        self.makeup_gain_linear = db_to_linear(self.params.makeup_gain_db)
        self._update_rms_targets()

    def _update_rms_targets(self) -> None:
        if self.params.rms_size_ms > 0.0:
            self.rms_smoothing_coeff = math.exp(-1000.0 / (self.params.rms_size_ms * self.srate))
            self.rms_smoothing_one_minus = 1.0 - self.rms_smoothing_coeff
        else:
            self.rms_smoothing_coeff = 0.0
            self.rms_smoothing_one_minus = 1.0

    def set_params(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            if hasattr(self.params, k):
                setattr(self.params, k, float(v))
        self._update_derived_params()
        self.env.sync_coefficients(self.params.envelope_params(), self.srate)

    def reset_audio_state(self) -> None:
        self.env.global_smoothed_gain_db = 0.0
        self.env.global_smoothed_gain_db_before_strength = 0.0
        self.env.hold_counter_samples = 0
        self.env.prev_detector_db = -20.0
        self.rms_max = 0.5
        self.peak_for_normalize_smooth = 0.0
        self.rms_smoothed_squared = 0.0
        self.limiter_prev = 0.0
        self.final_prev = 0.0

    def soft_clip_limiter(self, inp: float, prev_sample: float) -> float:
        abs_input = abs(inp)
        abs_prev = abs(prev_sample)
        if abs_input > 0.944 or abs_prev > 0.944:
            oversample1 = abs((inp + prev_sample) * 0.5)
            peak_detected = max(oversample1, abs_input) > 0.95
            if peak_detected:
                return tanh_jsfx(inp * LIMITER_SCALE) * self.limiter_tanh_norm
        return inp

    def process_sample(self, spl_in: float) -> float:
        p = self.params

        detect = spl_in
        if p.detection_mode < 0.5:
            detect = self.final_prev

        detect_squared = detect * detect
        if p.rms_size_ms > 0.0:
            self.rms_smoothed_squared = (
                self.rms_smoothed_squared * self.rms_smoothing_coeff
                + detect_squared * self.rms_smoothing_one_minus
            )
            rms_level = math.sqrt(self.rms_smoothed_squared)
        else:
            rms_level = abs(detect)

        if p.rms_normalization > 0.5:
            self.rms_max = rms_level if rms_level > self.rms_max else (self.rms_max * 0.9999)
            normalized_rms = rms_level / (self.rms_max + 1e-30)
            peak_level = abs(detect)
            norm_peak_c = self.rms_smoothing_coeff if p.rms_size_ms > 0 else math.exp(-1.0 / (0.02 * self.srate))
            norm_peak_1m = 1.0 - norm_peak_c
            self.peak_for_normalize_smooth = (
                self.peak_for_normalize_smooth * norm_peak_c + peak_level * norm_peak_1m
            )
            detector_level = normalized_rms * self.peak_for_normalize_smooth
        else:
            detector_level = rms_level if p.rms_size_ms > 0 else abs(detect)

        detector_level = min(detector_level, MAX_DETECTOR_LINEAR)
        detector_level_db = clamp(
            linear_to_db(max(detector_level, MIN_DETECTOR_LEVEL)),
            MIN_DETECTOR_DB_FLOOR,
            MAX_DETECTOR_DB,
        )

        target_gr_db, _, _ = calculate_gain_reduction_from_db(
            self.graph,
            detector_level_db,
            p.input_offset_db,
            self.strength_multiplier,
        )

        if self._recording and self._trace is not None:
            self._trace["in"].append(float(spl_in))
            self._trace["detector_db"].append(float(detector_level_db))
            self._trace["target_gr_db"].append(float(target_gr_db))

        can_skip_envelope = abs(target_gr_db) < 0.01 and abs(self.env.global_smoothed_gain_db) < 0.01
        if can_skip_envelope:
            self.env.global_smoothed_gain_db = 0.0
            self.env.global_smoothed_gain_db_before_strength = 0.0
        else:
            self.env.process_envelope_following(
                target_gr_db,
                detector_level_db,
                self.strength_multiplier,
                p.hold_ms,
            )

        self.env.prev_detector_db = detector_level_db

        current_gr_db = max(-MAX_GR_DB, min(MAX_GR_DB, self.env.global_smoothed_gain_db))

        if abs(current_gr_db) < 1e-6:
            processed = spl_in
        else:
            gr_lin = db_to_linear(current_gr_db)
            processed = spl_in * gr_lin

        final_sample = processed * self.makeup_gain_linear

        if p.brickwall_limiter > 0.5:
            abs_f = abs(final_sample)
            if abs_f > 0.944:
                final_sample = self.soft_clip_limiter(final_sample, self.limiter_prev)
            self.limiter_prev = final_sample

        self.final_prev = final_sample

        if self._recording and self._trace is not None:
            self._trace["out"].append(float(final_sample))
            self._trace["smoothed_gr_db"].append(float(self.env.global_smoothed_gain_db))

        return final_sample

    def process_block(
        self, samples: np.ndarray, record: bool = False
    ) -> Tuple[np.ndarray, Optional[Dict[str, np.ndarray]]]:
        out = np.empty_like(samples, dtype=np.float64)
        if record:
            self._recording = True
            self._trace = {
                "in": [],
                "out": [],
                "detector_db": [],
                "target_gr_db": [],
                "smoothed_gr_db": [],
            }
        else:
            self._recording = False
            self._trace = None

        for i, x in enumerate(samples.flat):
            out.flat[i] = self.process_sample(float(x))

        self._recording = False
        if not record or self._trace is None:
            return out, None
        arrays = {k: np.array(v, dtype=np.float64) for k, v in self._trace.items()}
        self._trace = None
        return out, arrays
