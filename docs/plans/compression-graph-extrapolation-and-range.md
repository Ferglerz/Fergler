# Plan: Compression graph extrapolation cap and configurable dB range

**Status:** Planning document (no implementation in this change).  
**Product:** Composure (JSFX), repository root `Composure.jsfx` with modular `*.jsfx-inc` includes.

---

## 1. Purpose

Two related improvements:

1. **Extrapolation cap (below-graph / left of first sample):** Stop “infinite” gain reduction when the transfer curve is extended past the drawable graph using the tangent from the first polyline segment. Instead, bound behavior using the geometry of that tangent relative to the **output = 0 dB** line (the top edge of the graph in current constants).
2. **Configurable graph span:** Allow the effective transfer-function editing region to be wider than the current **20 dB** square (e.g. **40 dB** from **−40 dBFS … 0 dBFS** on both axes), as an alternative way to access deeper reduction without relying on unbounded extrapolation.

---

## 2. Coordinate system and semantics (explicit)

These definitions should match implementation comments so DSP, LUT, and UI stay aligned.

| Axis | Meaning | Current fixed bounds |
|------|---------|----------------------|
| **X** | Detector / input level in **dB** (after whatever scaling the compressor applies before the curve) | `GRAPH_MIN_DB` … `GRAPH_MAX_DB` |
| **Y** | **Output** level in **dB** (transfer curve output before downstream makeup / strength if applied downstream) | Same numeric window as X for the square graph |

**Constants today** (`01_Utils/00_constants.jsfx-inc`):

- `GRAPH_MAX_DB = 0` — top of the square; **this is the “Y = 0 dB output” line** in product language.
- `GRAPH_MIN_DB = -20` — bottom of the square.
- `GRAPH_RANGE_DB = 20` — span of the square (`GRAPH_MAX_DB - GRAPH_MIN_DB`).

**“Lowest point on the graph” (engineering interpretation):** For audio sampling, the relevant geometry is the **first sample along the piecewise curve in dB space** (`first_x`, `first_y` from `curve_segments_db`), not necessarily the user’s bottom-left corner handle. The corner point is kept consistent with tangents in `02_graph_data_core.jsfx-inc` (`update_corner_points()`), but the **first segment** used in `sample_curve_at_db_internal()` is the authoritative extrapolation for `input_db <= first_x`.

---

## 3. Assumptions about existing infrastructure

### 3.1 Module graph and single source of truth

- **Curve in dB** is built into `curve_segments_db` by `generate_curve_segments_db()` in `03_Compression/03_graph_curves.jsfx-inc`.
- **Audio** uses `sample_curve_at_db()` → `sample_curve_at_db_internal()` in the same file, then **gain** is derived elsewhere (`03_Compression/06_gain_reduction.jsfx-inc` and chain in `09_audio_processing_chain.jsfx-inc`). Any change to the transfer curve must remain consistent with **strength** and **input offset** application order (verify call order before locking behavior).
- **Fast path:** `build_compression_lut()` in `03_Compression/05_compression_core.jsfx-inc` fills `comp_lut[]` by calling `sample_curve_at_db()` at `COMP_LUT_GRANULARITY` steps. `lookup_compression_lut()` applies **additional** clamps for `input_db < GRAPH_MIN_DB` and `input_db > GRAPH_MAX_DB`. Any new cap must be implemented in **both** `sample_curve_at_db` *and* `lookup_compression_lut` **or** only in `sample_curve_at_db` with LUT rebuild rules verified so LUT entries and interpolation never contradict the function.

### 3.2 LUT extent vs graph extent

- `03_Compression/01_compression_constants.jsfx-inc` defines `COMP_LUT_MIN_DB` (e.g. −120) and `COMP_LUT_MAX_DB` (e.g. +20) so the table extends **far beyond** the drawable graph. This is **intentional** (headroom, expansion, threshold optimization).  
- **Assumption:** Graph-range changes (Plan B) must keep `COMP_LUT_MIN_DB` ≤ any selectable `GRAPH_MIN_DB` and `COMP_LUT_MAX_DB` ≥ any selectable `GRAPH_MAX_DB`, or the LUT must be regrown/rebounded (higher risk; prefer keeping LUT span wide).

### 3.3 UI parity

- The on-screen curve cache in `Interface/Pages/01_Graph_Page/Core/01_graph_cache.jsfx-inc` extends tangents for drawing; users expect **WYSIWYG** relative to the audible curve.  
- **Assumption:** After changing extrapolation math, update **graph cache** and any **LUT visualization** paths (e.g. `lut_viz_cache_dirty` invalidation in `invalidate_curve_cache()`) so debug/UI previews match audio.

### 3.4 Corner points and sorting

- `graph_points[]` includes **dynamic corner** points at indices `0` and `num_points-1`, updated by `update_corner_points()` in `02_graph_data_core.jsfx-inc`. Interior points are sorted by input.  
- **Assumption:** The first **segment** in `curve_segments_db` may start from the left corner; extrapolation uses `curve_segments_db[0..3]`. When changing caps, re-check **vertical first segments** and **near-zero** `seg_width` branches (already guarded with `abs(seg_width) > 0.0001`).

