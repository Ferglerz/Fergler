# Unused Functions Analysis

## Fixes Applied

### Analyzer Fixes
1. **Removed `tanh` from built-in functions** - `tanh` is a custom function defined in `01_Utils/02_math_utils.jsfx-inc`, not a JSFX built-in. It's actually USED in:
   - `02_InputProcessing/01_dsp_utils.jsfx-inc:65` (limiter soft clipping)
   - `01_Utils/02_math_utils.jsfx-inc:65` (constant initialization)

2. **Fixed logical operator detection** - Updated analyzer to not skip function calls preceded by `!` (negation) and `&&`/`||` (logical operators), which were causing false positives for:
   - `is_double_click_point` - Actually called on line 244 of `UI_Graph/03_graph.jsfx-inc`
   - `is_too_close_to_existing_points` - Actually called on line 154 of `UI_Graph/03_graph.jsfx-inc`

**Result**: Unused functions reduced from 29 to 26 (3 false positives eliminated)

---

## Analysis of Remaining Unused Functions (26 total)

### Compression Module Functions

#### `calculate_gain_reduction` (03_Compression/06_gain_reduction.jsfx-inc:40)
- **What it does**: Legacy wrapper function that converts linear input to dB, then calls `calculate_gain_reduction_from_db`
- **Why it might exist**: Backward compatibility wrapper for older code that passed linear values. The current codebase uses `calculate_gain_reduction_from_db` directly with dB values for better efficiency (avoids redundant conversions)
- **Recommendation**: Keep for backward compatibility if external code might call it, otherwise could be removed

#### `interpolate_compression_curve` (03_Compression/05_compression_core.jsfx-inc:13)
- **What it does**: Direct Bezier curve interpolation from graph points - samples the compression curve on-the-fly without using the lookup table or cached segments. Does real-time Bezier evaluation for any input dB value
- **Why it might exist**: Original implementation before optimization to LUT/cached segments system. The current codebase uses `lookup_compression_lut` which pre-calculates values into a lookup table for much better performance (O(1) lookup vs O(n) curve evaluation)
- **Recommendation**: Could be removed - replaced by LUT system. Might be useful for debugging or if dynamic curve changes are needed without rebuilding the LUT

#### `clear_all_curves` (03_Compression/02_graph_data_core.jsfx-inc:70)
- **What it does**: Sets all curve amounts to 0, removing all curve shaping from graph points - converts all curved segments to straight lines (1:1 compression)
- **Why it might exist**: UI feature to "reset" all curves to straight lines. May have been planned for a "Clear Curves" button or menu option that would flatten the compression curve
- **Recommendation**: Keep for potential UI feature (useful for resetting curves), or remove if not planned

#### `has_curve` (03_Compression/02_graph_data_core.jsfx-inc:66)
- **What it does**: Checks if a specific graph point has curve amount > 0 - simple boolean check
- **Why it might exist**: Helper for UI to determine if a point has curvature. Could be used to show visual indicator (different color/shape) on curved points vs straight points
- **Recommendation**: Keep as utility function - might be useful for future UI features to visually distinguish curved points

#### `invalidate_curve_segments_db` (03_Compression/03_graph_curves.jsfx-inc:194)
- **What it does**: Marks curve segments cache as dirty, forcing regeneration on next access. Fine-grained cache invalidation for just the curve segments
- **Why it might exist**: Cache invalidation helper for more precise control. Currently the cache is invalidated via `invalidate_curve_cache` which also invalidates LUT and visualization cache (coarser but simpler)
- **Recommendation**: Could be useful for fine-grained cache control if performance optimization is needed, or could be removed and rely on `invalidate_curve_cache`

### Harmonic Processing Functions

#### `apply_optical_processing` (03_Compression/08_harmonic_models.jsfx-inc:63)
- **What it does**: Adds very subtle even-dominant harmonics (x2, x4) for transparent "optical compressor" character - generates minimal harmonic content, mostly even harmonics with very low coefficients
- **Why it might exist**: Alternative harmonic model for optical-style compression character. Currently only tape (type 1) and tube (type 2) are used in `apply_harmonic_processing`. This would be type 3 for optical compressors
- **Recommendation**: Keep for future harmonic type expansion (could add `harmonic_type == 3` for optical in the selector)

#### `apply_tube_processing` (03_Compression/08_harmonic_models.jsfx-inc:130)
- **What it does**: Older tube processing using power factor saturation and asymmetric sharpening - different algorithm from `apply_enhanced_tube_processing`. Uses a more complex approach with multiple processing stages
- **Why it might exist**: Original tube implementation before enhancement. Replaced by `apply_enhanced_tube_processing` which uses a simpler polynomial approach (x2, x3, x5) that's easier to tune and control
- **Recommendation**: Could be removed - superseded by enhanced version. Or keep as alternative algorithm option if different tube characteristics are needed

### Math Utilities

