#!/usr/bin/env python3
"""
Explore a 3-knot graph (normalized 0..1 on X and Y) and behavior around -10 dBFS.

Run from repo:
  cd python_reference && . .venv/bin/activate  # optional
  PYTHONPATH=. python3 scripts/explore_cut_boost_crossing.py

Optional plot:
  PYTHONPATH=. python3 scripts/explore_cut_boost_crossing.py --plot cut_boost.png

Sine + level sweep (RMS detection so zeros do not slam the log):
  PYTHONPATH=. python3 scripts/explore_cut_boost_crossing.py --signal tone --rms-ms 25 --freq 220
"""

from __future__ import annotations

import argparse
import math
import os
import sys

# Allow running as script without installing package
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np

from composure_reference.chain import ComposureReferenceChain
from composure_reference.constants import GRAPH_MAX_DB, GRAPH_MIN_DB, GRAPH_RANGE_DB
from composure_reference.core_math import LOG_10_20
from composure_reference.gain_reduction import calculate_gain_reduction_from_db
from composure_reference.graph_lut import GraphAndLUT


def norm_to_db(nx: float, ny: float) -> tuple[float, float]:
    x_db = GRAPH_MIN_DB + nx * GRAPH_RANGE_DB
    y_db = GRAPH_MIN_DB + ny * GRAPH_RANGE_DB
    return x_db, y_db


def index_detector_near(
    det: np.ndarray, target_db: float, lo: int, hi: int
) -> int:
    """Sample index in [lo, hi) whose detector dB is closest to target_db."""
    lo = max(0, min(lo, len(det) - 1))
    hi = max(lo + 1, min(hi, len(det)))
    sl = slice(lo, hi)
    rel = int(np.argmin(np.abs(det[sl] - target_db)))
    return lo + rel


def find_11_crossings(graph: GraphAndLUT, dbs: np.ndarray) -> list[float]:
    """Input dB where piecewise-linear curve (from segments) crosses y=x (GR sign change)."""
    outs = np.array([graph.sample_curve_at_db(float(x)) for x in dbs])
    diff = outs - dbs
    crossings: list[float] = []
    for i in range(len(dbs) - 1):
        if diff[i] == 0:
            crossings.append(float(dbs[i]))
            continue
        if diff[i] * diff[i + 1] < 0:
            t = abs(diff[i]) / (abs(diff[i]) + abs(diff[i + 1]))
            crossings.append(float(dbs[i] + t * (dbs[i + 1] - dbs[i])))
    return crossings


