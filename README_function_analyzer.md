# JSFX Function Declaration and Call Analyzer

A Python script that analyzes JSFX modular codebases to detect undeclared function calls by respecting the import dependency order.

## Features

- **Dependency Resolution**: Automatically resolves import dependencies using topological sorting
- **Phase-Based Architecture**: Respects JSFX modular architecture with phase-based imports (0-5)
- **Circular Dependency Detection**: Warns about circular dependencies in the import graph
- **Built-in Function Filtering**: Filters out JSFX built-in functions, variables, and constants
- **Detailed Reporting**: Provides comprehensive reports of undeclared function calls
- **File Support**: Works with both `.jsfx-inc` and `.jsfx` files

## Usage

```bash
# Analyze current directory
python3 function_analyzer.py .

# Analyze specific directory
python3 function_analyzer.py /path/to/jsfx/modules
```

## Example Output

```
SUMMARY:
  Modules analyzed: 27
  Total function declarations: 190
  Total function calls: 121
  Undeclared function calls: 56

⚠️  WARNING: Found 56 undeclared function calls:

  03b_graph_interaction.jsfx-inc:
    - add_point
    - delete_point
    - graph_x_to_db
    - graph_y_to_db
    - handle_ui_mouse_input
    - invalidate_curve_cache
    - remove_displaced_points
    - set_curve_amount
    - sort_points
```

## How It Works

1. **Loads Modules**: Scans directory for `.jsfx-inc` and `.jsfx` files
2. **Parses Imports**: Extracts import statements from each module
3. **Resolves Dependencies**: Builds dependency graph and determines processing order
4. **Finds Functions**: Identifies function declarations and calls in each module
5. **Validates Calls**: Checks if function calls have corresponding declarations in dependency order
6. **Generates Report**: Provides detailed analysis of undeclared function calls

## JSFX Modular Architecture Rules

The analyzer enforces the JSFX modular architecture:

- **Phase 0**: Configuration (constants, config)
- **Phase 1**: Foundation (memory, state, initialization, UI config)
- **Phase 2**: Utilities (math, audio, DSP, UI utilities)
- **Phase 3**: Graph system (data, interaction, caching)
- **Phase 4**: Audio processing (compression, harmonics, filters, etc.)
- **Phase 5**: UI components (core, controls, rendering, graph)

### Key Principles

- Modules must be imported in strict dependency order
- No circular dependencies allowed
- Function declarations must precede function calls in dependency order
- Each module has a single focused responsibility

## Built-in Functions Filtered

The analyzer automatically filters out JSFX built-in functions including:

- Mathematical functions: `abs`, `min`, `max`, `floor`, `ceil`, `exp`, `log`, etc.
- Memory functions: `memcpy`, `memset`, `freemem`, `freembuf`
- Graphics functions: `gfx_drawstr`, `gfx_printf`, `gfx_line`, etc.
- File I/O functions: `file_var`, `file_read`, `file_write`, etc.
- System variables: `srate`, `samplesblock`, `spl0`, `spl1`, etc.
- Slider variables: `slider1` through `slider64`
- Mouse variables: `mouse_x`, `mouse_y`, `mouse_cap`
- Constants: `$pi`, `$e`, `$phi`, `$tau`

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library)

## Error Handling

The analyzer handles various edge cases:

- Circular dependencies in imports
- Missing import files
- Malformed function declarations
- Comment lines and inline comments
- Variable assignments vs function calls

## Use Cases

- **Code Quality**: Ensure all function calls have proper declarations
- **Refactoring**: Verify function dependencies when restructuring code
- **Documentation**: Understand function call patterns across modules
- **Debugging**: Find missing function declarations quickly
- **Maintenance**: Keep track of function dependencies as code evolves
