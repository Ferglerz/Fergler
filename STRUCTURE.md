# Composure Modular JSFX - Complete Architecture Documentation

This document provides a comprehensive overview of the modular JSFX compressor architecture, including the UI library and all core modules.

## Overview

The Composure Modular JSFX is a professional multi-algorithm compressor with an interactive graph interface, built using a clean modular architecture. The system is divided into focused modules that handle specific aspects of the compressor's functionality.

## Complete Module Structure

### Core Audio Processing Modules

#### 01_initialization.jsfx-inc
**System Initialization & Memory Management**
- Persistent state variables and constants
- Memory allocation for all processing buffers
- Complete system initialization orchestration
- Graph state management

**Key Functions:**
- `init_constants()` - Mathematical and system constants
- `allocate_memory()` - Memory allocation for all buffers
- `init_state_variables()` - Initialize processing state
- `perform_complete_initialization()` - Master initialization function

**Important Constants:**
- Uses Reaper's built-in `$pi` constant directly throughout the codebase
- All mathematical constants are defined in `init_constants()` function

**Memory Layout:**
- Graph points: 10000+
- Control definitions: 30000+
- Audio processing buffers: Various locations
- State variables: Global scope

#### 02_shared_utilities.jsfx-inc
**Mathematical & Utility Functions**
- Audio processing utilities (dB/linear conversion, clamping)
- Mathematical functions (biquad filters, envelope following)
- Shared helper functions used across modules

**Key Functions:**
- `db_to_linear()` / `linear_to_db()` - Audio level conversion
- `clamp()` - Value constraint functions
- `calc_biquad_*()` - Filter coefficient calculation
- `soft_clip_limiter()` - Limiting functions

#### 03_compression_algorithms.jsfx-inc
**Compression Engine Core**
- Multiple compression algorithms (Clean Digital, Varimu, VCA, etc.)
- Gain reduction calculation
- Compressor character modeling
- Program-dependent release logic

**Key Functions:**
- `calculate_gain_reduction()` - Main GR calculation
- `apply_compressor_character()` - Character modeling
- `process_envelope_following()` - Envelope processing
- Various algorithm-specific functions

#### 04_audio_processing.jsfx-inc
**Audio Processing Pipeline**
- RMS detection and filtering
- Lookahead processing
- Harmonic processing stage
- Final mix and output processing

**Key Functions:**
- `process_rms_detection()` - RMS level detection
- `apply_sidechain_filters()` - Input filtering
- `process_lookahead()` - Lookahead delay processing
- `apply_harmonic_processing()` - Harmonic generation
- `apply_final_mix()` - Wet/dry mixing

### User Interface Modules

#### 05_graph_management.jsfx-inc
**Interactive Graph System**
- Compression curve point management
- Interactive point manipulation (add, delete, move)
- Curve interpolation and sorting
- Mouse interaction for graph editing

**Key Functions:**
- `init_graph_points()` - Initialize curve points
- `add_point()` / `delete_point()` - Point management
- `sort_points()` - Maintain point order
- `find_point_at_mouse()` - Hit testing
- `process_mouse_input()` - Graph interaction

#### 06_graphics_ui.jsfx-inc
**Visual Interface Rendering**
- Graph background and grid rendering
- Compression curve visualization
- Level indicators and meters
- Complete interface orchestration

**Key Functions:**
- `draw_grid()` - Graph grid rendering
- `draw_compression_curves()` - Curve visualization
- `draw_level_indicators()` - Input/output level display
- `draw_gain_reduction_meter()` - GR meter
- `render_complete_interface()` - Main rendering function

### UI Library Modules

## File Structure

### 07_ui_core.jsfx-inc
**Core UI Foundation**
- UI constants and configuration
- Parameter value management functions
- Control label definitions
- UI panel background rendering
- Main UI rendering orchestration

**Key Functions:**
- `init_ui_constants()` - Initialize all UI constants and memory
- `get_param_value()` / `set_param_value()` - Parameter value management
- `get_control_label()` - Control label mapping
- `draw_ui_panel_background()` - Panel background rendering

### 08_ui_controls.jsfx-inc
**Control Definition & Layout**
- Control definition system
- Control property accessors
- Layout management and positioning
- Control initialization

**Key Functions:**
- `define_control()` - Create control definitions
- `get_control_*()` - Property accessors (type, x, y, w, h, param, min, max)
- `setup_control_layout()` - Initialize control positions and properties

### 09_ui_rendering.jsfx-inc
**Control Rendering**
- Generic control rendering
- Individual control drawing functions
- Visual representation of all control types

**Key Functions:**
- `draw_control()` - Main control rendering dispatcher
- `draw_generic_slider()` - Slider rendering
- `draw_generic_button()` - Button rendering
- `draw_generic_dropdown()` - Dropdown rendering
- `render_custom_ui_controls()` - Main UI rendering orchestration

### 10_ui_interaction.jsfx-inc
**Mouse Interaction & Events**
- Mouse input handling
- Control interaction logic
- Event processing and state management

**Key Functions:**
- `handle_ui_mouse_input()` - Main mouse input handler
- `is_point_in_control()` - Hit testing
- `update_slider_value()` - Slider value calculation

## Main Application File

#### Composure_Modular.jsfx
**Main Application Entry Point**
- Slider definitions and parameter management
- Module import orchestration
- Main processing sections (@init, @slider, @gfx, @sample)
- Audio processing pipeline coordination

**Key Sections:**
- **Sliders**: 30 parameters covering all compressor functionality
- **@init**: System initialization and memory setup
- **@slider**: Parameter updates and coefficient calculation
- **@gfx**: Visual interface rendering
- **@sample**: Real-time audio processing

