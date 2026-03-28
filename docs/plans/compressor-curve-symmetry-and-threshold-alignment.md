# Plan: Compressor curve symmetry, threshold alignment, and related behaviour

This document turns the code audit into an actionable roadmap. It assumes the product goal is **predictable alignment** between the drawn transfer curve, the diagonal (1:1), debug “threshold” labelling, and audio behaviour—while preserving intentional differences where they serve sound or CPU.

---

## Goals

1. **Single definition of “curve X”** used for LUT lookup, early-exit/skip paths, and UI readouts (including input offset).
2. **Documented, intentional** behaviour outside `GRAPH_MIN_DB`…`GRAPH_MAX_DB` (extensions/clamps), with optional symmetry if we decide it is musically desirable.
3. **Explicit decision** on whether envelope and GR-blend paths should remain asymmetric (cut vs boost) or be unified.

Non-goals for an initial pass (unless scoped later): redesigning the entire UI graph model, changing Bezier junction logic for aesthetics only, or rewriting harmonic colour without a separate spec.

---

## Issue 1: Threshold vs “where compression starts” vs diagonal

### What the code does today

- `calculate_compression_threshold()` sets `comp_curve_min_threshold_db` to the **X coordinate of the point before the first interior point** where `abs(input_db - output_db) > 0.01`.
- That is **not** necessarily where the smooth curve crosses \(y = x\), because interior points can be off-diagonal while earlier segments still visually cross the diagonal.

### Likely rationale (assumption)

- **CPU / architecture**: Skipping compression when the detector is clearly in a “linear” region avoids per-sample curve work and envelope churn.
- **Stability**: Using discrete graph knots avoids searching for a numerical crossing on Bezier-subdivided segments.
- **Corner points**: The left/right synthetic corners are not user “musical” anchors; the first deviation from 1:1 at a **control point** was a simple, deterministic rule.

### Downsides of leaving it as-is

- Users who think “threshold = diagonal crossing” get **misaligned** behaviour vs the drawn blue curve.
- Debug overlay text (“Threshold: … dB”) reinforces a misleading mental model.

### Proposed work

1. **Rename or clarify in UI/debug** (low risk): e.g. “Curve onset (control point): X dB” vs a separate computed “Diagonal crossing (approx): X dB” if we add it.
2. **Optional**: Add a numerical **crossing finder** on the sampled curve (`sample_curve_at_db_internal` / segment list) for display and/or for threshold; gate behind precision and performance review.
3. **Tests**: Python or fixed-point checks for known point layouts (diagonal until point 2, then knee).

---

## Issue 2: Input offset inconsistent with threshold and skip paths

### What the code does today

- `calculate_gr_from_curve()` evaluates the LUT at `input_level_db + input_offset_db`.
- `calculate_gain_reduction_from_db()` compares **raw** `input_level_db` to `comp_curve_min_threshold_db`.
- `@block` `can_skip_compression` compares **raw** `detector_level` to `comp_curve_min_threshold_linear`.
- UI/histogram use offset-adjusted dB so the dot matches “what the compressor sees on the graph X axis” in intent, but the **gate** does not.

### Likely rationale (assumption)

- Threshold was defined in **physical detector dB** so automation and sidechain levels stay interpretable.
- Input offset was added as a **graph slide** without refactoring all threshold and skip logic.
- The comment in `calculate_compression_threshold()` (“Input offset is NOT factored in here”) reads as an intentional but partial design.

### Downsides of leaving it as-is

- Any non-zero **Input Offset** breaks alignment: the same visual position on the graph does not match when early-exit forces GR = 0 vs when full processing runs.
- Double standards between skip path and curve lookup can cause **clicks or stuck GR** when offset crosses the boundary.

### Proposed work

1. **Define canonical abscissa** `curve_input_db = detector_db + input_offset_db` (name TBD) used everywhere we mean “position on drawn curve”.
2. **Threshold in curve space**: Either
   - store `comp_curve_min_threshold_db` as today but compare using `curve_input_db`, or
   - store threshold in detector space as `comp_curve_min_threshold_db - input_offset_db` (harder to keep stable when offset changes).
