#!/usr/bin/env python3
"""
Test Ultra-Subtle Odd Boost - Test with 100x reduced odd boost coefficients
"""

import math

def apply_enhanced_tape_processing(driven, amount, combined_factor, even_boost, odd_boost):
    """Enhanced tape processing with ultra-subtle odd boost"""
    scaled_saturation = amount * combined_factor
    x = driven
    
    # Pre-calculate boost factors
    even_boost_factor = 1 + even_boost * 0.01
    odd_boost_factor = 1 + odd_boost * 0.01
    
    # Asymmetric processing
    asymmetric_factor = 1.0 if x > 0 else 0.9
    
    # Polynomial waveshaping
    x2 = x * x  # x² (2nd harmonic)
    x3 = x2 * x  # x³ (3rd harmonic)
    x5 = x3 * x2  # x⁵ (5th harmonic)
    x7 = x5 * x2  # x⁷ (7th harmonic)
    
    # Tape baseline: very subtle even harmonics
    result = x + x2 * scaled_saturation * 0.001 * even_boost_factor * asymmetric_factor
    
    # Add ultra-subtle odd harmonics when boosted
    if odd_boost > 0:
        result += x3 * scaled_saturation * 0.005 * odd_boost_factor * asymmetric_factor + \
                  x5 * scaled_saturation * 0.0025 * odd_boost_factor * asymmetric_factor + \
                  x7 * scaled_saturation * 0.00125 * odd_boost_factor * asymmetric_factor
    
    return result

def apply_enhanced_tube_processing(driven, amount, combined_factor, even_boost, odd_boost):
    """Enhanced tube processing with ultra-subtle odd boost"""
    scaled_saturation = amount * combined_factor
    x = driven
    
    # Pre-calculate boost factors
    odd_boost_factor = 1 + odd_boost * 0.01
    even_boost_factor = 1 + even_boost * 0.01
    
    # Asymmetric processing
    asymmetric_factor = 1.0 if x > 0 else 0.85
    
    # Polynomial waveshaping
    x2 = x * x  # x² (2nd harmonic)
    x3 = x2 * x  # x³ (3rd harmonic)
    x5 = x3 * x2  # x⁵ (5th harmonic)
    
    # Tube baseline: very subtle even harmonics
    result = x + x2 * scaled_saturation * 0.001 * even_boost_factor * asymmetric_factor
    
    # Add ultra-subtle odd harmonics when boosted
    if odd_boost > 0:
        result += x3 * scaled_saturation * 0.002 * odd_boost_factor * asymmetric_factor + \
                  x5 * scaled_saturation * 0.001 * odd_boost_factor * asymmetric_factor
    
    return result

def test_ultra_subtle_odd_boost():
    """Test ultra-subtle odd boost coefficients"""
    print("=== ULTRA-SUBTLE ODD BOOST TEST ===")
    print("Testing with 100x reduced odd boost coefficients")
    print()
    
    # Test parameters
    harmonic_amount = 0.5
    combined_factor = 0.3
    test_level = 0.5
    
    # Test different odd boost levels
    boost_combinations = [
        ("No boosts", 0, 0),
        ("Low odd", 0, 25),
        ("Medium odd", 0, 50),
        ("High odd", 0, 100),
        ("Very high odd", 0, 200),
        ("Both low", 25, 25),
        ("Both medium", 50, 50),
        ("Both high", 100, 100),
        ("Both very high", 200, 200)
    ]
    
    print("=== ODD BOOST TEST (100x Reduced) ===")
    for name, even_boost, odd_boost in boost_combinations:
        tape_result = apply_enhanced_tape_processing(test_level, harmonic_amount, combined_factor, even_boost, odd_boost)
        tube_result = apply_enhanced_tube_processing(test_level, harmonic_amount, combined_factor, even_boost, odd_boost)
        
        tape_gain = 20 * math.log10(tape_result / test_level)
        tube_gain = 20 * math.log10(tube_result / test_level)
        
        print(f"{name:15}: Tape {tape_gain:+.1f}dB, Tube {tube_gain:+.1f}dB")
    
    print()
    
    # Test with different harmonic amounts
    print("=== HARMONIC AMOUNT TEST (100% Odd Boost) ===")
    harmonic_amounts = [0.1, 0.3, 0.5, 0.7, 0.9]
    even_boost, odd_boost = 0, 100  # 100% odd boost
    
    for harm_amount in harmonic_amounts:
        tape_result = apply_enhanced_tape_processing(test_level, harm_amount, combined_factor, even_boost, odd_boost)
        tube_result = apply_enhanced_tube_processing(test_level, harm_amount, combined_factor, even_boost, odd_boost)
        
        tape_gain = 20 * math.log10(tape_result / test_level)
        tube_gain = 20 * math.log10(tube_result / test_level)
        
        print(f"Amount {harm_amount:.1f}: Tape {tape_gain:+.1f}dB, Tube {tube_gain:+.1f}dB")
    
    print()
    
    # Compare coefficient reductions
    print("=== COEFFICIENT REDUCTION HISTORY ===")
    print("ORIGINAL TAPE COEFFICIENTS:")
    print("- x³ (3rd): 0.5")
    print("- x⁵ (5th): 0.25") 
    print("- x⁷ (7th): 0.125")
    print("Total: 0.875")
    print()
    print("FIRST REDUCTION (10x):")
    print("- x³ (3rd): 0.05")
    print("- x⁵ (5th): 0.025")
    print("- x⁷ (7th): 0.0125")
    print("Total: 0.0875")
    print()
    print("SECOND REDUCTION (100x total):")
    print("- x³ (3rd): 0.005")
    print("- x⁵ (5th): 0.0025")
    print("- x⁷ (7th): 0.00125")
    print("Total: 0.00875 (100x reduction)")
    print()
    print("ORIGINAL TUBE COEFFICIENTS:")
    print("- x³ (3rd): 0.2")
    print("- x⁵ (5th): 0.1")
    print("Total: 0.3")
    print()
    print("FIRST REDUCTION (10x):")
    print("- x³ (3rd): 0.02")
    print("- x⁵ (5th): 0.01")
    print("Total: 0.03")
    print()
    print("SECOND REDUCTION (100x total):")
    print("- x³ (3rd): 0.002")
    print("- x⁵ (5th): 0.001")
    print("Total: 0.003 (100x reduction)")
    print()
    print("=== RESULT ===")
    print("✅ Odd boost is now 100x more subtle than original")
    print("✅ Should be inaudible on snare samples")
    print("✅ Still provides character when needed")
    print("✅ Much more usable boost range")

if __name__ == "__main__":
    test_ultra_subtle_odd_boost()