#### `soft_clip` (01_Utils/02_math_utils.jsfx-inc:42)
- **What it does**: Soft clipping function using inverse square curve for harmonic generation - smooth saturation above threshold using `1 + sqr((x - threshold) * 4)` formula
- **Why it might exist**: Original soft clipping implementation for harmonics. Currently harmonics use enhanced tape/tube models with polynomial harmonics (x2, x3, x5, x7) instead of this soft clipping approach
- **Recommendation**: Could be removed unless needed for future harmonic algorithms, or keep as general-purpose soft clipping utility for other uses

### State Management

#### `set_large_knob_value` (01_Utils/06_state.jsfx-inc:49)
- **What it does**: Sets value property for large knob control objects - accessor function for `large_knob_defs` array at index `*8 + 7` position
- **Why it might exist**: Helper for large knob control system. Might have been part of a control system that was refactored or simplified. Large knobs might be a special UI control type
- **Recommendation**: Keep if large knob system might be used, otherwise could be removed

### Debug Functions

#### `debug_clear` (01_Utils/03_debug_logging.jsfx-inc:40)
- **What it does**: Clears all debug messages and resets scroll offset to 0 - wipes the debug log clean
- **Why it might exist**: UI function to clear debug log. Could be called from menu or button (like "Clear Log" button) for developer convenience
- **Recommendation**: Keep for potential "Clear Log" UI feature - very useful for debugging workflow

#### `debug_separator` (01_Utils/03_debug_logging.jsfx-inc:59)
- **What it does**: Adds separator line ("----------------------------------------") to debug log for visual grouping
- **Why it might exist**: Helper to organize debug output into sections - makes debug log more readable by adding visual breaks
- **Recommendation**: Keep as utility - useful for organizing debug output into logical sections

### UI Utilities

#### `format_freq_display` (UI_General/02_ui_utils.jsfx-inc:307)
- **What it does**: Formats frequency values for display with "k" suffix (e.g., "4k" for 4000 Hz, "1.5k" for 1500 Hz, "500" for 500 Hz) - converts Hz to kHz for readability
- **Why it might exist**: Display formatting for frequency sliders (HP/LP filters). May have been replaced by different formatting approach that handles units differently
- **Recommendation**: Keep as utility function - might be useful for filter frequency display to show kHz for high frequencies

#### `format_value_with_suffix` (UI_General/02_ui_utils.jsfx-inc:287)
- **What it does**: Formats values with appropriate decimal places and suffix (%/dB/ms/Hz) - general-purpose formatter with multiple display modes
- **Why it might exist**: General-purpose value formatter. Currently `format_slider_value` is used which may have different formatting logic or may not support all these suffixes
- **Recommendation**: Keep as utility - might be useful for custom display needs where different formatting is required

#### `set_slider_increment` (UI_General/02_ui_utils.jsfx-inc:231)
- **What it does**: Convenience wrapper to set slider increment property via property system - calls `set_slider_property(control_index, 0, increment)`
- **Why it might exist**: Helper for dynamic slider property changes. May have been planned for runtime slider modification (e.g., changing increment based on mode or context)
- **Recommendation**: Keep as utility - useful for dynamic control configuration if slider properties need to be changed at runtime

#### `update_value_from_mouse_delta` (UI_General/02_ui_utils.jsfx-inc:199)
- **What it does**: Updates slider value based on vertical mouse drag delta, with increment snapping - calculates new value from mouse movement distance with sensitivity scaling
- **Why it might exist**: Alternative input method for slider control (drag-based instead of click-and-drag). Current system might use different interaction pattern (e.g., direct value setting from click position rather than delta-based)
- **Recommendation**: Keep if drag-based interaction is planned, otherwise could be removed

#### `draw_ui_panel_background` (UI_General/05_header.jsfx-inc:90)
- **What it does**: Draws background rectangle for UI panel area - fills a rectangular region with UI background color and border
- **Why it might exist**: Background rendering for UI sections. May have been replaced by other rendering functions or rendering might be handled at a higher level
- **Recommendation**: Could be removed if not needed, or keep for modular UI background rendering

#### `set_interactive_color` (UI_General/01_drawing_primitives.jsfx-inc:122)
- **What it does**: Sets color based on hover/active state with normal and highlight colors - provides visual feedback for interactive elements by blending between normal and highlight colors
- **Why it might exist**: Color state management for hover/click feedback. May have been replaced by inline color logic that directly sets colors without this abstraction
- **Recommendation**: Keep as utility - useful for consistent interactive element coloring and would reduce code duplication if used

#### `draw_threshold_line_with_label` (UI_General/01_drawing_primitives.jsfx-inc:168)
- **What it does**: Draws threshold line with text label at specified position - combined rendering function that draws both line and label together
- **Why it might exist**: Combined rendering function for threshold lines. Current code might render line and label separately (e.g., in `render_gr_blend_threshold_line` and `render_input_level_threshold_line`)
- **Recommendation**: Keep as convenience function, or remove if current approach (separate rendering) works better

### Graph Functions