def build_dynamic_signal(
    signal: str,
    srate: float,
    dur: float,
    freq_hz: float,
    rms_ms: float,
) -> tuple[np.ndarray, np.ndarray, str]:
    """
    Returns (x, db_sweep_target, description).
    db_sweep_target is the nominal peak dBFS of the amplitude envelope (for labels / comparison).
    """
    n = int(srate * dur)
    t = np.arange(n, dtype=np.float64) / srate
    db_sweep = -14.0 + 6.0 * (t / dur)
    amp = np.maximum(1e-8, np.exp(db_sweep * LOG_10_20))

    if signal == "dc":
        return amp, db_sweep, "DC level (peak detection, rms_size_ms=0)"

    if signal == "tone":
        ph = 2.0 * math.pi * freq_hz * t
        x = amp * np.sin(ph)
        return x, db_sweep, (
            f"sine {freq_hz:.0f} Hz × swept envelope, RMS ~{rms_ms:.0f} ms "
            "(detector follows level, not zero-crossings)"
        )

    raise SystemExit(f"Unknown --signal {signal!r} (use dc or tone)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot", default="", help="Save PNG path")
    ap.add_argument(
        "--signal",
        choices=("dc", "tone"),
        default="dc",
        help="dc: steady level sweep; tone: sine × same envelope (use RMS)",
    )
    ap.add_argument(
        "--rms-ms",
        type=float,
        default=25.0,
        help="RMS window for --signal tone (0 falls back to peak; not recommended for tone)",
    )
    ap.add_argument("--freq", type=float, default=220.0, help="Sine frequency for --signal tone")
    args = ap.parse_args()

    # User scenario: normalized graph coordinates
    knots_norm = [(0.25, 0.0), (0.4, 0.6), (0.75, 1.0)]
    print("Graph range: {:.0f} dB ({} dB .. {} dB)".format(GRAPH_RANGE_DB, GRAPH_MIN_DB, GRAPH_MAX_DB))
    print("Interior knots (normalized -> dB):")
    for i, (nx, ny) in enumerate(knots_norm, start=1):
        xd, yd = norm_to_db(nx, ny)
        print(f"  p{i}: norm=({nx},{ny}) -> input_x={xd:.2f} dB, output_y={yd:.2f} dB")

    g = GraphAndLUT()
    g.set_interior_points_normalized(knots_norm)
    g.build_compression_lut()
    print("\nDerived corners (after update_corner_points):")
    print(f"  left:  ({g.get_point_x(0):.3f}, {g.get_point_y(0):.3f})")
    li = g.num_points - 1
    print(f"  right: ({g.get_point_x(li):.3f}, {g.get_point_y(li):.3f})")
    print(f"compression threshold (first LUT cell deviating from unity): {g.comp_curve_min_threshold_db:.2f} dB")

    # Static sweep through -10 dB neighborhood (and wider for crossing)
    dbs = np.linspace(-18.0, -6.0, 241)
    crossings = find_11_crossings(g, np.linspace(-20.0, 2.0, 2001))
    print("\nApproximate y=x crossings (curve output == input, GR_before_strength == 0):")
    for c in crossings:
        if GRAPH_MIN_DB - 2 < c < GRAPH_MAX_DB - 0.01:
            print(f"  {c:.3f} dB")
    if crossings and not any(GRAPH_MIN_DB - 2 < c < GRAPH_MAX_DB - 0.01 for c in crossings):
        print("  (none inside graph span)")

    print("\nStatic curve vs 1:1 around -10 dBFS (detector dB):")
    print(f"{'in_dB':>8} {'out_dB':>8} {'GR_tgt':>8}  region")
    strength = 1.0
    for db in [-14.0, -13.5, -13.0, -12.5, -12.0, -11.0, -10.0, -9.0, -8.5, -8.0, -7.5, -7.0]:
        out = g.lookup_compression_lut(db)
        tgt, pre, _ = calculate_gain_reduction_from_db(g, db, 0.0, strength)
        region = "cut" if out < db - 0.02 else ("boost" if out > db + 0.02 else "~unity")
        print(f"{db:8.2f} {out:8.3f} {tgt:8.3f}  {region}")

    srate = 48000.0
    dur = 0.6 if args.signal == "tone" else 0.4
    x, db_sweep, sig_desc = build_dynamic_signal(args.signal, srate, dur, args.freq, args.rms_ms)
    n = x.size
    t = np.arange(n, dtype=np.float64) / srate

    chain = ComposureReferenceChain(srate=srate)
    chain.graph = g
    rms_ms = 0.0 if args.signal == "dc" else max(0.0, float(args.rms_ms))
    if args.signal == "tone" and rms_ms < 0.1:
        print(
            "Warning: --signal tone with very small --rms-ms will show ripple at 2× tone frequency; "
            "try --rms-ms 15–50.",
            file=sys.stderr,
        )
    chain.set_params(
        attack=80000.0,
        release_ms=80.0,
        strength=100.0,
        input_offset_db=0.0,
        rms_size_ms=rms_ms,
        rms_normalization=0.0,
    )
    chain.reset_audio_state()
    y, tr = chain.process_block(x.astype(np.float64), record=True)
    assert tr is not None

    # Indices near -10 dB in the sweep (db_sweep crosses -10 at t = (4/6)*dur)
    step = max(120, n // 72)

    def print_window(center_i: int, label: str) -> None:
        print(f"\n--- {label} ---")
        print(f"{'idx':>10} | {'det_dB':>6} | {'tgt_GR':>8} | {'smth_GR':>9}")
        seen: set[int] = set()
        for off in range(-4, 5):
            i = max(0, min(n - 1, center_i + off * step))
            if i in seen:
                continue
            seen.add(i)
            print(
                f"{i:10d} | {tr['detector_db'][i]:6.2f} | {tr['target_gr_db'][i]:8.3f} | "
                f"{tr['smoothed_gr_db'][i]:9.3f}"
            )

    print(
        "\nDynamic ramp ({}), nominal envelope {:.1f} .. {:.1f} dBFS peak:".format(
            sig_desc, float(db_sweep[0]), float(db_sweep[-1])
        )
    )
    if args.signal == "tone":
        print(
            "Note: RMS of a sine is ~3.01 dB below peak; detector dB sits below the "
            "envelope peak label. Warm-up ~50 ms excluded from window search."
        )

    warm = int(srate * 0.05)
    det = tr["detector_db"]

    if args.signal == "tone":
        # Trace-based centers (RMS level + ripple; avoids peak-time vs detector-time mismatch)
        i_start = index_detector_near(det, -13.9, warm, n // 3)
        i_unity = index_detector_near(det, -13.33, warm, n * 2 // 3)
        i_m10 = index_detector_near(det, -10.0, n // 4, n - 1)
        print_window(i_start, "Early ramp (~-13.9 dB det, still mostly cut)")
        print_window(
            i_unity,
            "Near static y=x crossing (~-13.33 dB det): target_GR crosses ~0 (ripple possible)",
        )
        print_window(
            i_m10,
            "Strong boost region (detector ~-11 dB here: RMS ≈3 dB below peak envelope top)",
        )
    else:
        i_unity = int(n * ((-13.333 + 14.0) / 6.0))
        i_m10 = int(n * (4.0 / 6.0))
        i_start = min(2000, n // 5)
        print_window(i_start, "Early ramp (still in cut vs unity)")
        print_window(i_unity, "Around y=x crossing (~-13.33 dB): target_GR passes through 0")
        print_window(i_m10, "Around -10 dBFS (deep boost on this curve)")

    print(
        "\nInterpretation: target_GR = (curve_output - input) * strength (dB). "
        "Negative => attenuation vs unity; positive => boost. "
        "The envelope uses hysteresis (attack vs release), so smoothed_GR lags when "
        "crossing zero — especially release uses a linear dB/step path by default "
        "(prog_release_blend=0), which avoids snapping at GR=0."
    )

    if args.plot:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib not installed; skipping plot", file=sys.stderr)
            return 0
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        dxf = np.linspace(GRAPH_MIN_DB - 5, GRAPH_MAX_DB + 2, 500)
        oyf = np.array([g.sample_curve_at_db(float(v)) for v in dxf])
        axes[0, 0].plot(dxf, dxf, "k--", alpha=0.4, label="y=x (unity)")
        axes[0, 0].plot(dxf, oyf, lw=1.2, label="curve")
        axes[0, 0].axvline(-10, color="C3", ls=":", label="-10 dB")
        axes[0, 0].set_xlabel("input dB")
        axes[0, 0].set_ylabel("output dB")
        axes[0, 0].legend(loc="lower right")
        axes[0, 0].set_title("Transfer curve (dB)")

        axes[0, 1].plot(dxf, oyf - dxf, lw=1.2)
        axes[0, 1].axhline(0, color="k", ls="--", alpha=0.3)
        axes[0, 1].axvline(-10, color="C3", ls=":")
        axes[0, 1].set_xlabel("input dB")
        axes[0, 1].set_ylabel("output - input (dB)")
        axes[0, 1].set_title("Static GR (before envelope)")

        ax_in = axes[1, 0]
        ax_db = ax_in.twinx()
        (ln0,) = ax_in.plot(t, x, color="C0", lw=0.45, alpha=0.85, label="input")
        (ln1,) = ax_db.plot(t, tr["detector_db"], color="C1", lw=0.9, label="det dB")
        ax_in.set_xlabel("time (s)")
        ax_in.set_ylabel("sample", color="C0")
        ax_db.set_ylabel("detector dB", color="C1")
        ax_in.tick_params(axis="y", labelcolor="C0")
        ax_db.tick_params(axis="y", labelcolor="C1")
        ax_in.legend(handles=[ln0, ln1], loc="upper right", fontsize=8)
        ax_in.set_title("Input + detector level")

        axes[1, 1].plot(t, tr["target_gr_db"], label="target GR", lw=0.9, alpha=0.8)
        axes[1, 1].plot(t, tr["smoothed_gr_db"], label="smoothed GR", lw=0.9, alpha=0.8)
        axes[1, 1].axhline(0, color="k", ls="--", alpha=0.3)
        axes[1, 1].set_xlabel("time (s)")
        axes[1, 1].legend()
        axes[1, 1].set_title(f"GR ({args.signal}, rms={args.rms_ms} ms)" if args.signal == "tone" else "GR (dc)")

        fig.tight_layout()
        fig.savefig(args.plot, dpi=130)
        print("Wrote", args.plot)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
