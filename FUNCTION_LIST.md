# JSFX Function List - Composure Compressor

Complete function reference organized by module file. Each function includes its purpose and parameter count.

## Table of Contents
- [01_Utils - Foundation Layer](#01_utils---foundation-layer)
- [02_InputProcessing - Input Processing Layer](#02_inputprocessing---input-processing-layer)
- [03_Compression - Compression Engine Layer](#03_compression---compression-engine-layer)
- [04_UI_Rendering - UI Rendering Layer](#04_ui_rendering---ui-rendering-layer)
- [05_UI_UserInteractions - User Interaction Layer](#05_ui_userinteractions---user-interaction-layer)
- [06_UI_Orchestration - UI Orchestration Layer](#06_ui_orchestration---ui-orchestration-layer)

---

## 01_Utils - Foundation Layer

### 01_constants.jsfx-inc
Utility functions for frequency handling and formatting.

- `get_freq_from_index(index)` (1 param) - Convert frequency index to Hz value (HP filter)
- `get_freq_from_lp_index(index)` (1 param) - Convert frequency index to Hz value (LP filter)
- `format_freq_display(freq)` (1 param) - Format frequency value for display (e.g., "2.1k")

### 02_math_utils.jsfx-inc
Mathematical utility functions for audio processing.

- `clamp(value, min_val, max_val)` (3 params) - Clamp value between min and max
- `tanh(x)` (1 param) - Hyperbolic tangent function
- `db_to_linear(db)` (1 param) - Convert dB to linear scale
- `linear_to_db(linear)` (1 param) - Convert linear scale to dB
- `soft_clip(x, threshold)` (2 params) - Apply soft clipping with threshold
- `convert_attack_time_to_ms(attack_value, time_unit)` (2 params) - Convert attack time based on unit selector

### 03_debug_logging.jsfx-inc
Debug logging system for development and troubleshooting.

- `debug_clear()` (0 params) - Clear debug message buffer
- `debug_log(message)` (1 param) - Log a message to debug buffer
- `debug_separator()` (0 params) - Add separator line to debug log
- `debug_handle_scroll()` (0 params) - Handle mouse wheel scrolling in debug panel
- `debug_render()` (0 params) - Render debug panel on screen

### 04_file_reading.jsfx-inc
File I/O operations for reading slider definitions from external file.

**Character Scanning:**
- `scan_for_char(str, char, start_pos)` (3 params) - Find character position in string
- `is_digit(char)` (1 param) - Check if character is a digit
- `char_to_digit(char)` (1 param) - Convert character to digit value

**Line Parsing:**
- `is_slider_line(str)` (1 param) - Check if line is a slider definition
- `is_stop_line(str)` (1 param) - Check if line is stop marker
- `parse_integer_from_digits(str, start_pos)` (2 params) - Parse integer from string
- `extract_slider_number(str)` (1 param) - Extract slider number from line
- `parse_sign(str_slot, start_pos)` (2 params) - Parse sign (+/-) from string
- `process_digit(digit, result, decimal_place)` (3 params) - Process digit during number parsing
- `parse_number_from_position(str_slot, start_pos)` (2 params) - Parse number starting at position
- `string_to_number(str_slot)` (1 param) - Convert string to number

**Parameter Extraction:**
- `find_param_delimiters(line)` (1 param) - Find parameter delimiters (=, <, >)
- `extract_default_value(line, pos_equals, pos_less)` (3 params) - Extract default value
- `find_comma_positions(line, params_start)` (2 params) - Find comma positions in parameters
- `extract_min_value(line, params_start, comma1_pos)` (3 params) - Extract minimum value
- `extract_max_value(line, comma1_pos, comma2_pos)` (2 params) - Extract maximum value
- `extract_inc_value(line, comma2_pos, pos_greater)` (3 params) - Extract increment value
- `store_slider_params(slider_index, default_val, min_val, max_val, inc_val)` (5 params) - Store slider parameters in memory
- `extract_slider_params(line, slider_index)` (2 params) - Extract all slider parameters

**Name Extraction:**
- `skip_hidden_prefix(line, start_pos)` (2 params) - Skip "-" prefix for hidden sliders
- `extract_name_to_slot(line, name_start, target_slot)` (3 params) - Extract slider name to string slot
- `extract_slider_name(line, index)` (2 params) - Extract slider name from line

**Dropdown Options:**
- `find_dropdown_delimiters(line)` (1 param) - Find { } delimiters for dropdown options
- `extract_options_string(line, pos_open, pos_close)` (3 params) - Extract options string
- `extract_single_option(temp_str, option_start, option_end, target_slot, slider_index, option_index)` (6 params) - Extract single option value
- `parse_comma_separated_options(options_str, options_len, slider_index)` (3 params) - Parse comma-separated option list
- `store_dropdown_count(slider_index, opt_count)` (2 params) - Store dropdown option count
- `extract_dropdown_options(line, slider_index)` (2 params) - Extract all dropdown options

**File Processing:**
- `process_slider_line(line, slider_num)` (2 params) - Process single slider definition line
- `process_file_line(line, line_count)` (2 params) - Process single file line
- `open_slider_file()` (0 params) - Open slider definitions file
- `finalize_slider_reading(max_slider_num, success)` (2 params) - Finalize reading and set state
- `read_slider_definitions()` (0 params) - Main function to read all slider definitions

**Accessor Functions:**
- `get_slider_name(slider_num)` (1 param) - Get slider name string slot
- `get_dropdown_option_count(slider_num)` (1 param) - Get number of dropdown options
- `get_dropdown_option(slider_num, option_index)` (2 params) - Get dropdown option string slot
- `get_dropdown_option_value(slider_num, option_index)` (2 params) - Get dropdown option numeric value
- `get_freq_list_index(slider_num, freq_value)` (2 params) - Get index for frequency value (O(1) lookup)
- `get_slider_default(slider_num)` (1 param) - Get slider default value
- `get_slider_min(slider_num)` (1 param) - Get slider minimum value
- `get_slider_max(slider_num)` (1 param) - Get slider maximum value
- `get_slider_increment(slider_num)` (1 param) - Get slider increment value

### 05_memory.jsfx-inc
Centralized memory allocation and management.

- `allocate_memory()` (0 params) - Allocate all memory buffers (lookahead, RMS, transient, etc.)

### 06_state.jsfx-inc
State variable initialization and management.

- `clear_rms_state()` (0 params) - Clear RMS detection state
- `init_state_variables()` (0 params) - Initialize all state variables
- `update_histogram_state(gr_value)` (1 param) - Update gain reduction histogram
- `update_input_histogram_state(input_level_db)` (1 param) - Update input level histogram
- `set_large_knob_value(index, value)` (2 params) - Set large knob display value

---

## 02_InputProcessing - Input Processing Layer

### 01_dsp_utils.jsfx-inc
DSP utility functions for audio processing.

- `process_lookahead_audio(input_l, input_r)` (2 params) - Process audio through lookahead delay buffer
- `soft_clip_limiter(input, prev_sample)` (2 params) - Apply soft clipping brickwall limiter

### 02_filters.jsfx-inc
Biquad filter implementation for detection signal filtering.

- `calc_biquad(type, freq)` (2 params) - Calculate biquad filter coefficients
- `apply_detection_filters(detect_l, detect_r)` (2 params) - Apply HP/LP filters to detection signal
- `update_filter_coefficients()` (0 params) - Update filter coefficients based on current slider values

### 04_transient_detection.jsfx-inc
Transient detection for dynamic envelope modification.

- `detect_transients(current_level_db)` (1 param) - Detect transient peaks in input signal

---

## 03_Compression - Compression Engine Layer

### 02_graph_data_core.jsfx-inc
Graph point data structures and manipulation.

**Initialization:**
- `init_graph_optimization_constants()` (0 params) - Initialize graph coordinate conversion constants
- `init_curve_data()` (0 params) - Initialize curve data arrays
- `init_graph_points()` (0 params) - Initialize graph points with default 1:1 curve

**Coordinate Conversion:**
- `db_to_graph_x(db)` (1 param) - Convert dB to graph X coordinate
- `db_to_graph_y(db)` (1 param) - Convert dB to graph Y coordinate
- `graph_x_to_db(x)` (1 param) - Convert graph X coordinate to dB
- `graph_y_to_db(y)` (1 param) - Convert graph Y coordinate to dB
- `is_point_in_graph(x, y)` (2 params) - Check if point is within graph bounds

**Curve Management:**
- `get_curve_amount(point_index)` (1 param) - Get curve amount for point (-1 to 1)
- `set_curve_amount(point_index, amount)` (2 params) - Set curve amount for point
- `has_curve(point_index)` (1 param) - Check if point has curve enabled
- `clear_all_curves()` (0 params) - Clear all curve flags

**Point Management:**
- `sort_points()` (0 params) - Sort points by input dB value
- `add_point(input_db, output_db)` (2 params) - Add new compression point
- `delete_point(point_index)` (1 param) - Delete compression point
- `remove_displaced_points(moved_input_db, moved_output_db)` (2 params) - Remove points displaced by moved point
- `find_point_at_mouse(x, y)` (2 params) - Find point at mouse coordinates

**Compression Threshold:**
- `calculate_compression_threshold()` (0 params) - Calculate compression threshold from graph
- `invalidate_compression_threshold()` (0 params) - Mark threshold as needing recalculation

### 03_graph_curves.jsfx-inc
Curve interpolation algorithms for smooth compression curves.

- `calculate_bezier_control_points(point_index, curve_amount)` (2 params) - Calculate Bezier control points for curve segment
- `evaluate_bezier_curve(t, p0_x, p0_y, p1_x, p1_y, p2_x, p2_y, p3_x, p3_y)` (9 params) - Evaluate Bezier curve at parameter t
- `generate_curve_segments_db()` (0 params) - Generate curve segments for all points
- `invalidate_curve_segments_db()` (0 params) - Mark curve segments as invalid
- `sample_curve_at_db(input_db)` (1 param) - Sample compression curve at input dB value

### 04_graph_cache.jsfx-inc
Compression lookup table (LUT) caching for performance.

- `invalidate_curve_cache()` (0 params) - Mark curve cache as invalid

### 05_compression_core.jsfx-inc
Core compression calculations and lookup table.

- `interpolate_compression_curve(input_db)` (1 param) - Interpolate compression curve (legacy, unused)
- `build_compression_lut()` (0 params) - Build compression lookup table from curve
- `lookup_compression_lut(input_db)` (1 param) - Fast lookup of output dB from input dB
- `invalidate_compression_lut()` (0 params) - Mark LUT as needing rebuild

### 06_gain_reduction.jsfx-inc
Gain reduction computation from input levels.

- `calculate_gr_from_curve(input_level_db)` (1 param) - Calculate gain reduction from curve
- `calculate_gain_reduction_from_db(input_level_db)` (1 param) - Calculate gain reduction from input dB (main function)
- `calculate_gain_reduction(input_level_linear)` (1 param) - Calculate gain reduction from linear input (legacy, unused)

### 07_envelope.jsfx-inc
Envelope following with attack/release and program-dependent release.

**Coefficient Blending:**
- `blend_two_coefficients(coef1, coef2, blend_factor)` (3 params) - Blend two envelope coefficients
- `normalized_blend(blend_fast, blend_slow, coef_fast, coef_slow)` (4 params) - Normalized blend of fast/slow coefficients

**Program-Dependent Release:**
- `release_input_dependent_single(input_level_db)` (1 param) - Input-dependent release coefficient
- `release_gr_dependent(gr_amount)` (1 param) - Gain reduction-dependent release coefficient
- `release_rate_of_change(det_delta)` (1 param) - Rate-of-change-dependent release coefficient
- `select_program_release_coef(target_gr_abs, detector_level_db)` (2 params) - Select release coefficient based on program type

**Envelope Processing:**
- `process_single_stage_envelope(target_gr_db, detector_level_db)` (2 params) - Process single-stage envelope following
- `process_envelope_following(target_gr_db, detector_level_db)` (2 params) - Main envelope following function with program-dependent release

### 08_harmonic_models.jsfx-inc
Harmonic character models for compressor coloration.

**Character Models:**
- `apply_enhanced_tape_processing(driven, amount, combined_factor, even_boost, odd_boost)` (5 params) - Apply tape saturation model
- `apply_enhanced_tube_processing(driven, amount, combined_factor, even_boost, odd_boost)` (5 params) - Apply tube saturation model
- `apply_optical_processing(driven, amount, combined_factor, even_boost, odd_boost)` (5 params) - Apply optical compressor model (unused)
- `apply_valvity_processing(input, amount, power_factor, sharpening_amount, clip_threshold)` (5 params) - Apply valvity model (unused)

**Processing Functions:**
- `apply_asymmetric_sharpening(input, sharpening_amount)` (2 params) - Apply asymmetric sharpening
- `apply_power_factor_saturation(input, power_factor, gain_scaling)` (3 params) - Apply power factor saturation
- `apply_soft_clipping(input, clip_threshold, compensation_factor)` (3 params) - Apply soft clipping
- `apply_harmonic_processing(input, gr_amount, envelope_amount, detector_level, type, drive, mix, even_boost, odd_boost)` (9 params) - Main harmonic processing dispatcher

### 09_audio_processing_chain.jsfx-inc
Complete audio processing pipeline orchestration.

- `process_complete_audio_chain()` (0 params) - Main audio processing function orchestrating all stages (input, filtering, detection, character, envelope, lookahead, gain reduction, harmonics, mix, limiter, output)

---

## 04_UI_Rendering - UI Rendering Layer

### 00_ui_constants.jsfx-inc
UI control creation function.

- `create_ui_control(orientation, display_mode, fill_direction, formatting, format_options)` (5 params) - Create UI control configuration bitmask

### 01_drawing_primitives.jsfx-inc
Basic drawing primitives and color helpers.

**Rounded Rectangles:**
- `draw_rounded_rect(x, y, w, h, radius)` (5 params) - Draw filled rounded rectangle
- `draw_corner_arc(center_x, center_y, radius, start_angle, segments)` (5 params) - Draw single corner arc
- `draw_rounded_rect_outline(x, y, w, h, radius)` (5 params) - Draw rounded rectangle outline

**Group Rendering:**
- `draw_group(group_index)` (1 param) - Draw UI group with background, border, and title

**Color Helpers:**
- `set_interactive_color(is_hovered, is_active, normal_r, normal_g, normal_b, highlight_r, highlight_g, highlight_b, alpha)` (9 params) - Set color based on hover/active state
- `set_point_color(is_hovered, is_curved)` (2 params) - Set color for graph point
- `set_threshold_line_color(threshold_type, is_hovered, is_dragging)` (3 params) - Set color for threshold line

**Threshold Lines:**
- `draw_threshold_line_with_label(line_y, start_x, end_x, threshold_type, threshold_value, label_text, label_x, label_y)` (8 params) - Draw threshold line with label

### 02_ui_utils.jsfx-inc
UI utility functions for control interaction and coordinate conversion.

**Control Interaction:**
- `is_point_in_control(x, y, control_index)` (3 params) - Check if point is inside control bounds
- `update_slider_value(control_index, mouse_x, mouse_y)` (3 params) - Update slider value from mouse position
- `update_value_from_mouse_delta(current_value, min_val, max_val, mouse_dy, sensitivity, param_index)` (6 params) - Update value from mouse delta movement
- `set_slider_property(control_index, property_index, value)` (3 params) - Set slider property
- `set_slider_increment(control_index, increment)` (2 params) - Set slider increment value

**Coordinate Conversion:**
- `clamp_x_to_graph(x)` (1 param) - Clamp X coordinate to graph bounds
- `clamp_y_to_graph(y)` (1 param) - Clamp Y coordinate to graph bounds

**Drawing Utilities:**
- `draw_indicator_circle(x, y, radius, r, g, b, alpha, filled)` (8 params) - Draw indicator circle
- `draw_text_at(r, g, b, a, x, y, format_str, value)` (8 params) - Draw formatted text at position

**Value Formatting:**
- `get_decimal_places(increment)` (1 param) - Get decimal places from increment value
- `format_value_with_suffix(value, increment, display_mode)` (3 params) - Format value with suffix (ms, dB, %, etc.)

### 03_controls.jsfx-inc
Control rendering functions (sliders, knobs, buttons, dropdowns).

**Display Mode:**
- `get_time_display_mode(param_index, display_mode)` (2 params) - Get dynamic display mode for time controls
- `format_slider_value(param_index, value, display_mode, formatting, format_options)` (5 params) - Format slider value for display

**Knob Rendering:**
- `draw_knob_at_position(x, y, value, min_val, max_val, knob_type)` (6 params) - Draw knob at position
- `draw_large_knob_at_position(x, y, value, min_val, max_val, knob_type)` (6 params) - Draw large knob at position

**Slider Rendering:**
- `draw_control(x, y, w, h, value, min_val, max_val, label, param_index, slider_config)` (10 params) - Draw control with configurable behavior (horizontal, vertical, knob)

**Control Rendering:**
- `draw_generic_button(x, y, w, h, is_on, label)` (6 params) - Draw button control
- `draw_generic_dropdown(x, y, w, h, current_value, label, param_index)` (7 params) - Draw dropdown control
- `render_control(index)` (1 param) - Main control rendering dispatcher

### 04_debug.jsfx-inc
Debug rendering functions.

- `draw_debug_performance_counters()` (0 params) - Draw performance counters on screen

### 05_header.jsfx-inc
Header and menu rendering.

- `draw_menu_button()` (0 params) - Draw menu button in header
- `draw_custom_menu()` (0 params) - Draw custom menu dropdown
- `draw_header()` (0 params) - Draw complete header
- `draw_ui_panel_background()` (0 params) - Draw main UI panel background

### 06_graph_cache.jsfx-inc
Graph curve caching for rendering performance.

- `calculate_curve_hash()` (0 params) - Calculate hash of current curve state
- `generate_curve_cache()` (0 params) - Generate cached curve points for rendering
- `cache_curve_if_needed()` (0 params) - Check and regenerate cache if needed

### 07_graph_curves.jsfx-inc
Graph curve rendering functions.

- `draw_compression_lut_curve()` (0 params) - Draw compression lookup table curve
- `draw_cached_mixed_curves()` (0 params) - Draw cached mixed curves (LUT + bezier)
- `draw_debug_invisible_points(point_index, curve_factor)` (2 params) - Draw invisible point indicators for debugging
- `draw_mixed_curves()` (0 params) - Draw mixed curves (LUT + bezier segments)
- `draw_graph_points()` (0 params) - Draw compression graph points
- `draw_threshold_lines_on_graph()` (0 params) - Draw threshold lines on graph

### 08_graph_meters.jsfx-inc
Graph meter and histogram rendering.

**Meters:**
- `draw_processing_state_indicator()` (0 params) - Draw red/green processing state indicator
- `draw_gain_reduction_meter()` (0 params) - Draw gain reduction meter

**Histogram Rendering:**
- `draw_input_histogram_line(buffer, buffer_pos, max_samples, r, g, b, a)` (7 params) - Draw input histogram line
- `draw_gr_histogram_neg_line_pixel(buffer, r, g, b, a)` (5 params) - Draw GR histogram negative line (pixel-based)
- `draw_gr_histogram_neg_line(buffer, buffer_pos, max_samples, r, g, b, a)` (7 params) - Draw GR histogram negative line
- `draw_gr_histogram_pos_line_pixel(buffer, r, g, b, a)` (5 params) - Draw GR histogram positive line (pixel-based)
- `draw_gr_histogram_pos_line(buffer, buffer_pos, max_samples, r, g, b, a)` (7 params) - Draw GR histogram positive line
- `draw_input_histogram()` (0 params) - Draw complete input histogram
- `draw_histogram()` (0 params) - Draw complete gain reduction histogram

### 09_graph_display.jsfx-inc
Graph display elements (background, grid, labels, hints).

- `draw_graph_background()` (0 params) - Draw graph background
- `draw_grid()` (0 params) - Draw graph grid lines
- `draw_labels_and_info()` (0 params) - Draw axis labels and info text
- `draw_compression_threshold_overlay()` (0 params) - Draw compression threshold overlay text
- `draw_mouse_hints()` (0 params) - Draw mouse interaction hints

### 10_menu.jsfx-inc
Menu interaction handling.

- `is_menu_button_clicked()` (0 params) - Check if menu button was clicked
- `handle_menu_button_click()` (0 params) - Handle menu button click
- `is_mouse_in_menu()` (0 params) - Check if mouse is in menu area
- `get_hovered_menu_item()` (0 params) - Get currently hovered menu item index
- `handle_menu_item_click(item_index)` (1 param) - Handle menu item click

### 11_threshold_lines.jsfx-inc
Threshold line interaction and rendering.

**Validation:**
- `validate_threshold_spacing(value, other_value)` (2 params) - Validate threshold spacing constraints

**Clamping:**
- `clamp_gr_blend_threshold(new_value)` (1 param) - Clamp GR blend threshold value
- `clamp_input_level_threshold(new_value)` (1 param) - Clamp input level threshold value
- `clamp_input_level_threshold_2(new_value)` (1 param) - Clamp input level threshold 2 value
- `clamp_transient_threshold(new_value)` (1 param) - Clamp transient threshold value

**Coordinate Conversion:**
- `gr_blend_db_to_meter_y(gr_db)` (1 param) - Convert GR blend dB to meter Y coordinate
- `meter_y_to_gr_blend_db(y)` (1 param) - Convert meter Y coordinate to GR blend dB

**Hit Testing:**
- `is_mouse_near_meter_line(mouse_x, mouse_y, line_y)` (3 params) - Check if mouse is near meter line
- `is_mouse_near_graph_line(mouse_x, mouse_y, line_y)` (3 params) - Check if mouse is near graph line
- `check_threshold_line(mouse_x, mouse_y, threshold_type, is_visible, line_y, is_on_meter)` (6 params) - Check if threshold line is hit
- `find_threshold_line_at_mouse(mouse_x, mouse_y)` (2 params) - Find threshold line at mouse position

**Updates:**
- `update_gr_blend_threshold(mouse_y)` (1 param) - Update GR blend threshold from mouse Y
- `update_input_level_threshold(mouse_y)` (1 param) - Update input level threshold from mouse Y
- `update_input_level_threshold_2(mouse_y)` (1 param) - Update input level threshold 2 from mouse Y
- `update_transient_threshold(mouse_y)` (1 param) - Update transient threshold from mouse Y
- `update_dragged_threshold_line(mouse_y)` (1 param) - Update dragged threshold line position
- `handle_threshold_line_mouse()` (0 params) - Main threshold line mouse interaction handler

### 12_dot_trail.jsfx-inc
Trail dot system for visualizing compression activity.

- `create_trail_dot()` (0 params) - Create new trail dot at current position
- `update_trail_dots()` (0 params) - Update trail dot fade and remove expired dots
- `render_trail_dots()` (0 params) - Render all trail dots
- `update_and_render_trail_dots()` (0 params) - Update and render trail dots (combined function)

---

## 05_UI_UserInteractions - User Interaction Layer

### 01_control_definitions.jsfx-inc
Control definition and layout functions.

**Control Definition:**
- `define_group(index, x, y, w, h, show_title, title)` (7 params) - Define UI group
- `set_control_group(group_index)` (1 param) - Set current control group
- `define_slider(index, x, y, w, h, param_index, min_val, max_val, label, slider_config)` (10 params) - Define slider control
- `define_button(index, x, y, w, h, param_index, min_val, max_val, label)` (9 params) - Define button control
- `define_dropdown(index, x, y, w, h, param_index, min_val, max_val, label)` (9 params) - Define dropdown control

**Layout:**
- `setup_control_layout()` (0 params) - Setup complete control layout
- `setup_header_controls()` (0 params) - Setup header controls

**Rendering:**
- `render_all_groups()` (0 params) - Render all UI groups
- `render_custom_ui_controls()` (0 params) - Render all custom UI controls

### 02_control_interactions.jsfx-inc
Control interaction handling.

- `update_pdc_delay_if_needed(param_index)` (1 param) - Update plugin delay compensation if parameter changed
- `reset_control_to_default(control_index)` (1 param) - Reset control to default value
- `is_double_click_control(control_index)` (1 param) - Check if control was double-clicked
- `handle_control_click(control_index)` (1 param) - Handle control click
- `handle_drag_continuation()` (0 params) - Handle continued drag operation
- `handle_ui_mouse_input()` (0 params) - Main UI mouse input handler

### 03_graph.jsfx-inc
Graph interaction handling.

- `invalidate_all_graph_caches()` (0 params) - Invalidate all graph-related caches
- `mouse_to_constrained_graph_coords()` (0 params) - Convert mouse to constrained graph coordinates
- `is_too_close_to_existing_points(mouse_x, mouse_y)` (2 params) - Check if point is too close to existing points (unused)
- `handle_point_movement()` (0 params) - Handle point movement interaction
- `handle_curve_adjustment()` (0 params) - Handle curve adjustment interaction
- `handle_point_addition()` (0 params) - Handle point addition interaction
- `handle_point_deletion()` (0 params) - Handle point deletion interaction
- `is_double_click_point(point_index)` (1 param) - Check if point was double-clicked (unused)
- `reset_point_to_1_to_1(point_index)` (1 param) - Reset point to 1:1 ratio
- `handle_graph_mouse_input()` (0 params) - Main graph mouse input handler

---

## 06_UI_Orchestration - UI Orchestration Layer

### 01_ui_interaction.jsfx-inc
Main UI interaction coordinator.

- `process_mouse_input()` (0 params) - Process all mouse input (UI controls, graph, threshold lines, menu)

### 02_ui_orchestration.jsfx-inc
Main UI rendering coordinator.

- `render_complete_interface()` (0 params) - Render complete UI interface (header, controls, graph, meters, menu, debug)

---

## Statistics

- **Total Functions**: ~276
- **Modules**: 38 files
- **Layers**: 6 (Utils, InputProcessing, Compression, UI_Rendering, UI_UserInteractions, UI_Orchestration)

---

## Notes

- Functions marked as "(unused)" are declared but never called in the codebase
- Functions marked as "(legacy, unused)" are old implementations kept for reference but not used
- Parameter counts reflect the actual function signatures
- All functions are defined in `@init` sections and become available globally after import