3. **Prefer comparing in curve space** to match `graph_points` and LUT.
4. Update `can_skip_compression` to use the same definition (may require converting threshold to linear with `db_to_linear` of `curve_input_db` vs threshold in curve space—careful with ordering).
5. **Regression**: Listen tests with offset ±10 dB straddling threshold; verify no skip/engage flicker.

---

## Issue 3: Asymmetric extension outside the graph (low vs high input)

### What the code does today

- Below `GRAPH_MIN_DB`: tangent extension, then `min(output_db, input_db)` to forbid boost past 1:1 in that region.
- Above `GRAPH_MAX_DB`: output pinned to `sample_curve_at_db_internal(GRAPH_MAX_DB)` / LUT equivalent.
- Inside segment search: left of first segment = tangent; right of last segment = **constant** last Y.

### Likely rationale (assumption)

- **Musical safety**: Prevent runaway gain from extrapolating upward on the right; “never more than 1:1 boost” below the graph protects ultra-low extrapolation.
- **Stability**: Constant extrapolation on the right is cheap and predictable; tangent on the left matches “continue the knee” for expanders.
- **Headroom**: Graph tops at 0 dBFS reference in `GRAPH_MAX_DB`; pinning avoids implying infinite gain above the widget.

### Downsides of “symmetrizing” without care

- **Tangent on both ends** can predict **large boosts** if the user’s last segment slopes up—bad for level safety.
- **Flat on both ends** can **mis-represent** an expander’s intent at very low levels.
- Any change alters **existing presets** and A/B comparisons.

### Proposed work

1. **Document** current rules in user-facing or dev docs as “reference behaviour v1”.
2. **Design v2 options** (pick one product-wide):
   - **A**: Keep asymmetry but align **UI drawn preview** (LUT viz / trails) so it never implies symmetry that DSP does not implement.
   - **B**: Symmetric tangent extension with **explicit caps** (e.g. `min(output, input)` on both sides, or max GR limits).
   - **C**: User toggle “safe extrapolation” vs “continuous tangent” (maintenance cost).
3. Implement chosen option in `sample_curve_at_db`, `lookup_compression_lut`, and any UI cache that duplicates the logic (`01_graph_cache.jsfx-inc`).

---

## Issue 4: Corner points (`update_corner_points`) left/right mismatch

### What the code does today

- Left corner: driven by first segment slope with bottom-edge and X-clamp rules; special case when `p1_y > p2_y` snaps to `(GRAPH_MIN_DB, GRAPH_MIN_DB)`.
- Right corner: \(x = \text{GRAPH_MAX_DB}\), \(y = \min(\text{tangent}, \text{GRAPH_MAX_DB})\) (1:1 cap at top).

### Likely rationale (assumption)

- **Widget bounds**: Keep handles on visible edges; left on bottom, right on right edge matches typical transfer-function editors.
- **Anti-boost on top**: `min(calculated_y, GRAPH_MAX_DB)` prevents the right anchor from sitting above the 1:1 corner of the square.

### Downsides of making corners “symmetric”

- Symmetric formulas might **pull corners off** the bottom/right edges and break hit-testing or user expectations.
- Aligning left/right **mathematically** might conflict with **always** clamping the top to 0 dB output reference.

### Proposed work

1. Treat as **UI geometry + DSP consistency** pair: any change to corners must regenerate segments and LUT identically.
2. Add **unit checks** that corner (0) and corner (last) match `sample_curve_at_db` at `GRAPH_MIN_DB` and `GRAPH_MAX_DB`.
3. Defer “symmetric corner law” unless product wants both edges to use the same tangent+cap policy (spec first).

---

## Issue 5: Envelope and GR-blend asymmetry (negative vs positive GR)

### What the code does today

- `is_negative_gr` selects different blend thresholds (`gr_blend_threshold_reduction_db` vs `gr_blend_threshold_addition_db`) and program-release branches.
- Attack/release hysteresis operates on **magnitudes** but coupled with sign-dependent release logic.

### Likely rationale (assumption)

- **Perception**: Expansion/upward compression and downward compression **feel** different; separate release shapes avoid “pumping” on boosts.
- **Mix safety**: Boost paths often need **gentler or faster** release to avoid runaway resonant build-up.
- **Tuning history**: Independent knobs allow mastering-style reduction vs parallel-style addition without forcing one time constant.

