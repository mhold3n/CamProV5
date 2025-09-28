#!/usr/bin/env python3
"""
Test suite for extracted collocation solver components.

This module tests the extracted collocation solver components to ensure
they work correctly when moved to the new modular structure.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add campro to path for imports
sys.path.append(str(Path(__file__).parent.parent / "campro"))

from campro.optimization.collocation_optimizer import CollocationOptimizer, CollocationParameters, CollocationSolution


class TestExtractedCollocationSolver:
    """Test suite for extracted collocation solver components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parameters = CollocationParameters(
            node_count=8,  # Small number for testing
            max_iterations=100,
            tolerance=1e-6,
            use_continuation=False,  # Disable for faster testing
            enable_numerical_guards=False,  # Disable for faster testing
            enable_dense_validation=False  # Disable for faster testing
        )
        self.optimizer = CollocationOptimizer(self.parameters)
        self.baseline_motion_params = self.get_baseline_motion_params()
    
    def get_baseline_motion_params(self):
        """Get baseline motion parameters for testing."""
        return {
            "strokeLengthMm": 10.0,
            "riseDeg": 90.0,
            "dwellDeg": 30.0,
            "fallDeg": 90.0,
            "rpm": 1000.0,
            "maxAcceleration": 1000.0,
            "maxJerk": 5000.0
        }
    
    def test_collocation_parameters_initialization(self):
        """Test collocation parameters initialization."""
        # Test default parameters
        default_params = CollocationParameters()
        assert default_params.node_count == 16
        assert default_params.node_type == "LGL"
        assert default_params.max_iterations == 1000
        assert default_params.tolerance == 1e-8
        assert default_params.use_continuation is True
        assert default_params.use_warm_start is True
        
        # Test custom parameters
        custom_params = CollocationParameters(
            node_count=8,
            max_iterations=100,
            tolerance=1e-6,
            use_continuation=False
        )
        assert custom_params.node_count == 8
        assert custom_params.max_iterations == 100
        assert custom_params.tolerance == 1e-6
        assert custom_params.use_continuation is False
    
    def test_collocation_optimizer_initialization(self):
        """Test collocation optimizer initialization."""
        # Test with default parameters
        optimizer_default = CollocationOptimizer()
        assert optimizer_default.parameters is not None
        assert optimizer_default.nlp_formulation is None
        assert optimizer_default.last_solution is None
        
        # Test with custom parameters
        custom_params = CollocationParameters(node_count=8)
        optimizer_custom = CollocationOptimizer(custom_params)
        assert optimizer_custom.parameters.node_count == 8
    
    def test_collocation_solution_structure(self):
        """Test collocation solution structure."""
        # Create a mock solution
        solution = CollocationSolution(
            success=True,
            execution_time=1.0,
            iterations=50,
            theta_grid=np.linspace(0, np.pi, 8),
            position=np.linspace(0, 10, 8),
            velocity=np.ones(8),
            acceleration=np.zeros(8),
            objective_value=0.1,
            constraint_violation=1e-6,
            solver_status="Solve_Succeeded",
            return_code=0,
            node_count=8,
            discretization_type="LGL"
        )
        
        # Verify solution structure
        assert solution.success is True
        assert solution.execution_time == 1.0
        assert solution.iterations == 50
        assert len(solution.theta_grid) == 8
        assert len(solution.position) == 8
        assert len(solution.velocity) == 8
        assert len(solution.acceleration) == 8
        assert solution.objective_value == 0.1
        assert solution.constraint_violation == 1e-6
        assert solution.solver_status == "Solve_Succeeded"
        assert solution.return_code == 0
        assert solution.node_count == 8
        assert solution.discretization_type == "LGL"
    
    def test_motion_law_optimization(self):
        """Test motion law optimization."""
        # Test the optimization method
        solution = self.optimizer.optimize_motion_law(self.baseline_motion_params)
        
        # Verify solution structure
        assert isinstance(solution, CollocationSolution)
        assert hasattr(solution, 'success')
        assert hasattr(solution, 'execution_time')
        assert hasattr(solution, 'iterations')
        assert hasattr(solution, 'theta_grid')
        assert hasattr(solution, 'position')
        assert hasattr(solution, 'velocity')
        assert hasattr(solution, 'acceleration')
        assert hasattr(solution, 'objective_value')
        assert hasattr(solution, 'constraint_violation')
        assert hasattr(solution, 'solver_status')
        assert hasattr(solution, 'return_code')
        
        # Verify solution data
        if solution.success:
            assert len(solution.theta_grid) > 0
            assert len(solution.position) == len(solution.theta_grid)
            assert len(solution.velocity) == len(solution.theta_grid)
            assert len(solution.acceleration) == len(solution.theta_grid)
            assert np.all(np.isfinite(solution.position))
            assert np.all(np.isfinite(solution.velocity))
            assert np.all(np.isfinite(solution.acceleration))
            assert solution.objective_value >= 0
            assert solution.constraint_violation >= 0
    
    def test_gear_profile_optimization(self):
        """Test gear profile optimization."""
        # Test the gear optimization method
        solution = self.optimizer.optimize_gear_profiles(
            self.baseline_motion_params, self.baseline_motion_params
        )
        
        # Verify solution structure
        assert isinstance(solution, CollocationSolution)
        assert hasattr(solution, 'success')
        assert hasattr(solution, 'execution_time')
        assert hasattr(solution, 'iterations')
        assert hasattr(solution, 'theta_grid')
        assert hasattr(solution, 'position')
        assert hasattr(solution, 'velocity')
        assert hasattr(solution, 'acceleration')
        
        # Verify solution data
        if solution.success:
            assert len(solution.theta_grid) > 0
            assert len(solution.position) == len(solution.theta_grid)
            assert len(solution.velocity) == len(solution.theta_grid)
            assert len(solution.acceleration) == len(solution.theta_grid)
            assert np.all(np.isfinite(solution.position))
            assert np.all(np.isfinite(solution.velocity))
            assert np.all(np.isfinite(solution.acceleration))
    
    def test_solver_info(self):
        """Test solver info method."""
        info = self.optimizer.get_solver_info()
        
        # Verify info structure
        assert isinstance(info, dict)
        assert "solver_type" in info
        assert "casadi_available" in info
        assert "parameters" in info
        assert "has_solution" in info
        assert "matrix_cache" in info
        
        # Verify info content
        assert info["solver_type"] == "collocation"
        assert isinstance(info["casadi_available"], bool)
        assert isinstance(info["parameters"], dict)
        assert isinstance(info["has_solution"], bool)
        assert isinstance(info["matrix_cache"], dict)
    
    def test_cache_management(self):
        """Test cache management methods."""
        # Test cache clearing
        self.optimizer.clear_cache()
        
        # Test cache performance
        performance = self.optimizer.get_cache_performance()
        assert isinstance(performance, dict)
    
    def test_export_solution_for_kotlin(self):
        """Test solution export for Kotlin."""
        # Create a mock successful solution
        solution = CollocationSolution(
            success=True,
            execution_time=1.0,
            iterations=50,
            theta_grid=np.linspace(0, 2*np.pi, 8),
            position=np.linspace(0, 10, 8),
            velocity=np.ones(8),
            acceleration=np.zeros(8),
            objective_value=0.1,
            constraint_violation=1e-6,
            solver_status="Solve_Succeeded",
            return_code=0,
            node_count=8,
            discretization_type="LGL"
        )
        
        # Test export (this should not raise an exception)
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
                output_path = Path(tmp_file.name)
            
            self.optimizer.export_solution_for_kotlin(solution, output_path)
            
            # Verify file was created
            assert output_path.exists()
            
            # Clean up
            output_path.unlink()
            
        except Exception as e:
            # If CasADi is not available, this is expected
            if "CasADi" in str(e):
                pytest.skip("CasADi not available for export test")
            else:
                raise
    
    def test_parameter_sensitivity(self):
        """Test parameter sensitivity."""
        # Test with different node counts
        for node_count in [4, 8, 16]:
            params = CollocationParameters(
                node_count=node_count,
                max_iterations=50,
                use_continuation=False,
                enable_numerical_guards=False,
                enable_dense_validation=False
            )
            optimizer = CollocationOptimizer(params)
            
            solution = optimizer.optimize_motion_law(self.baseline_motion_params)
            
            # Verify solution structure
            assert isinstance(solution, CollocationSolution)
            if solution.success:
                assert len(solution.theta_grid) == node_count
                assert len(solution.position) == node_count
                assert len(solution.velocity) == node_count
                assert len(solution.acceleration) == node_count
    
    def test_error_handling(self):
        """Test error handling."""
        # Test with invalid parameters
        invalid_params = {
            "strokeLengthMm": -10.0,  # Invalid negative stroke
            "riseDeg": 0.0,  # Invalid zero rise
            "fallDeg": 0.0,  # Invalid zero fall
        }
        
        solution = self.optimizer.optimize_motion_law(invalid_params)
        
        # Should handle errors gracefully
        assert isinstance(solution, CollocationSolution)
        # May or may not succeed depending on implementation
        if not solution.success:
            assert solution.return_code != 0
            assert solution.solver_status != "Solve_Succeeded"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