#### `draw_cached_mixed_curves` (UI_Graph/07_graph_curves.jsfx-inc:34)
- **What it does**: Renders curves from cached curve segments (optimized version of `draw_mixed_curves`) - uses pre-calculated cache instead of regenerating each frame
- **Why it might exist**: Performance optimization using pre-calculated cache. Currently `draw_mixed_curves` is used which may regenerate curve segments each frame or use a different caching approach
- **Recommendation**: Could be used to optimize curve rendering if cache is maintained, or remove if current approach (`draw_mixed_curves`) is preferred and performs adequately

#### `validate_threshold_spacing` (UI_General/11_threshold_lines.jsfx-inc:36)
- **What it does**: Ensures minimum spacing between threshold values to prevent overlap - validates that two threshold values maintain `MIN_THRESHOLD_SPACING` distance
- **Why it might exist**: Validation helper for threshold line positioning. May have been replaced by inline validation or different approach (e.g., clamping functions that handle spacing automatically)
- **Recommendation**: Keep as utility - useful for threshold validation logic and would centralize spacing rules

### Slider Object Functions

#### `get_control_object` (UI_Sliders/01h_control_objects.jsfx-inc:161)
- **What it does**: Returns control object (S1-S64 namespace) for a given parameter index - accessor function that maps param_index to the appropriate namespace object (S1, S2, etc.)
- **Why it might exist**: Helper to get control objects dynamically. May not be needed if objects are accessed directly via S1, S2, etc. in the code
- **Recommendation**: Keep as utility - useful for dynamic control access when parameter index is determined at runtime

#### `init_control_objects` (UI_Sliders/01h_control_objects.jsfx-inc:81)
- **What it does**: Initializes all S1-S64 control object namespaces with their parameter data - bulk initialization that calls `construct_from_param` for all 64 sliders
- **Why it might exist**: Bulk initialization for control object system. May not be called if slider objects (from `01h_slider_objects.jsfx-inc`) are used instead, or initialization might be done differently
- **Recommendation**: Keep if control object system might be used, or remove if slider objects are preferred

#### `current_value` (UI_Sliders/01h_slider_objects.jsfx-inc:56 & 01h_control_objects.jsfx-inc:72)
- **What it does**: Instance method to get current live slider value for the object's parameter - calls `slider(this.param_index)` as a convenience method
- **Why it might exist**: Object-oriented accessor for slider values. May not be used if direct `slider(N)` calls are preferred for simplicity
- **Recommendation**: Keep as convenience method if object-oriented approach is used - provides cleaner syntax (`S1.current_value()` vs `slider(1)`)

#### `option_value` (UI_Sliders/01h_slider_objects.jsfx-inc:48 & 01h_control_objects.jsfx-inc:64)
- **What it does**: Instance method to get option value by index for dropdown/enumerated sliders - accesses `dropdown_option_values_base` array
- **Why it might exist**: Object-oriented accessor for dropdown options. May not be used if direct array access is preferred
- **Recommendation**: Keep as convenience method if object-oriented approach is used - provides cleaner syntax for accessing dropdown values

#### `extract_single_option` (UI_Sliders/00_file_reading.jsfx-inc:284)
- **What it does**: Extracts one option value from dropdown options string during slider definition parsing - parses individual option from comma-separated list
- **Why it might exist**: Helper for parsing dropdown options. May have been replaced by `parse_comma_separated_options` or different parsing approach that handles multiple options at once
- **Recommendation**: Could be removed if parsing logic changed, or keep if it's a useful helper for single-option extraction

### VUmeter

#### `mark_dirty` (VUmeter.jsfx:129)
- **What it does**: Sets `needs_redraw = 1` flag to force VU meter redraw - cache invalidation helper
- **Why it might exist**: Cache invalidation helper for VU meter. May not be called if automatic redraw detection (e.g., `check_needs_redraw`) is used instead
- **Recommendation**: Keep as utility - useful for forcing redraws when needed (e.g., after parameter changes)

---

## Summary

### False Positives Fixed (3)
- `tanh` - Actually used in limiter and constant initialization
- `is_double_click_point` - Actually called for double-click detection
- `is_too_close_to_existing_points` - Actually called for point proximity checking

### Likely Legacy/Replaced Functions (4)
- `calculate_gain_reduction` - Legacy wrapper, replaced by `calculate_gain_reduction_from_db`
- `interpolate_compression_curve` - Replaced by LUT system for performance
- `apply_tube_processing` - Replaced by enhanced version
- `soft_clip` - Replaced by polynomial harmonics

### Utilities for Future Features (19)
Most unused functions appear to be utilities kept for potential future use:
- UI helpers (formatting, drawing, validation)
- Debug utilities (clear, separator)
- Object-oriented accessors (current_value, option_value)
- Cache invalidation helpers
- Alternative algorithms (optical processing)

### Recommendation
Most of these functions are small utilities that don't significantly impact codebase size. They could be kept for potential future use, or removed if codebase cleanup is prioritized. The legacy functions (`calculate_gain_reduction`, `interpolate_compression_curve`, `apply_tube_processing`, `soft_clip`) could be removed since they've been superseded by better implementations.



