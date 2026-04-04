"""
Run: python -m composure_reference --out /tmp/composure_trace.npz

Generates a short test signal, processes through ComposureReferenceChain, saves arrays.
Optional: --plot saves a PNG if matplotlib is installed.
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

from .chain import ComposureReferenceChain


def main() -> int:
    p = argparse.ArgumentParser(description="Composure DSP reference runner / recorder")
    p.add_argument("--srate", type=float, default=44100.0)
    p.add_argument("--seconds", type=float, default=0.25)
    p.add_argument("--out", type=str, default="", help="Output .npz path (default: ./composure_reference_trace.npz)")
    p.add_argument("--plot", type=str, default="", help="If set, save waveform plot to this PNG path")
    args = p.parse_args()

    n = int(args.srate * args.seconds)
    t = np.arange(n, dtype=np.float64) / args.srate
    # Loud burst then decay — exercises attack/release
    env = np.minimum(1.0, t * 200.0) * np.exp(-t * 3.0)
    x = 0.5 * env * np.sin(2.0 * np.pi * 220.0 * t)

    chain = ComposureReferenceChain(srate=args.srate)
    chain.reset_audio_state()
    y, trace = chain.process_block(x, record=True)

    out_path = args.out or os.path.join(os.getcwd(), "composure_reference_trace.npz")
    if trace is not None:
        np.savez(
            out_path,
            in_=trace["in"],
            out=trace["out"],
            detector_db=trace["detector_db"],
            target_gr_db=trace["target_gr_db"],
            smoothed_gr_db=trace["smoothed_gr_db"],
            srate=np.array([args.srate]),
        )
        print("Wrote", out_path)

    if args.plot:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib not installed; skip --plot", file=sys.stderr)
            return 0
        fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        axes[0].plot(t, x, label="in", lw=0.8)
        axes[0].plot(t, y, label="out", lw=0.8, alpha=0.85)
        axes[0].legend(loc="upper right")
        axes[0].set_ylabel("sample")
        if trace is not None:
            axes[1].plot(t, trace["detector_db"], lw=0.8, color="C2")
            axes[1].set_ylabel("detector dB")
            axes[2].plot(t, trace["target_gr_db"], label="target GR", lw=0.8)
            axes[2].plot(t, trace["smoothed_gr_db"], label="smoothed GR", lw=0.8, alpha=0.85)
            axes[2].legend(loc="upper right")
            axes[2].set_ylabel("dB")
        axes[-1].set_xlabel("time (s)")
        fig.tight_layout()
        fig.savefig(args.plot, dpi=120)
        print("Wrote plot", args.plot)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
