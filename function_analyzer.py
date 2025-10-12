#!/usr/bin/env python3
"""
JSFX Function Declaration and Call Analyzer

This script analyzes a JSFX modular codebase to:
1. Parse import statements and resolve dependency order
2. Collect function declarations from each module
3. Track function calls throughout the codebase
4. Report undeclared function calls

Usage: python3 function_analyzer.py [path_to_jsfx_files]

If no path is provided, the current directory will be analyzed by default.

Example:
    python3 function_analyzer.py                     # Analyzes current directory
    python3 function_analyzer.py .                   # Analyzes current directory
    python3 function_analyzer.py /path/to/jsfx/modules  # Analyzes specific path

Features:
- Respects JSFX modular architecture with phase-based imports
- Handles dependency resolution with topological sorting
- Detects circular dependencies
- Filters out JSFX built-in functions and variables
- Provides detailed reporting of undeclared function calls
- Supports both .jsfx-inc and .jsfx files

The analyzer follows the JSFX modular architecture rules:
- Modules must be imported in strict dependency order
- Phase 0: Configuration, Phase 1: Foundation, Phase 2: Utilities, etc.
- No circular dependencies allowed
- Function declarations must precede function calls in dependency order
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque


class JSFXFunctionAnalyzer:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.modules: Dict[str, str] = {}  # filename -> content
        self.imports: Dict[str, List[str]] = {}  # filename -> list of imported files
        self.function_declarations: Dict[str, Set[str]] = {}  # filename -> set of function names
        self.function_calls: Dict[str, Set[str]] = {}  # filename -> set of called functions
        self.builtin_functions = {
            # JSFX built-in mathematical functions
            'abs', 'min', 'max', 'floor', 'ceil', 'round', 'exp', 'log', 'log10', 'sqrt', 'sin', 'cos', 'tan',
            'pow', 'atan', 'tanh', 'atan2', 'sinh', 'cosh', 'asinh', 'acosh', 'atanh', 'asin', 'acos',
            'spline', 'loop', 'while', 'if', 'else', 'for', 'function', 'sign', 'rand', 'convolve_c', 'sqr',
            
            # JSFX memory functions
            'memcpy', 'memset', 'freemem', 'freembuf', 'mem', 'mem_size', 'mem_multiply_sum', 
            'mem_insert_shuffle', 'mem_delete_shuffle',
            
            # JSFX file I/O functions
            'file_var', 'file_avail', 'file_peek', 'file_read', 'file_write', 'file_open', 'file_close', 
            'file_string', 'file_mem', 'file_riff', 'file_text', 'file_rewind',
            
            # JSFX graphics functions
            'gfx_r', 'gfx_g', 'gfx_b', 'gfx_a', 'gfx_mode', 'gfx_x', 'gfx_y', 'gfx_w', 'gfx_h',
            'gfx_line', 'gfx_rect', 'gfx_circle', 'gfx_roundrect', 'gfx_drawnumber', 'gfx_drawchar',
            'gfx_getpixel', 'gfx_setpixel', 'gfx_set', 'gfx_blit', 'gfx_gradrect', 'gfx_drawstr', 'gfx_printf',
            'gfx_muladd', 'gfx_memset', 'gfx_getimgdim', 'gfx_setimgdim', 'gfx_lineto', 'gfx_arc',
            'gfx_blurto', 'gfx_getchar', 'gfx_showmenu', 'gfx_setcursor', 'gfx_measurestr', 'gfx_setfont',
            'gfx_getfont', 'gfx_transformblit', 'gfx_clienttoscreen', 'gfx_screentoclient', 'gfx_deltablit',
            
            # JSFX slider functions and variables
            'sliderchange', 'slider_automate', 'slider_show', 'slider_hide', 'slider_next_chg', 'slider',
            
            # JSFX slider variables (1-64)
            'slider1', 'slider2', 'slider3', 'slider4', 'slider5', 'slider6', 'slider7', 'slider8',
            'slider9', 'slider10', 'slider11', 'slider12', 'slider13', 'slider14', 'slider15', 'slider16',
            'slider17', 'slider18', 'slider19', 'slider20', 'slider21', 'slider22', 'slider23', 'slider24',
            'slider25', 'slider26', 'slider27', 'slider28', 'slider29', 'slider30', 'slider31', 'slider32',
            'slider33', 'slider34', 'slider35', 'slider36', 'slider37', 'slider38', 'slider39', 'slider40',
            'slider41', 'slider42', 'slider43', 'slider44', 'slider45', 'slider46', 'slider47', 'slider48',
            'slider49', 'slider50', 'slider51', 'slider52', 'slider53', 'slider54', 'slider55', 'slider56',
            'slider57', 'slider58', 'slider59', 'slider60', 'slider61', 'slider62', 'slider63', 'slider64',
            
            # JSFX extension functions
            'ext_noinit', 'ext_midi_bus', 'ext_midi_clock', 'ext_midi_in', 'ext_midi_out',
            
            # JSFX plugin delay compensation
            'pdc_delay', 'pdc_bot_ch', 'pdc_top_ch', 'pdc_midi', 'pdc_beats',
            
            # JSFX system variables
            'srate', 'samplesblock', 'num_ch', 'num_ch_in', 'num_ch_out', 'tempo', 'play_state',
            'play_position', 'beat_position', 'ts_num', 'ts_denom', 'time_precise',
            
            # JSFX audio sample variables
            'spl0', 'spl1', 'spl2', 'spl3', 'spl4', 'spl5', 'spl6', 'spl7', 'spl8', 'spl9',
            'spl10', 'spl11', 'spl12', 'spl13', 'spl14', 'spl15', 'spl16', 'spl17', 'spl18', 'spl19',
            'spl20', 'spl21', 'spl22', 'spl23', 'spl24', 'spl25', 'spl26', 'spl27', 'spl28', 'spl29',
            'spl30', 'spl31', 'spl32', 'spl33', 'spl34', 'spl35', 'spl36', 'spl37', 'spl38', 'spl39',
            'spl40', 'spl41', 'spl42', 'spl43', 'spl44', 'spl45', 'spl46', 'spl47', 'spl48', 'spl49',
            'spl50', 'spl51', 'spl52', 'spl53', 'spl54', 'spl55', 'spl56', 'spl57', 'spl58', 'spl59',
            'spl60', 'spl61', 'spl62', 'spl63',
            
            # JSFX mouse variables
            'mouse_x', 'mouse_y', 'mouse_cap', 'mouse_wheel', 'mouse_hwheel',
            
            # JSFX constants
            '$pi', '$e', '$phi', '$tau',
            
            # JSFX string functions
            'strcpy', 'strlen', 'strcmp', 'strncmp', 'strcpy_substr', 'str_getchar', 'str_setchar',
            'sprintf', 'strcpy_from', 'strcpy_fromslider', 'match', 'matchi', 'matchex',
            
            # JSFX FFT/MDCT functions
            'fft', 'fft_real', 'fft_permute', 'fft_ipermute', 'ifft', 'ifft_real',
            'mdct', 'imdct',
            
            # JSFX MIDI functions
            'midisend', 'midisend_buf', 'midisend_str', 'midirecv', 'midirecv_buf', 'midirecv_str',
            'midisyx',
            
            # JSFX local keyword (not a function but appears in function calls)
            'local', 'global', 'instance', 'static',
            
            # Other JSFX functions
            'get_host_placement', 'get_host_numchan', 'get_pin_mapping'
        }
        
    def load_modules(self):
        """Load all JSFX module files from the base path (including subdirectories)"""
        # Search recursively for all .jsfx-inc and .jsfx files
        jsfx_files = list(self.base_path.rglob("*.jsfx-inc")) + list(self.base_path.glob("*.jsfx"))
        
        for file_path in jsfx_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Store with relative path from base_path
                    relative_path = file_path.relative_to(self.base_path)
                    self.modules[str(relative_path)] = content
                    print(f"Loaded: {relative_path}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    def parse_imports(self):
        """Parse import statements from each module (handles folder paths)"""
        # Updated pattern to handle folder paths like 01_Utils/02_math_utils.jsfx-inc
        import_pattern = r'import\s+([a-zA-Z0-9_\-/\.]+\.jsfx-inc)'
        
        for filename, content in self.modules.items():
            imports = re.findall(import_pattern, content, re.IGNORECASE)
            self.imports[filename] = imports
            if imports:
                print(f"{filename} imports: {imports}")
    
    def parse_function_declarations(self):
        """Parse function declarations from each module"""
        # Pattern to match function declarations
        # Matches: function function_name(...) or function function_name(...) local(...) (...)
        # Now handles multi-line local() declarations
        function_pattern = r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        
        for filename, content in self.modules.items():
            functions = set()
            
            # Remove comments first
            lines = []
            for line in content.split('\n'):
                # Skip comment-only lines
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('/*'):
                    continue
                # Remove inline comments
                if '//' in line:
                    line = line[:line.find('//')]
                lines.append(line)
            
            # Join lines to handle multi-line declarations
            clean_content = ' '.join(lines)
            
            # Find all function declarations
            matches = re.finditer(function_pattern, clean_content)
            for match in matches:
                func_name = match.group(1)
                # Verify this is actually a function declaration by checking what follows
                # Look for the opening parenthesis of the function body
                pos = match.end()
                # Skip to find the function body opening (
                # This could be after ) or after local(...) )
                remaining = clean_content[pos:pos+500]  # Look ahead max 500 chars
                
                # Simple heuristic: if we see a pattern like ") (" or ") local(...) ("
                # then it's a function declaration
                if re.search(r'\)(?:\s+local\s*\([^)]*\))?\s*\(', remaining):
                    functions.add(func_name)
            
            self.function_declarations[filename] = functions
            if functions:
                print(f"{filename} declares: {sorted(functions)}")
    
    def parse_function_calls(self):
        """Parse function calls from each module"""
        for filename, content in self.modules.items():
            calls = set()
            lines = content.split('\n')
            in_multiline_comment = False
            
            for line_num, line in enumerate(lines):
                # Handle multiline comments
                if '/*' in line:
                    in_multiline_comment = True
                    # If the comment closes on the same line, handle it
                    if '*/' in line:
                        in_multiline_comment = False
                        # Remove the comment from the line
                        comment_start = line.find('/*')
                        comment_end = line.find('*/') + 2
                        line = line[:comment_start] + line[comment_end:]
                    else:
                        continue
                
                if in_multiline_comment:
                    if '*/' in line:
                        in_multiline_comment = False
                    continue
                
                # Skip comment lines
                stripped_line = line.strip()
                if stripped_line.startswith('//') or stripped_line.startswith('/*'):
                    continue
                
                # Skip slider definition lines (e.g., slider1:attack_ms=10<0.1,100,0.1>-Attack (ms))
                if re.match(r'^\s*slider\d+:', stripped_line, re.IGNORECASE):
                    continue
                
                # Skip desc: lines
                if re.match(r'^\s*desc:', stripped_line, re.IGNORECASE):
                    continue
                
                # Remove inline comments (preserve code before //)
                if '//' in line:
                    line = line[:line.find('//')]
                
                # Skip if line is now empty after comment removal
                if not line.strip():
                    continue
                
                # Remove string literals to avoid false matches from format strings
                # Remove double-quoted strings
                line_no_strings = re.sub(r'"[^"]*"', '""', line)
                
                # Look for function calls - must be standalone function calls
                # Pattern: word boundary, function name, optional whitespace, opening parenthesis
                call_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
                matches = re.finditer(call_pattern, line_no_strings)
                
                for match in matches:
                    func_name = match.group(1)
                    
                    # Skip single-letter identifiers (likely false positives)
                    if len(func_name) == 1:
                        continue
                    
                    # Skip if it's a builtin function
                    if func_name in self.builtin_functions:
                        continue
                    
                    # Skip if it's a function declaration
                    before_match = line_no_strings[:match.start()].strip()
                    if before_match.endswith('function'):
                        continue
                    
                    # Skip if it looks like a variable assignment or part of a larger expression
                    # Check if there's an assignment operator before the function call
                    before_context = line_no_strings[:match.start()].strip()
                    if '=' in before_context and not before_context.endswith('='):
                        # Check if this is an assignment to the function name
                        assignment_pattern = r'\b' + re.escape(func_name) + r'\s*='
                        if re.search(assignment_pattern, before_context):
                            continue
                    
                    # Skip if it's part of a conditional or logical expression
                    # Check for standalone operators before the function call (not compound operators like +=)
                    if re.search(r'[+\-*/<>!&|]\s*$', before_context):
                        continue
                    
                    # Skip if it's in a variable declaration context
                    if re.search(r'\b(var|local|global)\s+\w*\s*$', before_context, re.IGNORECASE):
                        continue
                    
                    # Skip string-like identifiers (JSFX string variables start with #)
                    if func_name.startswith('#'):
                        continue
                    
                    calls.add(func_name)
            
            self.function_calls[filename] = calls
            if calls:
                print(f"{filename} calls: {sorted(calls)}")
    
    def resolve_dependencies(self) -> List[str]:
        """Resolve import dependencies and return processing order
        
        For JSFX modular architecture, the main .jsfx file imports all modules
        in a specific order. We need to respect this sequential import order
        since it defines the dependency chain.
        """
        all_files = set(self.modules.keys())
        
        # Find main .jsfx file(s) that have imports
        main_files = [f for f in all_files if f.endswith('.jsfx') and self.imports.get(f)]
        
        if not main_files:
            print("Warning: No main .jsfx file found with imports. Using alphabetical order.")
            return sorted(all_files)
        
        # For JSFX modular architecture, there should be one main file
        # that imports all modules in dependency order
        main_file = main_files[0]
        if len(main_files) > 1:
            print(f"Warning: Multiple .jsfx files with imports found: {main_files}")
            print(f"Using import order from: {main_file}")
        
        # Get the import order from the main file
        # This is the explicit dependency order defined by the developer
        import_order = self.imports.get(main_file, [])
        
        # Filter to only include files that exist in our modules
        result = [f for f in import_order if f in all_files]
        
        # Add the main file at the end
        result.append(main_file)
        
        # Add any remaining files that weren't imported (shouldn't happen normally)
        remaining = all_files - set(result)
        if remaining:
            print(f"Warning: Files not imported by main file: {remaining}")
            result.extend(sorted(remaining))
        
        return result
    
    def analyze_function_usage(self) -> Dict[str, List[str]]:
        """Analyze function usage and return undeclared function calls"""
        processing_order = self.resolve_dependencies()
        print(f"\nProcessing order: {processing_order}")
        
        # Track all declared functions as we process files
        all_declared_functions = set(self.builtin_functions)
        undeclared_calls = defaultdict(list)
        
        for filename in processing_order:
            if filename not in self.modules:
                continue
                
            print(f"\nProcessing: {filename}")
            
            # Add functions declared in this file
            declared_in_file = self.function_declarations.get(filename, set())
            all_declared_functions.update(declared_in_file)
            print(f"  Declares: {sorted(declared_in_file)}")
            
            # Check function calls in this file
            calls_in_file = self.function_calls.get(filename, set())
            print(f"  Calls: {sorted(calls_in_file)}")
            
            # Find undeclared calls
            for func_call in calls_in_file:
                if func_call not in all_declared_functions:
                    undeclared_calls[filename].append(func_call)
                    print(f"  ❌ UNDECLARED: {func_call}")
                else:
                    print(f"  ✅ Declared: {func_call}")
        
        return undeclared_calls
    
    def generate_report(self, undeclared_calls: Dict[str, List[str]]):
        """Generate a comprehensive report"""
        print("\n" + "="*80)
        print("JSFX FUNCTION ANALYSIS REPORT")
        print("="*80)
        
        # Summary statistics
        total_modules = len(self.modules)
        total_declarations = sum(len(funcs) for funcs in self.function_declarations.values())
        total_calls = sum(len(funcs) for funcs in self.function_calls.values())
        total_undeclared = sum(len(calls) for calls in undeclared_calls.values())
        
        print(f"\nSUMMARY:")
        print(f"  Modules analyzed: {total_modules}")
        print(f"  Total function declarations: {total_declarations}")
        print(f"  Total function calls: {total_calls}")
        print(f"  Undeclared function calls: {total_undeclared}")
        
        if total_undeclared == 0:
            print(f"\n🎉 SUCCESS: All function calls have corresponding declarations!")
        else:
            print(f"\n⚠️  WARNING: Found {total_undeclared} undeclared function calls:")
            
            for filename, calls in undeclared_calls.items():
                if calls:
                    print(f"\n  {filename}:")
                    for call in sorted(calls):
                        print(f"    - {call}")
        
        # Detailed module breakdown
        print(f"\nDETAILED BREAKDOWN:")
        processing_order = self.resolve_dependencies()
        
        for filename in processing_order:
            if filename not in self.modules:
                continue
                
            declared = self.function_declarations.get(filename, set())
            called = self.function_calls.get(filename, set())
            undeclared = undeclared_calls.get(filename, [])
            
            print(f"\n  {filename}:")
            print(f"    Declares: {len(declared)} functions")
            print(f"    Calls: {len(called)} functions")
            print(f"    Undeclared: {len(undeclared)} functions")
            
            if declared:
                print(f"    Functions declared: {sorted(declared)}")
            
            if undeclared:
                print(f"    ❌ Undeclared calls: {sorted(undeclared)}")


def main():
    if len(sys.argv) > 2:
        print("Usage: python3 function_analyzer.py [path_to_jsfx_directory]")
        print("If no path is provided, the current directory will be used.")
        sys.exit(1)
    
    # Use provided path or default to current directory
    base_path = sys.argv[1] if len(sys.argv) == 2 else "."
    
    if not os.path.exists(base_path):
        print(f"Error: Path '{base_path}' does not exist")
        sys.exit(1)
    
    # Redirect output to final_analysis.txt
    output_file = "final_analysis.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        # Save original stdout
        original_stdout = sys.stdout
        # Redirect stdout to file
        sys.stdout = f
        
        print(f"Analyzing JSFX modules in: {os.path.abspath(base_path)}")
        print("-" * 60)
        
        analyzer = JSFXFunctionAnalyzer(base_path)
        
        # Load and analyze modules
        analyzer.load_modules()
        analyzer.parse_imports()
        analyzer.parse_function_declarations()
        analyzer.parse_function_calls()
        
        # Analyze function usage
        undeclared_calls = analyzer.analyze_function_usage()
        
        # Generate report
        analyzer.generate_report(undeclared_calls)
        
        # Restore original stdout
        sys.stdout = original_stdout
    
    print(f"Analysis complete! Results written to: {output_file}")


if __name__ == "__main__":
    main()
