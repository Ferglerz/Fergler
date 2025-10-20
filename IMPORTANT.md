# JSFX CRITICAL SYNTAX AND CODE ORDER RULES

## 🚨 CRITICAL: FUNCTION DEFINITION ORDER

### **FUNDAMENTAL RULE: FUNCTIONS MUST BE DEFINED BEFORE BEING CALLED**

In JSFX, **ALL FUNCTIONS MUST BE DEFINED BEFORE THEY ARE CALLED**. This applies both within files and across imported modules.

### **Module Import Order (STRICTLY ENFORCED)**

The prefix system ensures correct dependency order:

```
Phase 0 (00): Configuration - No dependencies
Phase 1 (01): Foundation - Depends on Phase 0
Phase 2 (02): Utilities - Depends on Phases 0-1  
Phase 3 (03): Graph Data - Depends on Phases 0-2
Phase 4 (04): Audio Processing - Depends on Phases 0-3
Phase 5 (05): UI Components - Depends on Phases 0-4
```

### **Phase 5 UI Module Order (CRITICAL)**

```
05a_ui_interaction.jsfx-inc    ← Independent interaction handling
05b_ui_controls.jsfx-inc       ← Control definitions (uses interaction)
05c_ui_rendering.jsfx-inc      ← Pure drawing functions (uses controls)
05e_ui_graph.jsfx-inc          ← Graph rendering (uses rendering functions)
05f_ui_orchestration.jsfx-inc  ← MUST BE LAST - calls ALL other UI functions
```

**⚠️ ORCHESTRATION MUST ALWAYS BE LAST (05f)**
- Orchestration modules call functions from ALL other modules
- They coordinate the complete interface
- Must be imported after all dependencies are defined

### **Within-File Function Order**

Functions must be ordered by dependency within each file:
```jsfx
// ✅ CORRECT
function helper_function() (
  // implementation
);

function main_function() (
  helper_function(); // ✅ helper_function defined above
);

// ❌ WRONG  
function main_function() (
  helper_function(); // ❌ ERROR: helper_function not yet defined
);

function helper_function() (
  // implementation
);
```

## 🚨 CRITICAL: STRING VARIABLE ALLOCATION

### **String Slots 0-49 are RESERVED**

In JSFX, the first 50 string slots (0-49) are reserved for special purposes. **NEVER** use these slots for custom string variables.

```jsfx
// ❌ WRONG - Uses reserved slots
#temp_display_str = "";
#value_str = "";

// ✅ CORRECT - Use slots 50+
#temp_display_str = 50;
#value_str = 51;
```

### **String Variable Declaration**

Always declare string variables in the constants file:
```jsfx
// In 01_Utils/01_constants.jsfx-inc
@init
// === STRING VARIABLES ===
// Use slots 50+ to avoid reserved slots 0-49
#temp_display_str = 50;
#value_str = 51;
```

## 🚨 CRITICAL: SYNTAX RULES

### **No Forward Declarations**

JSFX does not support forward declarations. All functions must be defined before use.

### **Conditional Statements Must Have Content**

Empty conditional branches cause syntax errors:
```jsfx
// ❌ WRONG - Empty else clause
display_mode == DISPLAY_MODE_PERCENT ? (
  sprintf(#value_str, "%s %%", #value_str)
) : (
  // Empty - causes syntax error
);

// ✅ CORRECT - Meaningful content in all branches
display_mode == DISPLAY_MODE_PERCENT ? (
  sprintf(#value_str, "%s %%", #value_str)
) : (
  // No suffix for normal display - value_str already formatted
);
```

### **Dynamic Format Strings**

JSFX `gfx_printf` does not support dynamic format strings. Use two-step sprintf:
```jsfx
// ❌ WRONG - Dynamic format string
gfx_printf("%%.%df%%", decimal_places, value);

// ✅ CORRECT - Two-step sprintf
sprintf(#temp_display_str, "%%.%df%%", decimal_places);
sprintf(#temp_display_str, #temp_display_str, value);
gfx_drawstr(#temp_display_str);
```

### **Function Parameter Passing**

When adding new parameters to functions, update ALL call sites:
```jsfx
// Function definition
function draw_generic_slider(x, y, w, h, value, min_val, max_val, label, slider_type, display_mode, param_index)

// All calls must include the new parameter
draw_generic_slider(x, y, w, h, current_value, min_val, max_val, get_slider_name(param_index), slider_type, display_mode, param_index)
```

## 🚨 CRITICAL: MEMORY MANAGEMENT

### **String Variable Allocation**

- Use slots 50+ for custom strings
- Declare in constants file
- Never use reserved slots 0-49

### **Array Indexing**

- Use 0-based indexing for arrays
- Be careful with `slider_num - 1` conversions
- Avoid double-conversion bugs

## 🚨 CRITICAL: DEBUGGING TIPS

### **Common Syntax Errors**

1. **Empty conditional branches** - Add meaningful comments
2. **Dynamic format strings** - Use two-step sprintf
3. **String slot conflicts** - Use slots 50+
4. **Function order** - Define before calling
5. **Parameter mismatches** - Update all call sites

### **Testing Approach**

1. Use hardcoded values for debugging
2. Test with simple cases first
3. Add complexity gradually
4. Check linter errors immediately

## 🚨 CRITICAL: IMPORT ORDER ENFORCEMENT

### **Main File Import Order**

```jsfx
// 01_Utils: Foundation (no dependencies)
import 01_Utils/01_constants.jsfx-inc
import 01_Utils/02_math_utils.jsfx-inc
// ... rest of 01_Utils

// 02_InputProcessing (depends on 01_Utils)
import 02_InputProcessing/01_dsp_utils.jsfx-inc
// ... rest of 02_InputProcessing

// 03_Compression (depends on 01_Utils, 02_InputProcessing)
import 03_Compression/01_compression_constants.jsfx-inc
// ... rest of 03_Compression

// 04_UI_Rendering (depends on 01_Utils, 03_Compression)
import 04_UI_Rendering/01_helpers.jsfx-inc
// ... rest of 04_UI_Rendering

// 05_UI_UserInteractions (depends on 01_Utils, 04_UI_Rendering)
import 05_UI_UserInteractions/01_control_definitions.jsfx-inc
// ... rest of 05_UI_UserInteractions

// 06_UI_Orchestration (depends on ALL others - MUST BE LAST)
import 06_UI_Orchestration/01_ui_interaction.jsfx-inc
import 06_UI_Orchestration/02_ui_orchestration.jsfx-inc
```

**⚠️ ORCHESTRATION MUST ALWAYS BE LAST**
- It calls functions from ALL other modules
- Must be imported after all dependencies are defined
- Any changes to orchestration order will break the system
