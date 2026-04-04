import math

import numpy as np

from composure_reference.chain import ComposureReferenceChain
from composure_reference.constants import COMP_LUT_GRANULARITY, COMP_LUT_MIN_DB, COMP_LUT_SIZE
from composure_reference.core_math import db_to_linear, linear_to_db, tanh_jsfx
from composure_reference.graph_lut import GraphAndLUT


def test_db_roundtrip():
    for db in (-60.0, -20.0, 0.0, 6.0, 12.0):
        lin = db_to_linear(db)
        back = linear_to_db(lin)
        assert abs(back - db) < 1e-9


def test_tanh_jsfx_extremes():
    assert tanh_jsfx(20.0) == 1.0
    assert tanh_jsfx(-20.0) == -1.0


def test_default_graph_lut_is_unity_line():
    g = GraphAndLUT()
    g.build_compression_lut()
    # Perfect y=x interior → LUT matches input (within interpolation); threshold stays 1000 like JSFX
    assert g.comp_curve_min_threshold_db >= 500.0
    for i in range(COMP_LUT_SIZE):
        inp = COMP_LUT_MIN_DB + i * COMP_LUT_GRANULARITY
        out = g.lookup_compression_lut(inp)
        if -19.0 < inp < -0.5:
            assert abs(out - inp) < 0.2


def test_compressor_reduces_loud_input():
    chain = ComposureReferenceChain(srate=48000.0)
    # Bend default diagonal so GR is non-zero (unity curve leaves threshold at +1000 dB in JSFX).
    # Pull down y at the first interior knot (input ≈ -16 dB) so ~-14 dBFS material is compressed.
    chain.graph.graph_points[3] -= 14.0
    chain.graph.update_corner_points()
    chain.graph.invalidate()
    chain.graph.build_compression_lut()
    chain.set_params(strength=400.0, attack=50000.0, release_ms=50.0)
    chain.reset_audio_state()
    n = 48000
    x = np.zeros(n)
    # ~-14 dBFS — lands in the bent region of the default 6-point curve
    x[n // 4 : 3 * n // 4] = 0.2
    y, tr = chain.process_block(x, record=True)
    assert tr is not None
    mid = tr["target_gr_db"][2 * n // 3]
    assert mid < -0.05, "expected non-zero target GR with bent curve"
    rms_in = float(np.sqrt(np.mean(x[2 * n // 3 - 2000 : 2 * n // 3] ** 2)))
    rms_out = float(np.sqrt(np.mean(y[2 * n // 3 - 2000 : 2 * n // 3] ** 2)))
    assert rms_out < rms_in * 0.98


def test_trace_shapes():
    chain = ComposureReferenceChain(srate=8000.0)
    x = (0.1 * np.sin(np.linspace(0, 40 * math.pi, 4000))).astype(np.float64)
    y, tr = chain.process_block(x, record=True)
    assert y.shape == x.shape
    assert tr is not None
    assert len(tr["in"]) == len(x)
    assert len(tr["smoothed_gr_db"]) == len(x)
