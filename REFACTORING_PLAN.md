# Code Refactoring Plan - DRY, Modularity, and Readability

## 🔍 Issues Identified

### 1. **DRY Violations (Code Duplication)**

#### A. Repeated Index Clamping Pattern
**Location:** `03_surround_logic.jsfx-inc` (lines 37, 65, 71, 80, 87)
```jsfx
idx = idx < 0 ? 0 : (idx >= npos ? (npos-1) : idx);
```
**Fix:** Create helper function `sff_clamp_bin_index(idx, npos)`

#### B. Repeated dB Conversion with Eps Protection
**Location:** Multiple files
```jsfx
sff_linear_to_db(max(value, eps))
```
**Fix:** Create helper function `sff_safe_linear_to_db(value)`

#### C. Duplicate Gain Application Logic
**Location:** `04_stft_process.jsfx-inc`
- `sff_apply_gains_to_spec()` and `sff_apply_linked_gains_to_specs()` share similar patterns
**Fix:** Extract common gain calculation logic

#### D. Stereo/Mono Branching Pattern
**Location:** Multiple functions with `is_stereo` parameter
**Fix:** Consider unified approach or clearer abstraction

### 2. **Modularity Issues**

#### A. File Naming Conflict
**Issue:** Two files with `05_` prefix:
- `05_filter_mapping.jsfx-inc`
- `05_param_cache.jsfx-inc`
**Fix:** Rename one to `06_filter_mapping.jsfx-inc` or `07_filter_mapping.jsfx-inc`

#### B. Large Functions Doing Multiple Things
**Location:** `sff_process_stereo_frame()` - 105 lines, handles FFT, magnitude, delta, gain application, IFFT
**Fix:** Break into smaller functions:
- `sff_build_and_fft_frame()`
- `sff_compute_magnitudes()`
- `sff_compute_deltas()`
- `sff_apply_gains_and_ifft()`

#### C. Inline MS Mode Processing
**Location:** `sff_process_stereo_frame()` lines 162-180, 244-257
**Fix:** Extract to `sff_build_ms_spec()` and `sff_overlap_add_ms_spec()`

### 3. **Readability Issues**

#### A. Magic Numbers
- `0.5` for stereo average (appears multiple times)
- `1.0` for rate of change threshold
- `0.0001` for minimum magnitude threshold
- `0.001` for ms to seconds
**Fix:** Define constants in `01_constants.jsfx-inc`

#### B. Long Parameter Lists
**Location:** Functions like `sff_compute_delta_db_unified()` with 6 parameters
**Fix:** Consider using a configuration struct pattern (if JSFX supports it) or group related parameters

#### C. Inconsistent Naming
- Some functions use `_lin` suffix, others don't
- Mix of `mag` and `magnitude` terminology
**Fix:** Standardize naming convention

## 📋 Recommended Refactorings

### Priority 1: High Impact, Low Risk

1. **Add Helper Functions to Math Utils**
   ```jsfx
   // In 01_Utils/02_math_utils.jsfx-inc
   function sff_clamp_bin_index(idx, npos) (
     idx < 0 ? 0 : (idx >= npos ? (npos-1) : idx);
   );
   
   function sff_safe_linear_to_db(value) (
     sff_linear_to_db(max(value, eps));
   );
   ```

2. **Extract Constants**
   ```jsfx
   // In 01_Utils/01_constants.jsfx-inc
   SFF_STEREO_AVG_FACTOR = 0.5;
   SFF_RATE_OF_CHANGE_THRESHOLD_DB = 1.0;
   SFF_MIN_MAGNITUDE_THRESHOLD = 0.0001;
   SFF_MS_TO_SEC = 0.001;
   ```

3. **Fix File Naming**
   - Rename `05_filter_mapping.jsfx-inc` to `06_filter_mapping.jsfx-inc`
   - Update import in `Flattery.jsfx`

### Priority 2: Medium Impact, Medium Risk

4. **Extract MS Mode Processing**
   ```jsfx
   function sff_build_ms_spec(in_ring_L, in_ring_R, spec_L, spec_R, n) (
     // Extract MS encoding logic
   );
   
   function sff_overlap_add_ms_spec(spec_L, spec_R, out_ring_L, out_ring_R, ...) (
     // Extract MS decoding logic
   );
   ```

5. **Unify Neighbor Target Functions**
   ```jsfx
   // Instead of separate mono/stereo functions, use unified function with is_stereo flag
   function sff_compute_neighbor_target(mag_base, magL_base, magR_base, bin, radius, is_stereo) (
     // Unified logic
   );
   ```

6. **Extract Gain Application Common Logic**
   ```jsfx
   function sff_compute_target_gain_db(bin, delta_db, str_eff, active, max_boost_db, max_cut_db) (
     active ? sff_clamp_gain(delta_db * str_eff, max_boost_db, max_cut_db) : 0;
   );
   ```

### Priority 3: Lower Priority, Higher Risk

7. **Break Down Large Functions**
   - Split `sff_process_stereo_frame()` into smaller, focused functions
   - Each function should have a single, clear responsibility

8. **Standardize Naming Convention**
   - Document and enforce naming patterns
   - Consider creating a style guide

## 🎯 Implementation Order

1. **Phase 1: Safe Helpers** (Priority 1, items 1-2)
   - Add helper functions and constants
   - Low risk, immediate readability improvement

2. **Phase 2: File Organization** (Priority 1, item 3)
   - Fix naming conflict
   - Update imports

3. **Phase 3: Extract Patterns** (Priority 2, items 4-6)
   - Extract MS processing
   - Unify neighbor functions
   - Extract gain logic

4. **Phase 4: Major Refactoring** (Priority 3, items 7-8)
   - Break down large functions
   - Standardize naming

## 📝 Notes

- All refactorings should maintain backward compatibility
- Test after each phase
- Update comments and documentation as you go
- Consider creating unit tests for helper functions if possible

