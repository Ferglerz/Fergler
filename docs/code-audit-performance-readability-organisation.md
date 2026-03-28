# Code audit: performance, readability, organisation, and effectiveness

Audit of the Composure JSFX project (audio chain, UI, and module layout). No code was changed as part of this document.

---

## Performance

### Audio (`@sample`)

- **`process_complete_audio_chain()`** does substantial work per sample: detection, optional filters, RMS branch, gain reduction, envelope, lookahead, gain application, harmonics, and limiter. Early **compression skip** (`can_skip_compression`) and **envelope skip** (`can_skip_envelope`) help when the signal is below threshold or already at rest.
- **Debug instrumentation runs on every sample**: `debug_counter_audio_chain += 1` and, approximately once per `srate` samples, a large block that copies and clears many counters (`03_Compression/09_audio_processing_chain.jsfx-inc`). Comments in `Interface/Debug/01_debug.jsfx-inc` describe counters as “always active during development”. For a release-oriented build, gating this behind a single flag (e.g. `debug_profiling_enabled`) or omitting it would remove steady overhead from the hottest path.
- **Harmonics**: `apply_harmonic_processing` is invoked separately for left and right channels. If the model shares identical scalar work across channels, hoisting shared calculations (without changing stereo behaviour) could save CPU.
- **Limiter**: The `abs_final_* > 0.944` guard avoids calling `soft_clip_limiter` most of the time—a reasonable micro-optimization.

### Control rate (`@block`)

- **`refresh_core_parameters(0)`** every block recalculates filter coefficients, attack/release/hold, RMS targets, then **`smooth_rms_coefficient()`** (which uses `exp()` every block). That supports live parameter changes; if more CPU headroom is needed later, caching a “last slider fingerprint” and skipping unchanged coefficient paths would be a possible next step (with care for automation and modulation).

### Graphics (`@gfx`)

- Each frame: clearing up to **256** `updated_slider_values` entries, full **graph page** drawing, **reflection blur** (`gfx_blurto`), meters, and trails. Caching **`is_audio_active`** once per frame is a good pattern.
- **`render_graph_page()`** is invoked from `render_complete_interface()` regardless of the active page; confirm that hidden or inactive views are not doing redundant heavy drawing.

---

## Readability

- **`Composure.jsfx`** is unusually clear for JSFX: grouped sliders, an import map with rationale, helpers such as `refresh_core_parameters`, and documented `@serialize` behaviour.
- **`process_complete_audio_chain()`** is long and deeply nested (ternaries and boolean flags). Comments help, but splitting into smaller named functions (“detection”, “target GR”, “apply gain and output”) would improve scanability while respecting JSFX’s define-before-use ordering.
- **Magic numbers** (e.g. limiter threshold `0.944`, trail sizing caps) would read better as named constants beside related init or config.
- **`Interface/Core/02_utils.jsfx-inc`** vs **`Interface/Core/05_utils.jsfx-inc`**: `05_utils` states that several helpers live in FerglerUI while `02_utils` still defines overlapping utilities. That split can confuse anyone tracing control or layout behaviour.

---

## Organisation

- **Import order** in `Composure.jsfx` is complex but **documented** (envelope modules before `09_audio_processing_chain`, `05_envelope_parameters` after, etc.). Comments about dependencies such as **`clear_rms_state`** and **`09_audio_processing_chain`** signal **tight coupling** that a future refactor could simplify.
- **Workspace development rules** describe a strict phased naming scheme (`00_`–`05f_`); this repository uses **directory-based** layout (`01_Utils`, `03_Compression`, `Interface/...`). That is fine operationally but adds **onboarding friction** unless docs cross-reference the two conventions.
- **External includes**: `../FerglerUI/FerglerUI.jsfx-inc` and `../MathUtils/00_core_math.jsfx-inc` mean the effect is not fully self-contained in this tree. Packaging or contributor docs should state required relative paths.

---

## Effectiveness (design vs goals)

- **Strengths**: Preset survival via `@serialize` and `ext_noinit`; **PDC** integrated in `refresh_core_parameters`; **block-max** paths for histograms reduce per-sample dB work for meters; **staged skipping** for compression and envelope; **RMS coefficient smoothing** in `@block` targets zipper noise without abandoning live updates.
- **Debug tooling**: Centralised counters and a debug panel are **effective for profiling** hot functions; the tradeoff is **always-on cost** unless gated.
- **`get_detection_signal`**: Writes globals `detect_l` / `detect_r` rather than returning values—idiomatic in JSFX but easy to misuse; a consistent pattern (e.g. always passing output buffers) would reduce hidden side effects.

---

## Priority summary

| Priority | Area      | Issue |
|----------|-----------|--------|
| High     | `@sample` | Unconditional debug counter work on every sample |
| Medium   | `@gfx`    | Cost of full graph + blur every frame; verify hidden-page work |
| Medium   | Readability | Monolithic audio chain; overlapping util module story |
| Low      | `@block`  | Optional caching when sliders are unchanged |
| Low      | Docs/repo | Document FerglerUI + MathUtils paths; align or cross-link folder vs phase rules |

### Suggested follow-ups

1. Gate or strip **per-sample debug aggregation** for non-debug builds.
2. Review **`@gfx`** to avoid redundant work when the graph (or heavy overlays) are not visible.
3. Optionally refactor **`process_complete_audio_chain()`** into smaller functions for readability, preserving JSFX definition order.