### Downsides of **fixing** (unifying) envelope and blend paths

| Risk | Description |
|------|-------------|
| **Preset regression** | Long-time users’ saved settings assume asymmetric release; unified curves change level trajectories and tonal history. |
| **Audible pumping on boost** | Shared coefficients may make **positive GR** linger or release in a way that exaggerates low-level pumping or “breathing” when the curve adds gain. |
| **Loss of artistic control** | Collapsing to one threshold discards the ability to say “recover quickly from cuts, slowly from boosts” (or the inverse). |
| **More complex UI** | True symmetry with retained flexibility may require **two mirrored sets** of controls anyway—net complexity can rise, not fall. |
| **Interaction with harmonics** | Harmonic stage uses signed GR; envelope symmetry changes when harmonics engage, compounding unpredictability. |
| **Validation burden** | Full matrix: peak vs RMS, feedforward vs feedback, program release modes × sign of GR × strength. |

### Proposed work (phased)

1. **Phase A (documentation only)**: State clearly in docs/release notes that dynamics are **sign-aware by design**.
2. **Phase B (optional “symmetric dynamics” mode)**: Hidden/advanced toggle or preset flag that maps one set of release parameters to both signs, for users who want mirrored behaviour; default **off** for backward compatibility.
3. **Phase C (only if required)**: Shared implementation with **parameter remapping** so existing presets deserialize to equivalent asymmetric behaviour.

**Recommendation**: Treat envelope/blend **as out of scope for “curve/threshold symmetry”** unless the product explicitly wants one global dynamics law; the downsides above dominate.

---

## Issue 6: Harmonics and downstream stages

### Likely rationale (assumption)

- Harmonics keyed off `abs(target_gr_db)` approximate **energy** in the non-linear stage; sign used for directionality of colour.

### Downsides of symmetric harmonic treatment

- May **change timbre** for upward vs downward GR with no user-visible curve change.
- Couples to envelope changes above.

### Proposed work

- After curve/threshold alignment is stable, revisit harmonics in a **separate** ticket with AB stems.

---

## Suggested implementation order

1. **Input offset + threshold + skip alignment** (Issue 2)—highest impact on “trust the graph,” moderate code surface.
2. **Naming / optional diagonal crossing** (Issue 1)—clarifies mental model; low risk if only UI/debug.
3. **Extrapolation policy** (Issue 3)—product decision required; affects presets.
4. **Corner consistency tests** (Issue 4)—tightens DSP/UI match.
5. **Envelope/blend** (Issue 5)—only if explicitly in scope; default to documentation + optional mode.

---

## Files likely touched (reference)

| Area | Files |
|------|--------|
| Threshold / graph data | `03_Compression/02_graph_data_core.jsfx-inc`, `06_gain_reduction.jsfx-inc`, `09_audio_processing_chain.jsfx-inc` |
| Curve sample / LUT | `03_Compression/03_graph_curves.jsfx-inc`, `05_compression_core.jsfx-inc` |
| UI parity with LUT | `Interface/Pages/01_Graph_Page/Core/01_graph_cache.jsfx-inc`, curve drawing modules |
| Envelope / blend | `03_Compression/Envelope/*.jsfx-inc` (only if Phase B/C) |
| Sliders / labels | `Composure.jsfx` (threshold-related copy if any) |

---

## Assumptions (explicit)

- Graph **X** is “input level in dB” and **Y** is “output level in dB” in the same reference frame after any agreed definition of input offset.
- `GRAPH_MIN_DB` / `GRAPH_MAX_DB` bound the **editable** square; `COMP_LUT_*` extends evaluation for optimization and expansion edge cases.
- Backward compatibility of **sound** matters as much as **preset recall** (slider values).

---

## Open questions for product / maintainers

1. Should “threshold” in the UI mean **control-point onset**, **diagonal crossing**, or **first dB of GR**?
2. Is input offset strictly “move the curve under the signal” (curve space), or “trim detector gain” (detector space)? The code currently mixes both.
3. Do we accept preset drift when extrapolation rules change, or version the curve engine?

---

*Last updated: aligned with audit of threshold, LUT, corners, offset, envelope, and harmonics.*
