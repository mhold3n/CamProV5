#!/usr/bin/env python3
"""
Debug with minimal constraints to isolate the issue.
"""

import numpy as np
import casadi as ca

def debug_minimal_constraints():
    """Debug with minimal constraints."""
    
    print("=== Minimal Constraints Debug ===")
    
    # Very simple motion law
    n = 3  # Even smaller
    theta_deg = np.linspace(0.0, 180.0, n)
    displacement = np.zeros(n)
    velocity = np.zeros(n)
    acceleration = np.zeros(n)
    
    motion_law = {
        'grid': theta_deg,
        'displacement': displacement,
        'velocity': velocity,
        'acceleration': acceleration,
    }
    
    gear_params = {
        'ringRotationDeg': 180.0,
        'samplingStepDeg': theta_deg[1] - theta_deg[0],
        'rMin': 2.0,
        'rMax': 2.0,  # Fixed ratio to eliminate global constraint issues
    }
    
    print(f"Motion law: {len(motion_law['grid'])} points")
    print(f"Gear params: {gear_params}")
    
    # Create a minimal NLP manually
    sun_radius = ca.SX.sym('sun_radius', n)
    planet_radius = ca.SX.sym('planet_radius', n)
    ring_radius = ca.SX.sym('ring_radius', n)
    r_inst = ca.SX.sym('r_inst', n)
    
    # Simple objective: minimize sum of gear sizes
    f = ca.sum1(sun_radius) + ca.sum1(planet_radius) + ca.sum1(ring_radius)
    
    # Minimal constraints
    g = []
    lbg = []
    ubg = []
    
    # 1. Unified constraint: R_ring = R_sun + 2*R_planet
    for i in range(n):
        g.append(ring_radius[i] - (sun_radius[i] + 2 * planet_radius[i]))
        lbg.append(0.0)
        ubg.append(0.0)
    
    # 2. No-slip constraint: r_inst * R_planet = R_ring
    for i in range(n):
        g.append(r_inst[i] * planet_radius[i] - ring_radius[i])
        lbg.append(0.0)
        ubg.append(0.0)
    
    # Variable bounds
    lbx = []
    ubx = []
    
    # Gear bounds
    for i in range(n):
        lbx.extend([0.5, 0.5, 1.0])  # sun, planet, ring
        ubx.extend([100.0, 100.0, 100.0])
    
    # r bounds
    for i in range(n):
        lbx.append(2.0)
        ubx.append(2.0)
    
    # Initial guess
    x0 = []
    for i in range(n):
        x0.extend([5.0, 3.0, 11.0])  # sun, planet, ring
    for i in range(n):
        x0.append(2.0)  # r_inst
    
    # Create NLP
    nlp = {
        'x': ca.vertcat(sun_radius, planet_radius, ring_radius, r_inst),
        'f': f,
        'g': ca.vertcat(*g)
    }
    
    print(f"NLP: {4*n} variables, {len(g)} constraints")
    print(f"Variable bounds: [{min(lbx):.1f}, {max(ubx):.1f}]")
    print(f"Initial guess: {x0}")
    
    # Try to solve
    try:
        solver = ca.nlpsol('solver', 'ipopt', nlp)
        result = solver(x0=x0, lbx=lbx, ubx=ubx, lbg=lbg, ubg=ubg)
        
        x_opt = result['x']
        print(f"Solution found: {result['f']}")
        print(f"x_opt: {x_opt}")
        
        # Check constraints
        g_opt = result['g']
        print(f"Constraint residuals: {g_opt}")
        
    except Exception as e:
        print(f"Solver failed: {e}")

if __name__ == "__main__":
    debug_minimal_constraints()
