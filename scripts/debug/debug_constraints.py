#!/usr/bin/env python3
"""
Debug constraint consistency in Phase 2.
"""


def analyze_constraints():
    """Analyze if the constraint system is mathematically consistent."""
    
    print("=== Constraint Analysis ===")
    
    # Constraint 1: R_ring = R_sun + 2*R_planet (unified constraint)
    # Constraint 2: r_inst * R_planet = R_ring (no-slip constraint)
    
    # From constraint 2: R_ring = r_inst * R_planet
    # Substituting into constraint 1: r_inst * R_planet = R_sun + 2*R_planet
    # Rearranging: (r_inst - 2) * R_planet = R_sun
    
    # This means: R_sun = (r_inst - 2) * R_planet
    
    # For r_inst in [1.5, 2.5]:
    # - When r_inst = 1.5: R_sun = -0.5 * R_planet (negative!)
    # - When r_inst = 2.0: R_sun = 0 * R_planet (zero!)
    # - When r_inst = 2.5: R_sun = 0.5 * R_planet (positive)
    
    print("Constraint system analysis:")
    print("1. R_ring = R_sun + 2*R_planet")
    print("2. r_inst * R_planet = R_ring")
    print()
    print("Substituting constraint 2 into constraint 1:")
    print("r_inst * R_planet = R_sun + 2*R_planet")
    print("Rearranging: R_sun = (r_inst - 2) * R_planet")
    print()
    
    r_values = [1.5, 1.8, 2.0, 2.2, 2.5]
    R_planet = 5.0  # Example planet radius
    
    print("For R_planet = 5.0:")
    for r_inst in r_values:
        R_sun = (r_inst - 2) * R_planet
        R_ring = r_inst * R_planet
        print(f"r_inst = {r_inst:.1f}: R_sun = {R_sun:.1f}, R_ring = {R_ring:.1f}")
        
        # Check if constraints are satisfied
        constraint1 = R_ring - (R_sun + 2 * R_planet)
        constraint2 = r_inst * R_planet - R_ring
        print(f"  Constraint 1 residual: {constraint1:.6f}")
        print(f"  Constraint 2 residual: {constraint2:.6f}")
        print()
    
    print("PROBLEM: When r_inst < 2.0, R_sun becomes negative or zero!")
    print("But we have bounds: R_sun >= 0.5")
    print("This makes the problem infeasible for r_inst < 2.0")

if __name__ == "__main__":
    analyze_constraints()