### 3.5 Expansion and threshold optimization

- `calculate_compression_threshold()` in `02_graph_data_core.jsfx-inc` can push `comp_curve_min_threshold_db` down to `COMP_LUT_MIN_DB` when expansion below `GRAPH_MIN_DB` is implied by the tangent.  
- **Assumption:** A **reduction cap** (Plan A) may conflict with “allow expansion far below the graph” behavior. The plan must state **precedence**: e.g. cap applies only to **compressive** extrapolation, or cap disables certain expansion paths, or cap applies only when `output < input` is not desired below `GRAPH_MIN_DB`. This needs an explicit product decision.

### 3.6 Serialization and presets

- `@serialize` in `Composure.jsfx` persists `graph_initialized`, `num_points`, all `graph_points[*]`, and `curve_amounts[*]`. It does **not** currently persist a **graph range** mode.  
- **Assumption:** Adding Plan B requires new `file_var` fields **or** encoding range into an unused slider slot; version bump / migration logic may be needed so old projects load with **20 dB** span and valid point clamps.

### 3.7 Strength parameter

- `slider6:strength` scales behavior globally (`update_parameter_conversions()`).  
- **Assumption:** The user expectation is “deeper reduction via strength + graph shape,” not via unbounded extrapolation. Confirm whether the cap is applied **before** or **after** strength in the signal path; document in the implementation so QA can predict levels.

### 3.8 Hardcoded “20 dB” outside constants

- `Interface/Services/00_coordinate_conversion.jsfx-inc` sets `GR_PIXELS_PER_DB = GRAPH_SIZE / 20` even though `DB_TO_PIXEL_SCALE` uses `GRAPH_RANGE_DB` — this is an **inconsistency** today.  
- Other literals (e.g. meter weight `/ 20` in `Interface/Pages/01_Graph_Page/Meters/01_meter_render.jsfx-inc`, envelope blend comments referencing 20 dB in `03_Compression/Envelope/03_envelope_release.jsfx-inc`) may be **conceptually unrelated** to the graph square; grep and classify before changing.

---

## 4. Plan A — Cap extrapolated reduction using the tangent vs output 0 dB

### 4.1 Current behavior (precise)

For `input_db <= first_x` (`first_x` = first segment start in dB):

- `output = first_y + slope * (input_db - first_x)` with `slope = (seg_y2 - first_y) / (seg_x2 - first_x)` when `|seg_x2 - first_x|` is large enough.
- For `input_db < GRAPH_MIN_DB`, `sample_curve_at_db()` still uses that extrapolation but applies `min(output_db, input_db)` to forbid **boost** (output above input in dB is not the right inequality for linear amplitude—confirm in code whether variables are **dB** at this stage; the existing comment assumes anti-boost in the dB domain as used).

There is **no** upper bound on how **negative** `output_db` can become for very low `input_db` when `slope` is large and positive (deep compression to the left).

### 4.2 Desired behavior (descriptive)

Extend the **same** tangent line until it intersects the horizontal line **output = GRAPH_MAX_DB (0 dB)**. Call that intersection **(x_cross, 0)** in (input_dB, output_dB) space when it exists at finite `x_cross`.

**Cap:** For inputs in the extrapolated region (typically `input_db < first_x`, and possibly only `input_db < GRAPH_MIN_DB` depending on product choice), **do not allow the transfer function to predict deeper compression than implied by this construction**. Intuitively: if the line would meet 0 dB output at some input level, use that geometry as a **stop** for “runaway” reduction when continuing further left.

**Note:** The exact inequality (`max` vs `min`, and whether to clamp against `x_cross` or against `output` at `x_cross`) depends on **sign of slope** and whether `x_cross` lies to the left or right of `first_x`. Implementation should:

1. Branch (or use symmetric formulas) for `slope > 0`, `slope < 0`, `|slope| < epsilon`.
2. Define behavior when the tangent is **parallel** to Y = 0 (slope = 0): no finite `x_cross` — fallback to **current behavior**, **hold output at first_y**, or **cap at bottom-edge output** (product decision).
3. Define behavior when Y = 0 is **never reached** along the ray in the physically meaningful direction (e.g. line already entirely below 0 dB output for all inputs left of `first_x`): fallback rule required.

### 4.3 Implementation touchpoints (checklist)

| Area | File | Function / region |
|------|------|---------------------|
| Core sampling | `03_Compression/03_graph_curves.jsfx-inc` | `sample_curve_at_db_internal()`, `sample_curve_at_db()` |
| LUT consistency | `03_Compression/05_compression_core.jsfx-inc` | `build_compression_lut()`, `lookup_compression_lut()` post-process |
| Graph drawing | `Interface/Pages/01_Graph_Page/Core/01_graph_cache.jsfx-inc` | Tangent extension / first-segment start |
| Invalidation | `03_Compression/05_compression_core.jsfx-inc` | `invalidate_curve_cache()` and any viz cache |
| Threshold / expansion | `03_Compression/02_graph_data_core.jsfx-inc` | `calculate_compression_threshold()` interaction |

