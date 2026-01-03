# Refactoring Recommendations for Flattery.jsfx

## Executive Summary

This document identifies opportunities to improve code quality through:
- **DRY (Don't Repeat Yourself)**: Eliminating duplicated code patterns
- **Modularity**: Better separation of concerns
- **File Organization**: Improved structure and helper utilities
- **Function Length**: Breaking up long functions for readability

---

## 1. DRY Violations

### 1.1 Catmull-Rom Spline Interpolation (CRITICAL)

**Location**: `04_UI/01_ui.jsfx-inc`
- **Lines 99-201**: Magnitude curve spline drawing
- **Lines 268-315**: Filter gain curve spline drawing

**Problem**: ~100 lines of nearly identical Catmull-Rom spline code duplicated twice.

**Solution**: Extract to helper function:
```jsfx
// In 04_UI/02_ui_rendering_helpers.jsfx-inc (new file)
function sff_draw_catmull_rom_spline(p0_x, p0_y, p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, 
                                     draw_bins, color_r, color_g, color_b, color_a) local(...)
```

**Impact**: Reduces ~200 lines to ~50 lines + 2 function calls.

---

### 1.2 Triangle Drawing (HIGH)

**Location**: `04_UI/01_ui.jsfx-inc`
- **Lines 440-447**: Low cut triangle
- **Lines 453-460**: High cut triangle

**Problem**: Identical triangle drawing code duplicated.

**Solution**: Extract to helper:
```jsfx
function sff_draw_triangle(x, y_top, size, color_r, color_g, color_b) local(...)
```

**Impact**: Reduces ~16 lines to ~8 lines + 2 function calls.

---

### 1.3 Frequency Label Drawing (MEDIUM)

**Location**: `04_UI/01_ui.jsfx-inc`
- **Lines 500-538**: Five nearly identical frequency label drawing blocks

**Problem**: Repetitive label drawing code.

**Solution**: Extract to helper:
```jsfx
function sff_draw_frequency_label(freq_hz, min_freq, max_freq, x0, draw_bins, 
                                  label_y, label_text) local(...)
```

**Impact**: Reduces ~40 lines to ~15 lines + 5 function calls.

---

### 1.4 dB Label Drawing (MEDIUM)

**Location**: `04_UI/01_ui.jsfx-inc`
- **Lines 465-475**: Negative dB labels loop
- **Lines 477-487**: Positive dB labels loop

**Problem**: Similar pattern with only sign difference.

**Solution**: Extract to helper:
```jsfx
function sff_draw_db_labels(start_db, end_db, step_db, x0, y_base, 
                            h, gain_scale_inv, show_plus_sign) local(...)
```

**Impact**: Reduces ~24 lines to ~12 lines + 2 function calls.

---

### 1.5 Next Point Finding Logic (MEDIUM)

**Location**: `04_UI/01_ui.jsfx-inc`
- **Lines 108-123**: Find next magnitude point
- **Lines 250-266**: Find next filter gain point

**Problem**: Similar loop pattern to find next valid point in filtered range.

**Solution**: Extract to helper:
```jsfx
function sff_find_next_point_in_range(start_idx, max_idx, get_freq_func, 
                                      low_cut_hz, high_cut_hz) local(...)
```

**Impact**: Reduces ~30 lines to ~15 lines + 2 function calls.

---

### 1.6 Tilt Calculation Logic (MEDIUM)

**Location**: 
- `03_Processing/05_filter_mapping.jsfx-inc` (lines 17-96): `sff_calculate_tilt_multiplier()`
- `04_UI/01_ui.jsfx-inc` (lines 333-383): Tilt visualization uses similar logic

**Problem**: Tilt calculation logic exists in processing module, but UI reimplements similar scaling.

**Solution**: 
- Keep calculation in processing module (already done)
- UI should call `sff_calculate_tilt_multiplier()` instead of reimplementing
- Extract tilt visualization to separate function

**Impact**: Ensures single source of truth, reduces UI complexity.

---

## 2. Modularity Improvements

### 2.1 UI File Too Large (CRITICAL)

**Location**: `04_UI/01_ui.jsfx-inc` (542 lines)

**Problem**: Single file handles:
- Background rendering
- Magnitude curve drawing
- Filter gain curve drawing
- Tilt visualization
- Cut line drawing
- Mouse interaction
- Label drawing
- All coordinate conversions

**Solution**: Split into focused modules:

```
04_UI/
  01_ui_constants.jsfx-inc      (new - UI constants: colors, sizes)
  02_ui_coordinates.jsfx-inc     (new - coordinate conversion helpers)
  03_ui_rendering_helpers.jsfx-inc (new - spline, triangle, label helpers)
  04_ui_graph_rendering.jsfx-inc (new - graph background, curves, meters)
  05_ui_interaction.jsfx-inc     (new - mouse handling, dragging)
  06_ui_orchestration.jsfx-inc    (renamed from 01_ui.jsfx-inc - main draw function)
```

**Impact**: Each file ~100-150 lines, clear responsibilities.

---

### 2.2 Filter Mapping Mixed Concerns (HIGH)

**Location**: `03_Processing/05_filter_mapping.jsfx-inc`

**Problem**: File contains:
- Tilt calculation (96 lines)
- Rate of change scaling (28 lines)
- Gain mapping (98 lines)

**Solution**: Split into:
```
03_Processing/
  05a_tilt_calculation.jsfx-inc  (new - tilt multiplier calculation)
  05b_rate_of_change.jsfx-inc    (new - rate of change scaling)
  05c_filter_mapping.jsfx-inc    (renamed - gain mapping only)
```

**Impact**: Clear separation of concerns, easier to test and modify.

---

### 2.3 STFT Processing Too Complex (MEDIUM)

**Location**: `03_Processing/04_stft_process.jsfx-inc`

**Problem**: `sff_process_stereo_frame()` (105 lines) does:
- MS/LR conversion
- FFT analysis
- Magnitude computation
- RMS smoothing
- Delta computation
- Gain application
- IFFT synthesis
- Overlap-add

**Solution**: Break into logical stages:
```jsfx
function sff_build_spectrum_from_ring()      // MS/LR + windowing
function sff_analyze_spectrum()              // FFT + magnitude
function sff_compute_gain_deltas()           // Delta computation
function sff_apply_gains_to_spectrum()       // Gain application
function sff_synthesize_and_overlap_add()    // IFFT + OLA
```

**Impact**: Each function ~20-30 lines, easier to understand and test.

---

## 3. Function Length Issues

### 3.1 `sff_ui_draw()` - 520 lines (CRITICAL)

**Location**: `04_UI/01_ui.jsfx-inc`

**Problem**: Massive function doing everything.

**Solution**: Break into logical sections:
```jsfx
function sff_ui_draw() (
  sff_draw_background();
  sff_draw_magnitude_curve();
  sff_draw_filter_gain_curve();
  sff_draw_tilt_visualization();
  sff_draw_cut_lines();
  sff_draw_labels();
  sff_handle_mouse_interaction();
);
```

**Impact**: Main function becomes ~10 lines, each helper ~50-100 lines.

---

### 3.2 `sff_map_fft_gains_to_filters()` - 128 lines (HIGH)

**Location**: `03_Processing/05_filter_mapping.jsfx-inc`

**Problem**: Long function with multiple responsibilities.

**Solution**: Extract helper functions:
```jsfx
function sff_reset_filters_to_unity()        // Lines 135-144
function sff_map_single_filter_gain(i)       // Lines 147-218 (loop body)
function sff_apply_tilt_to_gain(gain_db, filter_freq)  // Lines 164-189
```

**Impact**: Main function becomes ~30 lines, helpers ~20-40 lines each.

---

### 3.3 `sff_calculate_tilt_multiplier()` - 96 lines (MEDIUM)

**Location**: `03_Processing/05_filter_mapping.jsfx-inc`

**Problem**: Complex mathematical function with nested conditionals.

**Solution**: Extract edge case handling and interpolation:
```jsfx
function sff_tilt_edge_cases(freq_hz, nyquist_hz)      // Lines 26-30
function sff_tilt_interpolate(freq_pos, center_pos)    // Lines 31-93
```

**Impact**: Main function becomes ~15 lines, helpers ~40 lines each.

---

### 3.4 `sff_process_stereo_frame()` - 105 lines (MEDIUM)

**Location**: `03_Processing/04_stft_process.jsfx-inc`

**Problem**: Orchestrates many operations.

**Solution**: Already addressed in section 2.3 (modularity).

---

## 4. Helper Functions & Utilities

### 4.1 New Utility Module: `04_UI/02_ui_coordinates.jsfx-inc`

**Purpose**: Centralize coordinate conversion functions.

**Functions**:
```jsfx
function sff_pos_to_x(pos, graph_x0, draw_bins)        // Already exists, move here
function sff_freq_to_x(freq_hz, min_freq, max_freq, x0, draw_bins)  // New convenience
function sff_db_to_y(db_val, y_base, h, gain_scale_inv) // New convenience
function sff_y_to_db(y_val, y_base, h, gain_scale_inv)  // New convenience
```

**Impact**: Consistent coordinate handling, easier to maintain.

---

### 4.2 New Utility Module: `04_UI/03_ui_rendering_helpers.jsfx-inc`

**Purpose**: Reusable rendering primitives.

**Functions**:
```jsfx
function sff_draw_catmull_rom_spline(...)     // Spline drawing
function sff_draw_filled_spline_area(...)      // Filled area under spline
function sff_draw_triangle(...)                // Triangle drawing
function sff_draw_vertical_line(...)           // Vertical line with optional triangle
function sff_draw_frequency_label(...)         // Frequency label
function sff_draw_db_label(...)                // Single dB label
function sff_draw_db_labels(...)                // Multiple dB labels
```

**Impact**: Eliminates duplication, consistent rendering.

---

### 4.3 New Utility Module: `01_Utils/03_spline_math.jsfx-inc`

**Purpose**: Mathematical spline utilities (could be used by processing too).

**Functions**:
```jsfx
function sff_catmull_rom_interpolate(p0, p1, p2, p3, t)  // Pure math, no rendering
function sff_catmull_rom_coefficients(p0, p1, p2, p3)   // Pre-compute coefficients
```

**Impact**: Reusable spline math, testable independently.

---

## 5. File Organization Improvements

### 5.1 Current Structure Issues

1. **Duplicate file naming**: `05_filter_mapping.jsfx-inc` and `05_param_cache.jsfx-inc` both use "05"
2. **UI module too monolithic**: Single 542-line file
3. **Processing concerns mixed**: Tilt, rate-of-change, and mapping in one file

### 5.2 Proposed Structure

```
01_Utils/
  01_constants.jsfx-inc          ✓ (keep)
  02_math_utils.jsfx-inc          ✓ (keep)
  03_spline_math.jsfx-inc         ✨ (new - spline math utilities)

02_FFT/
  01_fft_memory.jsfx-inc          ✓ (keep)
  02_fft_core.jsfx-inc            ✓ (keep)
  03_filter_bank.jsfx-inc          ✓ (keep)
  04_iir_filters.jsfx-inc          ✓ (keep)

03_Processing/
  01_band_config.jsfx-inc         ✓ (keep)
  02_attack_release.jsfx-inc       ✓ (keep)
  03_surround_logic.jsfx-inc       ✓ (keep)
  04_stft_process.jsfx-inc        ✓ (refactor - break up function)
  05a_tilt_calculation.jsfx-inc    ✨ (new - extract from 05_filter_mapping)
  05b_rate_of_change.jsfx-inc      ✨ (new - extract from 05_filter_mapping)
  05c_filter_mapping.jsfx-inc      ✨ (renamed from 05_filter_mapping, simplified)
  05d_param_cache.jsfx-inc        ✨ (renamed from 05_param_cache)
  06_output_mix.jsfx-inc          ✓ (keep)

04_UI/
  01_ui_constants.jsfx-inc         ✨ (new - UI constants)
  02_ui_coordinates.jsfx-inc       ✨ (new - coordinate helpers)
  03_ui_rendering_helpers.jsfx-inc ✨ (new - rendering primitives)
  04_ui_graph_rendering.jsfx-inc   ✨ (new - graph drawing)
  05_ui_interaction.jsfx-inc       ✨ (new - mouse handling)
  06_ui_orchestration.jsfx-inc     ✨ (renamed from 01_ui.jsfx-inc)
```

---

## 6. Implementation Priority

### Phase 1: High Impact, Low Risk (Start Here)
1. ✅ Extract Catmull-Rom spline helper (saves ~200 lines)
2. ✅ Extract triangle drawing helper (saves ~16 lines)
3. ✅ Extract label drawing helpers (saves ~60 lines)
4. ✅ Break up `sff_ui_draw()` into logical sections

**Estimated Impact**: Reduces UI file from 542 lines to ~200 lines + helpers

### Phase 2: Medium Impact, Medium Risk
1. ✅ Split UI into multiple modules
2. ✅ Extract tilt calculation to separate file
3. ✅ Extract rate-of-change to separate file
4. ✅ Break up `sff_map_fft_gains_to_filters()`

**Estimated Impact**: Better organization, easier maintenance

### Phase 3: Lower Priority
1. ✅ Break up `sff_process_stereo_frame()` into stages
2. ✅ Create coordinate utility module
3. ✅ Create spline math utility module

**Estimated Impact**: Further modularity improvements

---

## 7. Code Quality Metrics

### Before Refactoring
- **Longest function**: 520 lines (`sff_ui_draw`)
- **Largest file**: 542 lines (`01_ui.jsfx-inc`)
- **Duplicated code**: ~300+ lines (splines, triangles, labels)
- **Functions > 100 lines**: 3 functions

### After Refactoring (Target)
- **Longest function**: < 100 lines
- **Largest file**: < 200 lines
- **Duplicated code**: < 50 lines
- **Functions > 100 lines**: 0 functions

---

## 8. Testing Considerations

When refactoring, ensure:
1. **Visual regression**: UI looks identical after refactoring
2. **Audio processing**: No changes to audio output
3. **Performance**: No significant CPU increase
4. **Function signatures**: Maintain backward compatibility where possible

---

## 9. Specific Code Examples

### Example 1: Extract Spline Drawing

**Before** (duplicated ~100 lines):
```jsfx
// Lines 99-201: Magnitude spline
// Lines 268-315: Filter gain spline (nearly identical)
```

**After**:
```jsfx
// In 04_UI/03_ui_rendering_helpers.jsfx-inc
function sff_draw_catmull_rom_spline(p0_x, p0_y, p1_x, p1_y, p2_x, p2_y, p3_x, p3_y,
                                     draw_bins, color_r, color_g, color_b, color_a) local(
  x_dist, interp_steps, interp_step_inv, prev_interp_x, prev_interp_y, k, t, t2, t3,
  a0_x, a1_x, a2_x, a3_x, a0_y, a1_y, a2_y, a3_y, interp_x, interp_y,
  prev_x_int, interp_x_int
) (
  x_dist = abs(p2_x - p1_x);
  interp_steps = max((x_dist)|0, 1);
  interp_steps = min(interp_steps, draw_bins);
  interp_step_inv = 1.0 / interp_steps;
  
  prev_interp_x = p1_x;
  prev_interp_y = p1_y;
  k = 1;
  loop(interp_steps,
    t = k * interp_step_inv;
    t2 = t * t;
    t3 = t2 * t;
    
    a0_x = -0.5 * p0_x + 1.5 * p1_x - 1.5 * p2_x + 0.5 * p3_x;
    a1_x = p0_x - 2.5 * p1_x + 2.0 * p2_x - 0.5 * p3_x;
    a2_x = -0.5 * p0_x + 0.5 * p2_x;
    a3_x = p1_x;
    interp_x = a0_x * t3 + a1_x * t2 + a2_x * t + a3_x;
    
    a0_y = -0.5 * p0_y + 1.5 * p1_y - 1.5 * p2_y + 0.5 * p3_y;
    a1_y = p0_y - 2.5 * p1_y + 2.0 * p2_y - 0.5 * p3_y;
    a2_y = -0.5 * p0_y + 0.5 * p2_y;
    a3_y = p1_y;
    interp_y = a0_y * t3 + a1_y * t2 + a2_y * t + a3_y;
    
    prev_x_int = prev_interp_x|0;
    interp_x_int = interp_x|0;
    gfx_set(color_r, color_g, color_b, color_a);
    gfx_line(prev_x_int, prev_interp_y, interp_x_int, interp_y, 0);
    
    prev_interp_x = interp_x;
    prev_interp_y = interp_y;
    k += 1;
  );
  // Final segment
  prev_x_int = prev_interp_x|0;
  p2_x_int = p2_x|0;
  gfx_set(color_r, color_g, color_b, color_a);
  gfx_line(prev_x_int, prev_interp_y, p2_x_int, p2_y, 0);
);

// Usage in UI:
sff_draw_catmull_rom_spline(mag_p0_x, mag_p0_y, mag_p1_x, mag_p1_y, 
                            mag_p2_x, mag_p2_y, mag_p3_x, mag_p3_y,
                            draw_bins, 0.25, 0.55, 0.95, 0.8);
```

---

## 10. Migration Strategy

1. **Create new helper files** alongside existing code
2. **Extract functions** one at a time, test after each
3. **Update call sites** to use new helpers
4. **Remove old code** once verified working
5. **Split large files** after helpers are extracted

---

## Summary

This refactoring will:
- ✅ Reduce code duplication by ~300 lines
- ✅ Improve modularity with focused, single-responsibility modules
- ✅ Improve readability with shorter, well-named functions
- ✅ Make maintenance easier with clear organization
- ✅ Enable better testing with isolated functions

**Estimated Total Impact**: 
- **Lines of code**: Reduce by ~200-300 lines (net, after adding helpers)
- **Function length**: Average function length reduced from ~80 lines to ~30 lines
- **File size**: Average file size reduced from ~200 lines to ~100 lines
- **Maintainability**: Significantly improved through clear separation of concerns

