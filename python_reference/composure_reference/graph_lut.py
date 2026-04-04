# Mirrors 03_Compression/03_graph_curves.jsfx-inc, 05_compression_core.jsfx-inc (LUT),
# and calculate_compression_threshold from 02_graph_data_core.jsfx-inc

from __future__ import annotations

import math
from typing import List, Sequence, Tuple, Union

import numpy as np

from .constants import (
    BEZIER_STEPS,
    COMP_LUT_GRANULARITY,
    COMP_LUT_MAX_DB,
    COMP_LUT_MAX_REDUCTION_DB,
    COMP_LUT_MIN_DB,
    COMP_LUT_SIZE,
    GRAPH_MAX_DB,
    GRAPH_MIN_DB,
    GRAPH_RANGE_DB,
    MAX_CURVE_SEGMENTS,
    MAX_POINTS,
)
from .core_math import clamp, db_to_linear


def apply_extrapolation_caps(input_db: float, output_db: float) -> float:
    if input_db < GRAPH_MIN_DB or input_db > GRAPH_MAX_DB:
        upper_cap_db = input_db
        lower_cap_db = input_db - GRAPH_RANGE_DB
        return max(lower_cap_db, min(output_db, upper_cap_db))
    return output_db


class GraphAndLUT:
    """
    Holds graph_points (flat x0,y0,x1,y1,...), curve_amounts, segment cache, and compression LUT.
    """

    def __init__(self) -> None:
        self.num_points = 6
        self.graph_points: List[float] = [0.0] * (MAX_POINTS * 2)
        self.curve_amounts: List[float] = [0.0] * MAX_POINTS
        self.comp_curve_min_threshold_db = GRAPH_MAX_DB + 10.0
        self.comp_lut_dirty = True
        self.comp_curve_threshold_dirty = True
        self.curve_segments_db_dirty = True
        self.segments: List[Tuple[float, float, float, float]] = []
        self.comp_lut = np.zeros(COMP_LUT_SIZE, dtype=np.float64)
        self._init_default_graph()

    def _init_default_graph(self) -> None:
        # init_graph_points() from 02_graph_data_core.jsfx-inc
        gmax, gmin, gr = GRAPH_MAX_DB, GRAPH_MIN_DB, GRAPH_RANGE_DB
        self.graph_points[0] = gmin
        self.graph_points[1] = gmin
        self.graph_points[10] = gmax
        self.graph_points[11] = gmax
        self.graph_points[2] = gmin + gr * 0.2
        self.graph_points[3] = self.graph_points[2]
        self.graph_points[4] = gmin + gr * 0.4
        self.graph_points[5] = self.graph_points[4]
        self.graph_points[6] = gmin + gr * 0.6
        self.graph_points[7] = self.graph_points[6]
        self.graph_points[8] = gmin + gr * 0.8
        self.graph_points[9] = self.graph_points[8]
        self.update_corner_points()
        self.invalidate()

    def get_point_x(self, point_idx: int) -> float:
        return self.graph_points[point_idx * 2]

    def get_point_y(self, point_idx: int) -> float:
        return self.graph_points[point_idx * 2 + 1]

    def get_curve_amount(self, point_index: int) -> float:
        if 0 <= point_index < MAX_POINTS:
            return self.curve_amounts[point_index]
        return 0.0

    def is_valid_curve_point(self, point_idx: int) -> bool:
        return point_idx > 0 and point_idx < (self.num_points - 1)

    def update_corner_points(self) -> None:
        # update_corner_points() — same structure as JSFX
        if self.num_points >= 3:
            p1_x = self.graph_points[2]
            p1_y = self.graph_points[3]
            p2_x = self.graph_points[4]
            p2_y = self.graph_points[5]
            dx = p2_x - p1_x
            if abs(dx) > 0.001:
                slope = (p2_y - p1_y) / dx
                if p1_y > p2_y:
                    self.graph_points[0] = GRAPH_MIN_DB
                    self.graph_points[1] = GRAPH_MIN_DB
                else:
                    self.graph_points[1] = GRAPH_MIN_DB
                    self.graph_points[0] = p1_x + (GRAPH_MIN_DB - p1_y) / slope
                    if self.graph_points[0] < GRAPH_MIN_DB:
                        self.graph_points[0] = GRAPH_MIN_DB
                        self.graph_points[1] = p1_y + slope * (GRAPH_MIN_DB - p1_x)
                        if self.graph_points[1] > GRAPH_MIN_DB:
                            self.graph_points[1] = GRAPH_MIN_DB
                    elif self.graph_points[0] > GRAPH_MIN_DB:
                        self.graph_points[0] = GRAPH_MIN_DB
                        self.graph_points[1] = p1_y + slope * (GRAPH_MIN_DB - p1_x)
                        if self.graph_points[1] > GRAPH_MIN_DB:
                            self.graph_points[1] = GRAPH_MIN_DB
            else:
                self.graph_points[0] = GRAPH_MIN_DB
                self.graph_points[1] = GRAPH_MIN_DB
        else:
            self.graph_points[0] = GRAPH_MIN_DB
            self.graph_points[1] = GRAPH_MIN_DB

        last_idx = self.num_points - 1
        if self.num_points >= 3:
            p1_x = self.graph_points[(last_idx - 2) * 2]
            p1_y = self.graph_points[(last_idx - 2) * 2 + 1]
            p2_x = self.graph_points[(last_idx - 1) * 2]
            p2_y = self.graph_points[(last_idx - 1) * 2 + 1]
            dx = p2_x - p1_x
            if abs(dx) > 0.001:
                slope = (p2_y - p1_y) / dx
                self.graph_points[last_idx * 2] = GRAPH_MAX_DB
                calculated_y = p2_y + slope * (GRAPH_MAX_DB - p2_x)
                self.graph_points[last_idx * 2 + 1] = min(calculated_y, GRAPH_MAX_DB)
            else:
                self.graph_points[last_idx * 2] = GRAPH_MAX_DB
                self.graph_points[last_idx * 2 + 1] = min(p2_y, GRAPH_MAX_DB)
        else:
            self.graph_points[last_idx * 2] = GRAPH_MAX_DB
            self.graph_points[last_idx * 2 + 1] = GRAPH_MAX_DB

    def invalidate(self) -> None:
        self.curve_segments_db_dirty = True
        self.comp_lut_dirty = True
        self.comp_curve_threshold_dirty = True

    def set_interior_points_normalized(
        self, knots: Sequence[Union[Tuple[float, float], List[float]]]
    ) -> None:
        """
        Replace interior knots only; corners are derived via update_corner_points().
        Each knot is (norm_x, norm_y) in 0..1 mapped to dB as:
          dB = GRAPH_MIN_DB + norm * GRAPH_RANGE_DB
        """
        n_interior = len(knots)
        self.num_points = n_interior + 2
        for i in range(MAX_POINTS):
            self.curve_amounts[i] = 0.0
        for i, xy in enumerate(knots):
            nx, ny = float(xy[0]), float(xy[1])
            idx = i + 1
            self.graph_points[idx * 2] = GRAPH_MIN_DB + nx * GRAPH_RANGE_DB
            self.graph_points[idx * 2 + 1] = GRAPH_MIN_DB + ny * GRAPH_RANGE_DB
        self.update_corner_points()
        self.invalidate()

    def _calculate_bezier_control_points(
        self, point_index: int, curve_amount: float
    ) -> Tuple[float, float, float, float, float, float, float, float]:
        prev_x = self.get_point_x(point_index - 1)
        prev_y = self.get_point_y(point_index - 1)
        curr_x = self.get_point_x(point_index)
        curr_y = self.get_point_y(point_index)
        next_x = self.get_point_x(point_index + 1)
        next_y = self.get_point_y(point_index + 1)
        curve_factor = curve_amount / 100.0
        invisible1_x = curr_x + (prev_x - curr_x) * curve_factor
        invisible1_y = curr_y + (prev_y - curr_y) * curve_factor
        invisible2_x = curr_x + (next_x - curr_x) * curve_factor
        invisible2_y = curr_y + (next_y - curr_y) * curve_factor
        return (
            invisible1_x,
            invisible1_y,
            curr_x,
            curr_y,
            curr_x,
            curr_y,
            invisible2_x,
            invisible2_y,
        )

    @staticmethod
    def _evaluate_bezier_at_t(
        t: float,
        p0_x: float,
        p0_y: float,
        p1_x: float,
        p1_y: float,
        p2_x: float,
        p2_y: float,
        p3_x: float,
        p3_y: float,
    ) -> Tuple[float, float]:
        u = 1.0 - t
        uuu = u * u * u
        uu = u * u
        tt = t * t
        ttt = tt * t
        rx = uuu * p0_x + 3 * uu * t * p1_x + 3 * u * tt * p2_x + ttt * p3_x
        ry = uuu * p0_y + 3 * uu * t * p1_y + 3 * u * tt * p2_y + ttt * p3_y
        return rx, ry

    def generate_curve_segments_db(self) -> None:
        segs: List[Tuple[float, float, float, float]] = []
        if self.num_points < 2:
            self.segments = segs
            self.curve_segments_db_dirty = False
            return

        prev_x_db = self.get_point_x(0)
        prev_y_db = self.get_point_y(0)
        clamped_junction_x_db = 0.0
        clamped_junction_y_db = 0.0
        use_clamped_junction = False
        t_step = 1.0 / BEZIER_STEPS

        i = 0
        while i < self.num_points - 1:
            next_idx = i + 1
            next_point_has_curve = self.is_valid_curve_point(next_idx) and self.get_curve_amount(next_idx) > 0

            if next_point_has_curve:
                curve_amt = self.get_curve_amount(next_idx)
                p0_x_db, p0_y_db, p1_x_db, p1_y_db, p2_x_db, p2_y_db, p3_x_db, p3_y_db = (
                    self._calculate_bezier_control_points(next_idx, curve_amt)
                )
                if use_clamped_junction:
                    p0_x_db = clamped_junction_x_db
                    p0_y_db = clamped_junction_y_db
                    use_clamped_junction = False

                next_next_idx = i + 2
                next_next_point_has_curve = self.is_valid_curve_point(next_next_idx) and self.get_curve_amount(next_next_idx) > 0
                if next_next_point_has_curve:
                    next_curve_amount = self.get_curve_amount(next_next_idx)
                    n0_x, n0_y, _, _, _, _, _, _ = self._calculate_bezier_control_points(next_next_idx, next_curve_amount)
                    if p3_x_db > n0_x:
                        junction_x_db = (p3_x_db + n0_x) / 2.0
                        junction_y_db = (p3_y_db + n0_y) / 2.0
                        p3_x_db = junction_x_db
                        p3_y_db = junction_y_db
                        clamped_junction_x_db = junction_x_db
                        clamped_junction_y_db = junction_y_db
                        use_clamped_junction = True

                t = 0.0
                while t < 1.0 and len(segs) < MAX_CURVE_SEGMENTS - 1:
                    current_x_db, current_y_db = self._evaluate_bezier_at_t(
                        t, p0_x_db, p0_y_db, p1_x_db, p1_y_db, p2_x_db, p2_y_db, p3_x_db, p3_y_db
                    )
                    segs.append((prev_x_db, prev_y_db, current_x_db, current_y_db))
                    prev_x_db = current_x_db
                    prev_y_db = current_y_db
                    t += t_step
            else:
                end_x_db = self.get_point_x(next_idx)
                end_y_db = self.get_point_y(next_idx)
                segs.append((prev_x_db, prev_y_db, end_x_db, end_y_db))
                prev_x_db = end_x_db
                prev_y_db = end_y_db

            i += 1

        self.segments = segs
        self.curve_segments_db_dirty = False

    def sample_curve_at_db_internal(self, input_db: float) -> float:
        if self.curve_segments_db_dirty:
            self.generate_curve_segments_db()
        if len(self.segments) == 0:
            return input_db

        first_x, first_y, seg_x2_db, seg_y2_db = (
            self.segments[0][0],
            self.segments[0][1],
            self.segments[0][2],
            self.segments[0][3],
        )
        if input_db <= first_x:
            seg_width = seg_x2_db - first_x
            if abs(seg_width) > 0.0001:
                slope = (seg_y2_db - first_y) / seg_width
                return first_y + slope * (input_db - first_x)
            return first_y

        last_idx = len(self.segments) - 1
        last_x = self.segments[last_idx][2]
        if input_db >= last_x:
            last_seg_x1_db = self.segments[last_idx][0]
            last_seg_y1_db = self.segments[last_idx][1]
            last_seg_x2_db = self.segments[last_idx][2]
            last_seg_y2_db = self.segments[last_idx][3]
            last_seg_width = last_seg_x2_db - last_seg_x1_db
            if abs(last_seg_width) > 0.0001:
                last_slope = (last_seg_y2_db - last_seg_y1_db) / last_seg_width
                return last_seg_y2_db + last_slope * (input_db - last_seg_x2_db)
            return last_seg_y2_db

        for seg_x1_db, seg_y1_db, seg_x2_db, seg_y2_db in self.segments:
            if (input_db >= seg_x1_db - 0.0001 and input_db <= seg_x2_db + 0.0001) or (
                input_db >= seg_x2_db - 0.0001 and input_db <= seg_x1_db + 0.0001
            ):
                seg_width = seg_x2_db - seg_x1_db
                if abs(seg_width) > 0.0001:
                    t = max(0.0, min(1.0, (input_db - seg_x1_db) / seg_width))
                    return seg_y1_db + t * (seg_y2_db - seg_y1_db)
                return seg_y1_db

        return input_db

    def sample_curve_at_db(self, input_db: float) -> float:
        output_db = self.sample_curve_at_db_internal(input_db)
        return apply_extrapolation_caps(input_db, output_db)

    def build_compression_lut(self) -> None:
        if self.curve_segments_db_dirty:
            self.generate_curve_segments_db()
        for i in range(COMP_LUT_SIZE):
            input_db = COMP_LUT_MIN_DB + (i * COMP_LUT_GRANULARITY)
            sampled = self.sample_curve_at_db(input_db)
            self.comp_lut[i] = max(sampled, input_db - COMP_LUT_MAX_REDUCTION_DB)
        self._calculate_compression_threshold()
        self.comp_lut_dirty = False
        self.comp_curve_threshold_dirty = False

    def _calculate_compression_threshold(self) -> None:
        self.comp_curve_min_threshold_db = 1000.0
        for i in range(COMP_LUT_SIZE):
            lut_in = COMP_LUT_MIN_DB + (i * COMP_LUT_GRANULARITY)
            lut_out = float(self.comp_lut[i])
            if abs(lut_out - lut_in) > 0.08:
                self.comp_curve_min_threshold_db = lut_in
                break
        self.comp_curve_threshold_dirty = False

    def lookup_compression_lut(self, input_db: float) -> float:
        if self.comp_lut_dirty:
            self.build_compression_lut()

        if input_db < COMP_LUT_MIN_DB:
            output_db = float(self.comp_lut[0])
        elif input_db > COMP_LUT_MAX_DB:
            output_db = float(self.comp_lut[COMP_LUT_SIZE - 1])
        else:
            index_float = (input_db - COMP_LUT_MIN_DB) / COMP_LUT_GRANULARITY
            index_int = int(max(0, min(COMP_LUT_SIZE - 2, math.floor(index_float))))
            index_frac = index_float - index_int
            value1 = float(self.comp_lut[index_int])
            value2 = float(self.comp_lut[index_int + 1])
            output_db = value1 + index_frac * (value2 - value1)

        return max(apply_extrapolation_caps(input_db, output_db), input_db - COMP_LUT_MAX_REDUCTION_DB)