### 4.4 Testing suggestions

- **Python:** Replicate `curve_segments_db` first segment and cap logic for a matrix of `(first_x, first_y, seg_x2, seg_y2, input_db)` values, including edge cases above.
- **REAPER:** Extreme quiet input with steep left tangent; confirm GR meter and audio align with drawn curve.
- **Regression:** Default graphs where tangent is mild; ensure no audible change when cap is inactive by construction.

### 4.5 Open decisions (to resolve before coding)

- Apply cap only for `input_db < GRAPH_MIN_DB`, or for **all** `input_db < first_x`?
- Interaction with **expansion** (output > input in dB domain as coded) and `comp_curve_min_threshold_db`.
- Whether **makeup** and **strength** are considered part of “the graph contract” for the cap.

---

## 5. Plan B — Configurable effective graph range (e.g. 20 → 40 dB)

### 5.1 Intent

Keep a **square** transfer-function editor: same range on X and Y, but allow that range to be **20, 40, …** dB so one pixel does not represent the same dB resolution as today (unless `GRAPH_SIZE` is increased later).

**Example:** `GRAPH_MAX_DB = 0`, `GRAPH_RANGE_DB = 40` → `GRAPH_MIN_DB = -40`.

### 5.2 Infrastructure approach

1. **Parameters:** Add a user-facing control (e.g. enumerated slider `{20, 40, 60}` dB span) in `Composure.jsfx` **after** assessing slider slot budget (`// SEARCH STOP` marks the end of slider block).
2. **Runtime constants:** Replace or shadow compile-time `GRAPH_MIN_DB` / `GRAPH_RANGE_DB` in `00_constants.jsfx-inc` with values derived in `@init` / `@slider` from that control, **or** keep compile-time defaults and copy into `graph_min_db_runtime` used everywhere (grep-driven migration). Pure compile-time constants cannot change from a slider without this step.
3. **Coordinate conversion:** Fix `GR_PIXELS_PER_DB` to use `GRAPH_RANGE_DB` (see §3.8). Recompute `DB_TO_PIXEL_SCALE` / histogram offsets when range changes (`init_graph_optimization_constants()` may need calling from `@slider` when range changes, not only `@init`).
4. **Graph data:** `init_graph_points()` already spaces interior points using `GRAPH_RANGE_DB`; corners use `GRAPH_MIN_DB` / `GRAPH_MAX_DB`. Changing range **without** remapping existing `graph_points` will **change** the curve geometry in absolute dB — decide:
   - **Remap** interior points proportionally when span changes, or
   - **Clamp** out-of-range points, or
   - **Reset** graph on range change (simplest UX, destructive).
5. **Serialization:** Persist chosen span; on load, clamp or remap points into the new bounds.
6. **Audit:** Grep for `GRAPH_`, literal `-20`, `/ 20`, and `20 dB` comments across `Interface/` and `03_Compression/` to classify graph-related vs unrelated (envelope blend).

### 5.3 Risks

- **Preset compatibility:** Old presets assume −20…0; loading into −40…0 must not produce NaNs or invalid ordering.
- **UI density:** Labels/grid in `03_graph_display.jsfx-inc` may need adaptive tick spacing for 40 dB mode.
- **CPU:** LUT size is fixed by `COMP_LUT_*`; wider graph does not require wider LUT, but more **unique** curve shapes may stress QA.

---

## 6. Recommended sequencing

1. Resolve **Plan A** open decisions (§4.5), especially expansion vs cap.
2. Implement **Plan A** in DSP + LUT + graph cache + tests.
3. Implement **Plan B** behind a persisted control, with migration and grep cleanup for hardcoded 20 dB.
4. Final pass: documentation strings in UI and this plan’s **Status** field updated to reflect shipped behavior.

---

## 7. Key file index

| File | Role |
|------|------|
| `Composure.jsfx` | Sliders, `@serialize`, import order |
| `01_Utils/00_constants.jsfx-inc` | Graph dB constants |
| `03_Compression/01_compression_constants.jsfx-inc` | LUT bounds |
| `03_Compression/02_graph_data_core.jsfx-inc` | `graph_points`, corners, threshold optimization |
| `03_Compression/03_graph_curves.jsfx-inc` | Bezier → segments, `sample_curve_at_db*` |
| `03_Compression/05_compression_core.jsfx-inc` | LUT build / lookup |
| `Interface/Services/00_coordinate_conversion.jsfx-inc` | Pixel ↔ dB, `init_graph_optimization_constants()` |
| `Interface/Pages/01_Graph_Page/Core/01_graph_cache.jsfx-inc` | Drawn curve / tangent cache |

---

## 8. Revision history

| Date | Author | Notes |
|------|--------|-------|
| 2026-03-28 | Planning | Initial expanded plan with infrastructure assumptions and open decisions |
