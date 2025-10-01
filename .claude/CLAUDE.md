# Claude Index - JSFX Modular Compressor Project

## Project Overview
Advanced Multi-Model Compressor JSFX plugin with modular architecture. Features multiple compression algorithms, interactive graph editing, harmonic processing, and professional audio processing capabilities.

## Architecture

### Modular Design Philosophy
- **Phase-based organization**: Modules are organized in phases 0-5 based on dependency levels
- **Single responsibility**: Each module has one focused purpose
- **No circular dependencies**: Strict dependency hierarchy enforced
- **Centralized memory management**: All memory allocation in `01a_memory.jsfx-inc`

### Phase Organization
- **Phase 0**: Configuration and constants
- **Phase 1**: Foundation (memory, state, initialization, UI config)
- **Phase 2**: Utilities (math, audio, DSP, UI)
- **Phase 3**: Graph system (data, interaction, caching)
- **Phase 4**: Audio processing (compression, harmonics, filters, detection, envelope, effects)
- **Phase 5**: UI components (core, controls, rendering, graph)

## File Structure

### Main Entry Point
- **`Composure_Modular.jsfx`** - Main plugin file with slider definitions, includes, and audio processing pipeline

### Phase 0: Configuration
- **`00a_constants.jsfx-inc`** - All magic numbers, audio constants, performance constants, UI constants

### Phase 1: Foundation
- **`01a_memory.jsfx-inc`** - Memory allocation, layout configuration, buffer management
- **`01b_state.jsfx-inc`** - State variable initialization, audio processing configuration
- **`01c_initialization.jsfx-inc`** - System initialization orchestration and validation
- **`01d_ui_interaction.jsfx-inc`** - Mouse interaction and event handling for UI controls
- **`01e_ui_config.jsfx-inc`** - UI constants, configuration, and layout definitions
- **`01f_debug_logging.jsfx-inc`** - Centralized debug message collection and rendering
- **`01g_file_reading.jsfx-inc`** - Slider definition parsing with robust string handling

### Phase 2: Utilities
- **`02a_math_utils.jsfx-inc`** - Mathematical functions, denormal protection, utility functions
- **`02b_audio_utils.jsfx-inc`** - Audio-specific utilities (dB conversions, level processing)
- **`02c_dsp_utils.jsfx-inc`** - DSP utilities (filter coefficients, envelope processing, lookahead)
- **`02d_ui_utils.jsfx-inc`** - UI utilities, control accessors, graph coordinate functions

### Phase 3: Graph System
- **`03a_graph_data.jsfx-inc`** - Graph point management, serialization, curve mathematics
- **`03b_graph_interaction.jsfx-inc`** - Mouse interaction, point manipulation, graph editing
- **`03c_graph_cache.jsfx-inc`** - Curve calculation caching for performance

### Phase 4: Audio Processing
- **`04a_compression_core.jsfx-inc`** - Core compression logic, character models, curve interpolation
- **`04b_harmonic_models.jsfx-inc`** - Harmonic generation algorithms, character-specific processing
- **`04c_filters.jsfx-inc`** - Filter processing, biquad filters, sidechain filtering
- **`04d_detection.jsfx-inc`** - RMS detection, level processing, gain reduction calculation
- **`04e_envelope.jsfx-inc`** - Envelope following, program-dependent release algorithms
- **`04f_effects.jsfx-inc`** - Lookahead processing, harmonic processing, final mix
- **`04g_parameter_smoothing.jsfx-inc`** - Parameter smoothing to prevent zipper noise

### Phase 5: UI Components
- **`05a_ui_core.jsfx-inc`** - Basic UI core utilities and panel rendering
- **`05b_ui_controls.jsfx-inc`** - Control definition system and layout management
- **`05c_ui_rendering.jsfx-inc`** - Control rendering and drawing functions
- **`05e_ui_graph.jsfx-inc`** - Graph display, compression curves, interactive elements

## Key Features

### Compression Algorithms
- **Clean Digital**: No character modifications
- **Varimu**: Tube-like saturation and release characteristics
- **Bridged Diode**: Fast attack, complex release behavior
- **VCA**: Voltage-controlled amplifier characteristics
- **PWM/Fairchild**: Multi-stage release with program dependency
- **FET**: 1176-like transient detection and response
- **Optical**: LA-2A-like smooth response

### Interactive Graph System
- **Point-based editing**: Add, move, delete compression curve points
- **Bezier curves**: Smooth curve interpolation between points
- **Real-time visualization**: Live compression curve display
- **Serialization**: Graph state persists across plugin instances

