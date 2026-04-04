# Composure Repo Setup and Architecture Notes

This note documents repository assumptions and naming/layout conventions used by Composure.

## Required sibling repositories

Composure imports two files from sibling directories relative to this repository:

- `../FerglerUI/FerglerUI.jsfx-inc`
- `../MathUtils/00_core_math.jsfx-inc`

Expected local layout:

- `.../Effects/Fergler/Composure/`
- `.../Effects/Fergler/FerglerUI/`
- `.../Effects/Fergler/MathUtils/`

If those sibling paths are missing, JSFX import resolution will fail.

## Folder layout vs phase naming rules

The project uses directory-based organization (for example `01_Utils`, `03_Compression`, `Interface`) while development guidance may reference phase-based naming (`00_` to `05f_`).

Use this cross-reference:

- `01_Utils` -> Foundation and shared constants/memory/state.
- `02_InputProcessing` -> Detector-path input conditioning and filters.
- `03_Compression` -> Curve generation, LUT, GR logic, envelopes, sample chain.
- `04_UI_Controls` -> Composure-specific control definitions and rendering wiring.
- `Interface` -> Generic UI services, graph pages, interaction, orchestration.

For JSFX function safety, keep define-before-use ordering within each imported module chain.

## Current graph range behavior

- Graph range is runtime-configurable through `graph_range_mode` (20/40/60 dB).
- The slider is currently JSFX-visible only and is not yet exposed as a custom GUI control.
- Range updates remap interior points proportionally and invalidate curve/LUT caches.
