# Mirrors 03_Compression/Envelope/00, 01, 02, 03, 04 (orchestration) — same control flow as JSFX.

from __future__ import annotations

import math
from dataclasses import dataclass

from .constants import (
    CURVE_CALIBRATION_DB,
    CURVE_FAST_MULTIPLIER,
    CURVE_SLOW_MULTIPLIER,
    EPS,
    INPUT_DEPENDENT_DRAMA,
    LINEAR_RELEASE_FIXED_DB,
)
from .core_math import clamp, sign_jsfx


@dataclass
class EnvelopeParams:
    attack: float = 1000.0
    attack_curve: float = 0.0
    release_ms: float = 100.0
    release_curve: float = 0.0
    hold_ms: float = 0.0
    strength: float = 100.0
    prog_release_mode: float = 0.0
    prog_release_inverse: float = 0.0
    prog_release_blend: float = 0.0
    input_level_threshold_db: float = -20.0
    input_level_threshold_2_db: float = -40.0
    gr_blend_threshold_reduction_db: float = 6.0
    gr_blend_threshold_addition_db: float = 6.0
    rate_change_sensitivity_db: float = 3.0
    rate_change_threshold_modifier: float = 1.0


class EnvelopeEngine:
    def __init__(self) -> None:
        self.hold_counter_samples = 0
        self.hold_target_gr_db = 0.0
        self.hold_baseline_gr_db = 0.0
        self.global_smoothed_gain_db = 0.0
        self.global_smoothed_gain_db_before_strength = 0.0
        self.prev_detector_db = -20.0

        self.base_fast_s = 0.05
        self.base_med_s = 0.3
        self.base_slow_s = 1.0

        self.attack_coeff = 0.0
        self.release_coeff = 0.0
        self.release_time_ms = 0.0
        self.linear_release_db_per_sample = 0.0
        self.rel_fast_cached = 0.0
        self.rel_med_cached = 0.0
        self.rel_slow_cached = 0.0
        self.curve_fast_coeff_cached = 0.0
        self.curve_slow_coeff_cached = 0.0
        self.rel_input_fast_cached = 0.0

        self.hold_samples = 0
        self._p = EnvelopeParams()
        self._current_detector_level_db = -20.0

    @staticmethod
    def clamp_coeff(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def blend_two_coefficients(coef1: float, coef2: float, blend_factor: float) -> float:
        return coef1 * (1.0 - blend_factor) + coef2 * blend_factor

    def normalized_blend(self, blend_fast: float, blend_slow: float, coef_fast: float, coef_slow: float) -> float:
        s = blend_fast + blend_slow
        return (blend_fast * coef_fast + blend_slow * coef_slow) / s if s > EPS else coef_fast

    def apply_envelope_smoothing(self, coeff: float, target_value: float) -> float:
        valid_coeff = max(EPS, min(1.0 - EPS, coeff))
        self.global_smoothed_gain_db = valid_coeff * self.global_smoothed_gain_db + (1.0 - valid_coeff) * target_value
        return self.global_smoothed_gain_db

    def apply_envelope_smoothing_before_strength(self, coeff: float, target_value: float) -> float:
        valid_coeff = max(EPS, min(1.0 - EPS, coeff))
        self.global_smoothed_gain_db_before_strength = (
            valid_coeff * self.global_smoothed_gain_db_before_strength + (1.0 - valid_coeff) * target_value
        )
        return self.global_smoothed_gain_db_before_strength

    def apply_linear_envelope_smoothing(self, db_per_sample: float, target_value: float) -> float:
        err = target_value - self.global_smoothed_gain_db
        if abs(err) <= db_per_sample:
            self.global_smoothed_gain_db = target_value
        else:
            self.global_smoothed_gain_db = self.global_smoothed_gain_db + db_per_sample * sign_jsfx(err)
        return self.global_smoothed_gain_db

    def apply_linear_envelope_smoothing_before_strength(self, db_per_sample: float, target_value: float) -> float:
        err = target_value - self.global_smoothed_gain_db_before_strength
        if abs(err) <= db_per_sample:
            self.global_smoothed_gain_db_before_strength = target_value
        else:
            self.global_smoothed_gain_db_before_strength = (
                self.global_smoothed_gain_db_before_strength + db_per_sample * sign_jsfx(err)
            )
        return self.global_smoothed_gain_db_before_strength

    def update_hold_samples(self, hold_ms: float, srate: float) -> None:
        self.hold_samples = int(math.floor(hold_ms * 0.001 * srate))

    def update_attack_coefficient(self, attack: float, attack_curve: float, srate: float) -> None:
        attack_db_per_sec = attack
        attack_ms = 10000.0 / attack_db_per_sec
        attack_coeff_base = math.exp(-1000.0 / (attack_ms * srate))
        self.attack_coeff = attack_coeff_base
        if attack_curve != 0.0:
            if attack_curve > 0.0:
                curve_amount = attack_curve
                s_curve_factor = 1.0 + curve_amount * 0.45
                s_curve_factor *= 1.0 + curve_amount * 0.22
                self.attack_coeff = attack_coeff_base**s_curve_factor
            else:
                curve_amount = abs(attack_curve)
                self.attack_coeff = attack_coeff_base ** (1.0 - curve_amount * 0.45)

    def calculate_linear_release_rate(self, srate: float) -> None:
        db_per_second = LINEAR_RELEASE_FIXED_DB / (self.release_time_ms * 0.001)
        self.linear_release_db_per_sample = db_per_second / srate

    def update_release_coefficient(self, release_ms: float, srate: float) -> None:
        release_db_per_sec = release_ms
        self.release_time_ms = 10000.0 / release_db_per_sec
        self.calculate_linear_release_rate(srate)
        if self.release_time_ms > 0.0:
            self.release_coeff = math.exp(-1000.0 / (self.release_time_ms * srate))
        else:
            self.release_coeff = 1.0 - EPS

        rel_mult = 0.5 + (self.release_time_ms / 2000.0) * 1.5
        self.rel_fast_cached = math.exp(-1.0 / (self.base_fast_s * rel_mult * srate))
        self.rel_med_cached = math.exp(-1.0 / (self.base_med_s * rel_mult * srate))
        self.rel_slow_cached = math.exp(-1.0 / (self.base_slow_s * rel_mult * srate))

        if self.release_time_ms > 0.0:
            self.curve_fast_coeff_cached = math.exp(
                -1000.0 / ((self.release_time_ms / CURVE_FAST_MULTIPLIER) * srate)
            )
            self.curve_slow_coeff_cached = math.exp(
                -1000.0 / ((self.release_time_ms * CURVE_SLOW_MULTIPLIER) * srate)
            )
            self.rel_input_fast_cached = math.exp(
                -1000.0 / ((self.release_time_ms * (0.25 / INPUT_DEPENDENT_DRAMA)) * srate)
            )
        else:
            self.curve_fast_coeff_cached = 1.0 - EPS
            self.curve_slow_coeff_cached = 1.0 - EPS
            self.rel_input_fast_cached = 1.0 - EPS

    def release_gr_dependent(self, gr_amount: float) -> float:
        blend_fast = self.clamp_coeff(1.0 - gr_amount / self._p.gr_blend_threshold_reduction_db)
        blend_slow = self.clamp_coeff(gr_amount / self._p.gr_blend_threshold_reduction_db)
        return self.normalized_blend(blend_fast, blend_slow, self.rel_fast_cached, self.rel_slow_cached)

    def release_gr_dependent_dual(self, gr_amount: float, is_negative_gr: bool) -> float:
        threshold = (
            self._p.gr_blend_threshold_reduction_db if is_negative_gr else self._p.gr_blend_threshold_addition_db
        )
        blend_fast = self.clamp_coeff(1.0 - gr_amount / threshold)
        blend_slow = self.clamp_coeff(gr_amount / threshold)
        return self.normalized_blend(blend_fast, blend_slow, self.rel_fast_cached, self.rel_slow_cached)

    def release_rate_of_change(self, det_delta: float) -> float:
        effective_sensitivity = self._p.rate_change_sensitivity_db / (self._p.rate_change_threshold_modifier * 10.0)
        normalized_delta = det_delta / effective_sensitivity
        normalized_delta = max(0.0, min(2.0, normalized_delta))
        blend_fast = self.clamp_coeff(normalized_delta * 0.5)
        blend_slow = self.clamp_coeff(1.0 - blend_fast)
        return self.normalized_blend(blend_fast, blend_slow, self.rel_fast_cached, self.rel_slow_cached)

    def release_rate_of_change_inverse(self, det_delta: float) -> float:
        effective_sensitivity = self._p.rate_change_sensitivity_db / (self._p.rate_change_threshold_modifier * 10.0)
        normalized_delta = det_delta / effective_sensitivity
        normalized_delta = max(0.0, min(2.0, normalized_delta))
        blend_slow = self.clamp_coeff(normalized_delta * 0.5)
        blend_fast = self.clamp_coeff(1.0 - blend_slow)
        return self.normalized_blend(blend_fast, blend_slow, self.rel_fast_cached, self.rel_slow_cached)

    def release_gr_dependent_inverse_dual(self, gr_amount: float, is_negative_gr: bool) -> float:
        threshold = (
            self._p.gr_blend_threshold_reduction_db if is_negative_gr else self._p.gr_blend_threshold_addition_db
        )
        blend_slow = self.clamp_coeff(1.0 - gr_amount / threshold)
        blend_fast = self.clamp_coeff(gr_amount / threshold)
        return self.normalized_blend(blend_fast, blend_slow, self.rel_fast_cached, self.rel_slow_cached)

    def _input_dependent_u(self, input_level_db: float) -> float:
        knee_w = abs(self._p.input_level_threshold_db - self._p.input_level_threshold_2_db)
        knee_w = max(0.5, knee_w)
        level_above = input_level_db - self._p.input_level_threshold_db
        return self.clamp_coeff(INPUT_DEPENDENT_DRAMA * level_above / knee_w)

    def release_input_dependent_single(self, input_level_db: float) -> float:
        u = self._input_dependent_u(input_level_db)
        blend_fast = 1.0 - u
        blend_normal = u
        return self.normalized_blend(blend_fast, blend_normal, self.rel_input_fast_cached, self.release_coeff)

    def release_input_dependent_inverse(self, input_level_db: float) -> float:
        u = self._input_dependent_u(input_level_db)
        blend_fast = u
        blend_normal = 1.0 - u
        return self.normalized_blend(blend_fast, blend_normal, self.rel_input_fast_cached, self.release_coeff)

    def blend_curve_with_base(self, curve_shape_factor: float, base_coeff: float, release_curve_is_positive: bool) -> float:
        if release_curve_is_positive:
            blended = self.blend_two_coefficients(
                self.curve_fast_coeff_cached, self.curve_slow_coeff_cached, curve_shape_factor
            )
        else:
            blended = self.blend_two_coefficients(
                self.curve_slow_coeff_cached, self.curve_fast_coeff_cached, curve_shape_factor
            )
        return self.clamp_coeff(blended)

    def apply_curve_amount_blending(self, base_coeff: float, curve_shaped_coeff: float, curve_amount: float) -> float:
        curve_blend = self.clamp_coeff(curve_amount / 2.0)
        return self.blend_two_coefficients(base_coeff, curve_shaped_coeff, curve_blend)

    def calculate_curve_shaped_release_coeff(
        self, current_gr_db: float, target_gr_db: float, release_curve: float, base_coeff: float
    ) -> float:
        if abs(release_curve) < 0.001:
            return base_coeff if base_coeff > 0 else self.release_coeff
        base_to_use = base_coeff if base_coeff > 0 else self.release_coeff
        distance = abs(current_gr_db - target_gr_db)
        blend_factor = min(1.0, distance / CURVE_CALIBRATION_DB)
        curve_amount = abs(release_curve)
        blended_coeff = self.blend_curve_with_base(blend_factor, base_to_use, release_curve > 0)
        return self.apply_curve_amount_blending(base_to_use, blended_coeff, curve_amount)

    def calculate_gr_dependent_curve_release_coeff(
        self, current_gr_abs: float, release_curve: float, gr_threshold: float
    ) -> float:
        if abs(release_curve) < 0.001:
            return self.release_gr_dependent(current_gr_abs)
        distance_from_threshold = abs(current_gr_abs - gr_threshold)
        if gr_threshold > EPS:
            normalized_pos = min(2.0, distance_from_threshold / gr_threshold)
        else:
            normalized_pos = 0.0
        if release_curve > 0:
            curve_shape = self.clamp_coeff((normalized_pos * 0.5) * (normalized_pos * 0.5))
        else:
            curve_shape = self.clamp_coeff(1.0 - (normalized_pos * 0.5) * (normalized_pos * 0.5))
        blended_coeff = self.blend_curve_with_base(curve_shape, self.release_coeff, release_curve > 0)
        curve_amount = abs(release_curve)
        base_gr_release = self.release_gr_dependent(current_gr_abs)
        return self.apply_curve_amount_blending(base_gr_release, blended_coeff, curve_amount)

    def select_program_release_coef(
        self, target_gr_abs: float, detector_level_db: float, current_gr_abs: float, is_negative_gr: bool
    ) -> float:
        det_delta = self.prev_detector_db - detector_level_db
        input_level_db = detector_level_db
        mode = int(self._p.prog_release_mode + 0.5)
        is_inverse = self._p.prog_release_inverse > 0.5

        if mode == 0:
            return (
                self.release_input_dependent_inverse(input_level_db)
                if is_inverse
                else self.release_input_dependent_single(input_level_db)
            )
        if mode == 1:
            return (
                self.release_gr_dependent_inverse_dual(current_gr_abs, is_negative_gr)
                if is_inverse
                else self.release_gr_dependent_dual(current_gr_abs, is_negative_gr)
            )
        if mode == 2:
            return (
                self.release_rate_of_change_inverse(det_delta)
                if is_inverse
                else self.release_rate_of_change(det_delta)
            )
        return self.release_coeff

    def determine_attack_or_release(self, target_gr_abs: float, current_gr_abs: float) -> bool:
        hysteresis_threshold = max(0.2, current_gr_abs * 0.1)
        return target_gr_abs > (current_gr_abs + hysteresis_threshold)

    def calculate_release_coefficient(
        self,
        target_gr_abs: float,
        target_gr_db: float,
        detector_level_db: float,
        current_gr_abs: float,
        current_gr_abs_before_strength: float,
        is_negative_gr: bool,
        release_curve: float,
    ) -> float:
        blend_amount = self._p.prog_release_blend * 0.01
        if abs(release_curve) >= 0.001:
            fixed_rel_coef = self.calculate_curve_shaped_release_coeff(
                self.global_smoothed_gain_db, target_gr_db, release_curve, -1.0
            )
            if self._p.prog_release_mode >= 0.0:
                if int(self._p.prog_release_mode + 0.5) == 1:
                    prog_rel_coef = self.calculate_gr_dependent_curve_release_coeff(
                        current_gr_abs_before_strength,
                        release_curve,
                        self._p.gr_blend_threshold_reduction_db
                        if is_negative_gr
                        else self._p.gr_blend_threshold_addition_db,
                    )
                else:
                    base_rel_coef = self.select_program_release_coef(
                        target_gr_abs, detector_level_db, current_gr_abs, is_negative_gr
                    )
                    prog_rel_coef = self.calculate_curve_shaped_release_coeff(
                        self.global_smoothed_gain_db, target_gr_db, release_curve, base_rel_coef
                    )
                return fixed_rel_coef + (prog_rel_coef - fixed_rel_coef) * blend_amount
            return fixed_rel_coef

        fixed_rel_coef = self.release_coeff
        if self._p.prog_release_mode >= 0.0:
            prog_rel_coef = self.select_program_release_coef(
                target_gr_abs, detector_level_db, current_gr_abs, is_negative_gr
            )
            return fixed_rel_coef + (prog_rel_coef - fixed_rel_coef) * blend_amount
        return fixed_rel_coef

    def process_hold(self, target_gr_db: float, hold_ms: float) -> float:
        if hold_ms <= 0.0:
            self.hold_counter_samples = 0
            self.hold_target_gr_db = 0.0
            self.hold_baseline_gr_db = 0.0
            return target_gr_db

        target_gr_abs = abs(target_gr_db)
        hold_target_abs = abs(self.hold_target_gr_db)
        hold_baseline_abs = abs(self.hold_baseline_gr_db)

        if self.hold_counter_samples > 0:
            if target_gr_abs > hold_target_abs:
                self.hold_target_gr_db = target_gr_db
                hold_target_abs = target_gr_abs
                self.hold_counter_samples = self.hold_samples
            self.hold_counter_samples -= 1
            self.hold_counter_samples = max(0, self.hold_counter_samples)
            target_gr_db = self.hold_target_gr_db
            if self.hold_counter_samples <= 0:
                self.hold_baseline_gr_db = target_gr_db
        else:
            if target_gr_abs > hold_baseline_abs:
                self.hold_target_gr_db = target_gr_db
                self.hold_counter_samples = self.hold_samples
                target_gr_db = self.hold_target_gr_db
                self.hold_baseline_gr_db = self.hold_target_gr_db
            else:
                self.hold_baseline_gr_db = target_gr_db
                self.hold_target_gr_db = target_gr_db

        return target_gr_db

    def process_single_stage_envelope(self, target_gr_db: float, target_gr_db_before_strength: float) -> float:
        target_gr_abs = abs(target_gr_db)
        current_gr_abs = abs(self.global_smoothed_gain_db)
        current_gr_abs_before_strength = abs(self.global_smoothed_gain_db_before_strength)
        is_negative_gr = self.global_smoothed_gain_db < 0.0
        is_attack = self.determine_attack_or_release(target_gr_abs, current_gr_abs)

        if is_attack:
            self.apply_envelope_smoothing(self.attack_coeff, target_gr_db)
            self.apply_envelope_smoothing_before_strength(self.attack_coeff, target_gr_db_before_strength)
        else:
            blend_amount = self._p.prog_release_blend * 0.01
            use_linear_release = blend_amount <= 0.5

            rel_coef_use = self.calculate_release_coefficient(
                target_gr_abs,
                target_gr_db,
                self._current_detector_level_db,
                current_gr_abs,
                current_gr_abs_before_strength,
                is_negative_gr,
                self._p.release_curve,
            )
            if use_linear_release:
                c_ref = max(EPS, min(1.0 - EPS, self.release_coeff))
                c_use = max(EPS, min(1.0 - EPS, rel_coef_use))
                linear_speed_ratio = (1.0 - c_use) / (1.0 - c_ref)
                linear_speed_ratio = min(8.0, max(0.03125, linear_speed_ratio))
                linear_db_per_sample = self.linear_release_db_per_sample * linear_speed_ratio
                self.apply_linear_envelope_smoothing(linear_db_per_sample, target_gr_db)
                self.apply_linear_envelope_smoothing_before_strength(linear_db_per_sample, target_gr_db_before_strength)
            else:
                self.apply_envelope_smoothing(rel_coef_use, target_gr_db)
                self.apply_envelope_smoothing_before_strength(rel_coef_use, target_gr_db_before_strength)

        return self.global_smoothed_gain_db

    def process_envelope_following(
        self, target_gr_db: float, detector_level_db: float, strength_multiplier: float, hold_ms: float
    ) -> float:
        target_gr_db = self.process_hold(target_gr_db, hold_ms)
        if abs(strength_multiplier) > 0.0001:
            target_gr_db_before_strength = target_gr_db / strength_multiplier
        else:
            target_gr_db_before_strength = target_gr_db
        self._current_detector_level_db = detector_level_db
        return self.process_single_stage_envelope(target_gr_db, target_gr_db_before_strength)

    def sync_coefficients(self, p: EnvelopeParams, srate: float) -> None:
        self._p = p
        self.update_attack_coefficient(p.attack, p.attack_curve, srate)
        self.update_release_coefficient(p.release_ms, srate)
        self.update_hold_samples(p.hold_ms, srate)
