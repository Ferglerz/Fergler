# Mirrors ../MathUtils/00_core_math.jsfx-inc

import math

from .constants import EPS

LOG10_20 = 20.0 / math.log(10.0)
LOG_10_20 = math.log(10.0) / 20.0


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))


def tanh_jsfx(x: float) -> float:
    if x > 10.0:
        return 1.0
    if x < -10.0:
        return -1.0
    e2x = math.exp(2.0 * x)
    return (e2x - 1.0) / (e2x + 1.0)


def db_to_linear(db: float) -> float:
    return math.exp(db * LOG_10_20)


def linear_to_db(linear: float) -> float:
    return math.log(linear) * LOG10_20 if linear > 0 else -150.0


def sign_jsfx(x: float) -> float:
    if x > 0:
        return 1.0
    if x < 0:
        return -1.0
    return 0.0