### Advanced Features
- **Program-dependent release**: Adaptive release based on input characteristics
- **RMS normalization**: Automatic level compensation
- **Harmonic processing**: Tube, tape, and digital harmonic generation
- **Lookahead processing**: Zero-latency peak detection
- **Soft-clipping limiter**: Inter-sample peak protection

## Memory Layout

### Memory Address Ranges
- **Graph Points**: 10000+ (compression curve data)
- **Control Definitions**: 30000+ (UI control properties)
- **Audio Buffers**: 40000+ (lookahead, RMS buffers)
- **Debug Messages**: 5000-5099 (string slots)
- **Slider Names**: 100-199 (parameter labels)
- **Dropdown Options**: 200-1999 (menu choices)

### Key Memory Variables
- `graph_points`: Compression curve point coordinates
- `curve_amounts`: Bezier curve intensity per point
- `control_defs`: UI control definitions array
- `lookahead_buffer_l/r`: Lookahead delay buffers
- `rms_buffer`: RMS calculation buffer

## Audio Processing Pipeline

### Signal Flow
1. **Input Stage**: Cache original signals, determine channel configuration
2. **Detection Source**: Select feedforward/feedback mode, sidechain routing
3. **Sidechain Filtering**: High-pass and low-pass filtering of detection signal
4. **RMS Detection**: Level calculation with optional normalization
5. **Gain Reduction**: Apply compression curve with global offset
6. **Character Application**: Model-specific compression behavior
7. **Envelope Following**: Attack/release with program-dependent release
8. **Lookahead Processing**: Delay compensation for peak detection
9. **Harmonic Processing**: Optional harmonic generation and saturation
10. **Final Mix**: Output routing with limiter protection

### Performance Optimizations
- **Block processing**: Use @block instead of @sample when possible
- **Curve caching**: Pre-calculate compression curves
- **Parameter smoothing**: Prevent zipper noise from parameter changes
- **Denormal protection**: Prevent CPU spikes from denormalized numbers

## UI System

### Control Types
- **Sliders**: Continuous parameter adjustment
- **Buttons**: Toggle parameters (on/off)
- **Dropdowns**: Discrete value selection

### Graph Interaction
- **Left-click empty**: Add new curve point
- **Left-click point**: Select and drag to move
- **Right-click/Alt+click point**: Delete point
- **Cmd+drag point**: Adjust bezier curve amount
- **Hover**: Visual feedback and point highlighting

### Layout System
- **4-column layout**: Organized by parameter type
- **Column 1**: Time-related parameters
- **Column 2**: RMS & Detection, Filtering
- **Column 3**: Character & Harmonics
- **Column 4**: Global parameters

## Development Guidelines

### Adding New Features
1. **Determine phase**: Identify appropriate dependency level
2. **Create module**: Follow naming convention `[phase][letter]_[descriptive_name].jsfx-inc`
3. **Update includes**: Add import statement in main file
4. **Memory allocation**: Use centralized memory management
5. **No circular dependencies**: Only depend on lower-phase modules

### Debugging
- **Debug logging**: Use functions from `01f_debug_logging.jsfx-inc`
- **Memory validation**: Check memory layout with validation functions
- **State inspection**: Use state management functions for troubleshooting

### Performance Considerations
- **Memory efficiency**: Use lowest possible memory indices
- **CPU optimization**: Cache expensive calculations
- **Denormal protection**: Prevent CPU spikes
- **Parameter smoothing**: Avoid audio artifacts from parameter changes

## Common Functions

### Memory Management
- `allocate_memory()`: Allocate all memory buffers
- `validate_memory_layout()`: Verify memory allocation
- `get_memory_usage()`: Get total memory usage

### Graph System
- `interpolate_compression_curve(input_db)`: Get compression curve output
- `add_point(input_db, output_db)`: Add new curve point
- `delete_point(point_index)`: Remove curve point
- `set_curve_amount(point_index, amount)`: Set bezier curve intensity

### Audio Processing
- `apply_compressor_character(gr, type, input, dt, intensity)`: Apply character model
- `process_envelope_following(target_gr_db, detector_level)`: Envelope processing
- `apply_harmonic_processing(input, gr_amount, ...)`: Harmonic generation

### UI System
- `render_complete_interface()`: Render entire UI
- `process_mouse_input()`: Handle mouse interactions
- `draw_control(index)`: Render individual control

This index provides a comprehensive overview of the codebase structure, key features, and development guidelines for the JSFX modular compressor project.
