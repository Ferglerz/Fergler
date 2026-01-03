# Flattery Engine Library

The Flattery Engine is a modular library for frequency-domain audio leveling based on adjacent FFT bins. The engine functions accept parameter arrays instead of reading sliders directly, making it reusable in any JSFX script.

## Usage

### Basic Setup

1. Import the engine library:
```jsfx
import Flattery Engine/flattery_engine.jsfx-inc
```

2. Allocate a parameter array:
```jsfx
@init
  // Allocate parameter array (SFF_PARAM_COUNT elements)
  sff_params_array = 100000;  // Use high index to avoid conflicts
```

3. Initialize parameters from your sliders (or any source):
```jsfx
  // Set parameters in the array
  sff_params_array[SFF_PARAM_STRENGTH] = 35;
  sff_params_array[SFF_PARAM_FFT_SIZE_SEL] = 2;
  // ... set all parameters
  
  // Or use the helper function if you have sliders:
  sff_params_from_sliders(sff_params_array);
```

4. Initialize the engine:
```jsfx
  flattery_init(sff_params_array);
```

### Processing Audio

In your `@sample` section:
```jsfx
@sample
  flattery_process_sample();
  // spl0 and spl1 are automatically processed
```

### Updating Parameters

When parameters change (in `@slider` section):
```jsfx
@slider
  // Update parameter array
  sff_params_from_sliders(sff_params_array);
  
  // Update engine
  flattery_update_params(sff_params_array);
```

### Block Updates

In your `@block` section:
```jsfx
@block
  flattery_update_block();
```

### Rendering UI

In your `@gfx` section:
```jsfx
@gfx 900 260
  // Render using current engine parameters
  flattery_render_ui(0);
  
  // Or render with different parameters (for preview)
  flattery_render_ui(preview_params_array);
```

## Parameter Array Structure

The parameter array uses indices defined in `01_Utils/01_parameters.jsfx-inc`:

- `SFF_PARAM_FFT_SIZE_SEL` - FFT size selection (0-6)
- `SFF_PARAM_STRENGTH` - Strength (0-200)
- `SFF_PARAM_MAX_BOOST_DB` - Maximum boost in dB
- `SFF_PARAM_MAX_CUT_DB` - Maximum cut in dB
- `SFF_PARAM_WET` - Wet mix (0-100)
- `SFF_PARAM_OUTPUT_GAIN_DB` - Output gain in dB
- ... and many more (see `01_parameters.jsfx-inc` for full list)

Use helper functions like `sff_param_get_strength(params_base)` to read parameters, or access directly via `params_base[SFF_PARAM_STRENGTH]`.

## Architecture

The engine is organized into phases:

- **Phase 0**: Parameters, Constants, Math Utils
- **Phase 1**: FFT and Memory Management
- **Phase 2**: Audio Processing (STFT, filtering, gain application)
- **Phase 3**: UI Rendering
- **Phase 4**: Engine API (main entry point)

All processing functions use a parameter synchronization system that reads from the parameter array and sets global variables that the existing processing code expects. This allows the engine to work without requiring a full refactor of all processing functions.

## Example: Custom Plugin

```jsfx
desc:My Custom Flattery Plugin

// Your sliders
slider1:my_strength=50<0,200,1>Strength

// Import engine
import ../Flattery Engine/flattery_engine.jsfx-inc

@init
  // Allocate parameter array
  sff_params_array = 100000;
  
  // Set custom parameters
  sff_params_array[SFF_PARAM_STRENGTH] = my_strength;
  sff_params_array[SFF_PARAM_FFT_SIZE_SEL] = 2;
  // ... set other required parameters
  
  // Initialize engine
  flattery_init(sff_params_array);

@slider
  // Update parameters
  sff_params_array[SFF_PARAM_STRENGTH] = my_strength;
  flattery_update_params(sff_params_array);

@block
  flattery_update_block();

@sample
  flattery_process_sample();

@gfx 900 260
  flattery_render_ui(0);
```

## Notes

- The engine manages its own memory allocation internally
- PDC (Plugin Delay Compensation) is handled automatically
- All functions are parameterized - no direct slider access in engine code
- UI can render with different parameters than the engine is using (for previews)