**Slider Variable Naming:**
- `slider1:name` declares the variable name for that slider
- Slider order is correct: slider1=attack_ms, slider2=attack_curve, etc.
- UI parameter system maps parameter indices to these slider variables
- All audio processing uses the correct slider variable names

**Parameter Categories:**
- Basic Controls: Strength, Threshold, Attack, Release, Makeup Gain, Mix
- Advanced Controls: Compressor Type, Sidechain, Filters, RMS settings
- Character Controls: Over-the-top, Harmonic processing, Limiter
- Detection: Feedforward/Feedback modes, Program-dependent release

## Import Order & Dependencies

The modules are imported in strict dependency order:

### Phase 1: Core Foundation
1. `01_initialization.jsfx-inc` - System foundation
2. `02_shared_utilities.jsfx-inc` - Mathematical utilities
3. `03_compression_algorithms.jsfx-inc` - Compression engine
4. `04_audio_processing.jsfx-inc` - Audio processing pipeline

### Phase 2: User Interface
5. `07_ui_core.jsfx-inc` - UI foundation (constants, parameters)
6. `08_ui_controls.jsfx-inc` - Control definitions (depends on core)
7. `09_ui_rendering.jsfx-inc` - Rendering (depends on core + controls)
8. `10_ui_interaction.jsfx-inc` - Interaction (depends on core + controls)

### Phase 3: Integration
9. `05_graph_management.jsfx-inc` - Graph system (depends on UI interaction)
10. `06_graphics_ui.jsfx-inc` - Complete interface (depends on all UI modules)

## Data Flow & Processing Pipeline

### Audio Processing Flow
1. **Input** → Sidechain filtering → RMS detection
2. **Detection** → Gain reduction calculation → Character modeling
3. **Envelope** → Lookahead processing → Harmonic processing
4. **Output** → Final mix → Limiter → Audio output

### User Interface Flow
1. **Mouse Input** → UI interaction handling → Parameter updates
2. **Graph Interaction** → Point manipulation → Curve updates
3. **Visual Rendering** → Background → Controls → Graph → Meters
4. **Parameter Changes** → Slider updates → Real-time processing

## Memory Management

### Memory Layout
- **Graph Points**: 10000+ (compression curve data)
- **Control Definitions**: 30000+ (UI control properties)
- **Audio Buffers**: Various locations (lookahead, RMS, filters)
- **State Variables**: Global scope (envelope, feedback, etc.)

### Memory Allocation Strategy
- Sequential allocation to avoid conflicts
- Persistent variables for state preservation
- Efficient buffer management for real-time processing

## Key Features

### Compression Algorithms
- **Clean Digital**: Transparent, precise compression
- **Varimu**: Variable-mu tube compressor emulation
- **Bridged Diode**: Classic diode bridge compression
- **VCA**: Voltage-controlled amplifier compression
- **PWM/Fairchild**: Pulse-width modulation style
- **FET**: Field-effect transistor compression
- **Optical**: Opto-compressor characteristics

### Advanced Features
- **Interactive Graph**: Click to add/delete curve points
- **Multiple Detection Modes**: Feedforward and feedback
- **Program-Dependent Release**: Adaptive release timing
- **Harmonic Processing**: Dedicated saturation stage
- **Lookahead Processing**: Zero-latency lookahead
- **Soft-Clipping Limiter**: Brickwall limiting with musical character

## Critical Fixes Applied

### Mathematical Constants
- **Uses Reaper's built-in $pi directly**: No need for separate PI variable
- **Direct $pi usage throughout codebase**: Ensures compatibility and accuracy
- **Required for audio processing**: Filter coefficient calculations use $pi directly

### Slider Variable System
- **Slider naming is correct**: `slider1:name` declares variable name
- **UI parameter mapping works**: Maps parameter indices to slider variables
- **Audio processing uses correct variables**: All references use proper slider names

## Benefits

### Architecture Benefits
- **Modularity**: Each file has a single, clear responsibility
- **Maintainability**: Easy to modify specific aspects without affecting others
- **Reusability**: Individual modules can be used in other projects
- **Testability**: Each module can be tested independently
- **Scalability**: Easy to add new control types or interaction patterns

### Performance Benefits
- **Efficient Memory Usage**: Optimized buffer allocation
- **Real-Time Processing**: Low-latency audio processing
- **Smooth UI**: Responsive interface with minimal CPU usage
- **Professional Quality**: Studio-grade compression algorithms

## Usage & Integration

### For Developers
The modular structure makes it easy to:
- Add new compression algorithms in `03_compression_algorithms.jsfx-inc`
- Create new UI controls in the UI library modules
- Extend the graph system in `05_graph_management.jsfx-inc`
- Modify audio processing in `04_audio_processing.jsfx-inc`

### For Users
The interface provides:
- **Intuitive Graph Editing**: Visual compression curve manipulation
- **Professional Controls**: All standard compressor parameters
- **Real-Time Feedback**: Live gain reduction and level monitoring
- **Multiple Characters**: Various compressor emulations

## Entry Points

### Main Functions
- `render_complete_interface()` - Complete UI rendering
- `process_mouse_input()` - Graph interaction handling
- `handle_ui_mouse_input()` - UI control interaction
- `perform_complete_initialization()` - System initialization

### Processing Functions
- `calculate_gain_reduction()` - Main compression calculation
- `process_envelope_following()` - Envelope processing
- `apply_harmonic_processing()` - Harmonic generation
- `apply_final_mix()` - Wet/dry mixing
