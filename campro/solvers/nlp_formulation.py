"""
NLP Formulation for Collocation-based Motion Law Generation

This module formulates the motion law generation problem as a nonlinear program (NLP)
suitable for solution with CasADi + IPOPT.
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

try:
    import casadi as ca
    CASADI_AVAILABLE = True
except ImportError:
    CASADI_AVAILABLE = False

import logging
from .discretization import CollocationGrid
from .litvin_constraints import LitvinConstraintBuilder, LitvinParameters

logger = logging.getLogger(__name__)


@dataclass
class ConstraintDefinition:
    """Definition of a constraint in the NLP."""
    name: str
    constraint_type: str  # 'equality', 'inequality'
    description: str
    evaluation_points: np.ndarray
    target_value: Optional[float] = None
    upper_bound: Optional[float] = None
    lower_bound: Optional[float] = None
    tolerance: float = 1e-6


class ConstraintBuilder:
    """
    Builds constraints for the motion law NLP based on user parameters.
    
    This class converts UI parameters (dwells, ramps, CV segments) into
    mathematical constraints for the optimization problem.
    """
    
    def __init__(self, motion_params: Dict[str, Any], grid: CollocationGrid):
        """Initialize constraint builder."""
        self.motion_params = motion_params
        self.grid = grid
        self.constraints: List[ConstraintDefinition] = []
        
        # Extract key parameters
        self.stroke_length = motion_params.get('strokeLengthMm', 10.0)
        self.dwell_tdc_deg = motion_params.get('dwellTdcDeg', 0.0)
        self.dwell_bdc_deg = motion_params.get('dwellBdcDeg', 0.0)
        self.rpm = motion_params.get('rpm', 3000.0)
        
        logger.debug(f"Building constraints for stroke={self.stroke_length}mm, RPM={self.rpm}")
    
    def build_all_constraints(self) -> List[ConstraintDefinition]:
        """Build all constraints for the motion law problem."""
        self.constraints = []
        
        # Core constraints
        self._add_periodicity_constraints()
        self._add_stroke_constraints()
        
        # Motion quality constraints
        self._add_dwell_constraints()
        self._add_smoothness_constraints()
        
        # Physical limits
        self._add_kinematic_limits()
        
        logger.info(f"Built {len(self.constraints)} constraints")
        return self.constraints
    
    def _add_periodicity_constraints(self):
        """Add periodicity constraints for cam motion."""
        # Position periodicity: x(0) = x(2π)
        self.constraints.append(ConstraintDefinition(
            name="position_periodicity",
            constraint_type="equality",
            description="Position periodicity: x(0) = x(2π)",
            evaluation_points=np.array([0.0, 2.0 * np.pi]),
            target_value=0.0,
            tolerance=1e-8
        ))
        
        # Velocity periodicity: v(0) = v(2π)
        self.constraints.append(ConstraintDefinition(
            name="velocity_periodicity",
            constraint_type="equality", 
            description="Velocity periodicity: v(0) = v(2π)",
            evaluation_points=np.array([0.0, 2.0 * np.pi]),
            target_value=0.0,
            tolerance=1e-8
        ))
        
        # Acceleration periodicity: a(0) = a(2π)
        self.constraints.append(ConstraintDefinition(
            name="acceleration_periodicity",
            constraint_type="equality",
            description="Acceleration periodicity: a(0) = a(2π)",
            evaluation_points=np.array([0.0, 2.0 * np.pi]),
            target_value=0.0,
            tolerance=1e-8
        ))
    
    def _add_stroke_constraints(self):
        """Add stroke length and positioning constraints."""
        # TDC position (reference at 0)
        self.constraints.append(ConstraintDefinition(
            name="tdc_position",
            constraint_type="equality",
            description="TDC position = 0 (reference)",
            evaluation_points=np.array([0.0]),
            target_value=0.0,
            tolerance=1e-6
        ))
        
        # BDC position (maximum displacement): detect data-driven evaluation point
        bdc_angle = self._estimate_bdc_evaluation_angle()
        self.constraints.append(ConstraintDefinition(
            name="stroke_length",
            constraint_type="equality",
            description=f"Stroke length = {self.stroke_length}mm",
            evaluation_points=np.array([bdc_angle]),
            target_value=self.stroke_length,
            tolerance=1e-4 * self.stroke_length
        ))

    def _estimate_bdc_evaluation_angle(self) -> float:
        """Estimate BDC evaluation angle using grid and motion parameters.

        Strategy
        --------
        - If a BDC dwell is specified, center the evaluation at the dwell center
          (π) but snap to the nearest available grid node to ensure numerical stability.
        - Otherwise, use a surrogate cycloidal displacement over the existing grid
          nodes and pick the node with the maximum surrogate displacement. This
          avoids hard-coded angles and adapts to arbitrary node layouts.
        """
        nodes = self.grid.nodes
        if nodes.size == 0:
            return float(np.pi)

        # Preferred center for BDC dwell case: π (snap to nearest node)
        if self.dwell_bdc_deg and self.dwell_bdc_deg > 0.0:
            idx = int(np.argmin(np.abs(nodes - np.pi)))
            return float(nodes[idx])

        # Surrogate cycloidal displacement: s(θ) = (1 - cos θ)/2
        surrogate = 0.5 * (1.0 - np.cos(nodes))
        idx = int(np.argmax(surrogate))
        return float(nodes[idx])
    
    def _add_dwell_constraints(self):
        """Add dwell constraints (velocity ≈ 0 during dwells)."""
        if self.dwell_tdc_deg > 0:
            # TDC dwell: velocity should be small
            dwell_start = 0.0
            dwell_end = self.dwell_tdc_deg * np.pi / 180.0
            dwell_points = np.linspace(dwell_start, dwell_end, 3)
            
            self.constraints.append(ConstraintDefinition(
                name="tdc_dwell_velocity",
                constraint_type="inequality",
                description="TDC dwell velocity constraint",
                evaluation_points=dwell_points,
                upper_bound=0.1,  # Small velocity tolerance
                lower_bound=-0.1,
                tolerance=1e-3
            ))
        
        if self.dwell_bdc_deg > 0:
            # BDC dwell: velocity should be small
            bdc_center = np.pi
            dwell_half_span = self.dwell_bdc_deg * np.pi / 360.0
            dwell_start = bdc_center - dwell_half_span
            dwell_end = bdc_center + dwell_half_span
            dwell_points = np.linspace(dwell_start, dwell_end, 3)
            
            self.constraints.append(ConstraintDefinition(
                name="bdc_dwell_velocity",
                constraint_type="inequality",
                description="BDC dwell velocity constraint",
                evaluation_points=dwell_points,
                upper_bound=0.1,
                lower_bound=-0.1,
                tolerance=1e-3
            ))
    
    def _add_smoothness_constraints(self):
        """Add smoothness constraints to ensure reasonable motion profiles."""
        # Acceleration magnitude constraint
        all_nodes = self.grid.nodes
        omega = self.rpm * 2 * np.pi / 60.0  # rad/s
        max_acceleration = 1000.0 * omega * omega  # Conservative acceleration limit
        
        self.constraints.append(ConstraintDefinition(
            name="acceleration_magnitude",
            constraint_type="inequality",
            description="Acceleration magnitude constraint",
            evaluation_points=all_nodes,
            upper_bound=max_acceleration,
            lower_bound=-max_acceleration,
            tolerance=1e-2
        ))
    
    def _add_kinematic_limits(self):
        """Add kinematic limits for velocity and acceleration."""
        # Velocity limits
        omega = self.rpm * 2 * np.pi / 60.0
        max_velocity = 100.0 * omega  # Conservative velocity limit
        
        self.constraints.append(ConstraintDefinition(
            name="velocity_magnitude",
            constraint_type="inequality",
            description="Velocity magnitude constraint",
            evaluation_points=self.grid.nodes,
            upper_bound=max_velocity,
            lower_bound=-max_velocity,
            tolerance=1e-2
        ))


class MotionNLP:
    """
    Nonlinear Program formulation for motion law generation.
    
    This class sets up the complete NLP including variables, objective function,
    and constraints using CasADi symbolic framework.
    """
    
    def __init__(self, grid: CollocationGrid, constraint_builder: ConstraintBuilder, 
                 regularization_weight: float = 1e-3, enable_litvin_constraints: bool = False,
                 litvin_params: Optional[LitvinParameters] = None):
        """Initialize the NLP formulation."""
        if not CASADI_AVAILABLE:
            raise ImportError("CasADi is required for NLP formulation")
        
        self.grid = grid
        self.constraint_builder = constraint_builder
        self.regularization_weight = regularization_weight
        self.enable_litvin_constraints = enable_litvin_constraints
        
        # Initialize Litvin constraint builder if enabled
        self.litvin_builder = None
        if enable_litvin_constraints:
            litvin_params = litvin_params or LitvinParameters()
            self.litvin_builder = LitvinConstraintBuilder(litvin_params, grid)
        
        # Build NLP components
        self._setup_variables()
        self._setup_objective()
        self._setup_constraints()
        self._build_casadi_problem()
        
        logger.info(f"Built NLP with {self.num_variables} variables and {self.num_constraints} constraints")
    
    def _setup_variables(self):
        """Set up optimization variables."""
        n = self.grid.node_count
        
        # Primary variables: position at collocation nodes
        self.position_vars = ca.SX.sym('x', n)
        
        # For future extension: could add velocity/acceleration as independent variables
        # self.velocity_vars = ca.SX.sym('v', n)
        
        # Pack all variables
        self.variables = self.position_vars
        self.num_variables = n
        
        # Set variable bounds
        stroke = self.constraint_builder.stroke_length
        self.variable_bounds = {
            'lower': ca.DM([-0.1 * stroke] * n),  # Allow small negative displacement
            'upper': ca.DM([1.2 * stroke] * n)    # Allow overshoot
        }
    
    def _setup_objective(self):
        """Set up the objective function."""
        # Compute derivatives
        D = ca.DM(self.grid.differentiation_matrix)
        D2 = ca.DM(self.grid.second_derivative_matrix)
        
        velocity = D @ self.position_vars
        acceleration = D2 @ self.position_vars
        
        # Smoothness objective: minimize acceleration and jerk
        smoothness_term = (
            ca.sumsqr(acceleration) +
            self.regularization_weight * ca.sumsqr(D @ acceleration)  # Jerk
        )
        
        # Primary objective: tracking (could add reference trajectory here)
        tracking_term = 0  # For now, rely on constraints
        
        self.objective = smoothness_term + tracking_term
    
    def _setup_constraints(self):
        """Set up all constraints."""
        constraints = self.constraint_builder.build_all_constraints()
        
        constraint_expressions = []
        constraint_bounds_lower = []
        constraint_bounds_upper = []
        
        # Compute derivatives once
        D = ca.DM(self.grid.differentiation_matrix)
        D2 = ca.DM(self.grid.second_derivative_matrix)
        velocity = D @ self.position_vars
        acceleration = D2 @ self.position_vars
        
        for constraint in constraints:
            if constraint.name == "position_periodicity":
                # x(0) - x(2π) = 0 (implemented as x[0] - x[-1] = 0)
                expr = self.position_vars[0] - self.position_vars[-1]
                constraint_expressions.append(expr)
                constraint_bounds_lower.append(0.0)
                constraint_bounds_upper.append(0.0)
                
            elif constraint.name == "velocity_periodicity":
                # v(0) - v(2π) = 0
                expr = velocity[0] - velocity[-1]
                constraint_expressions.append(expr)
                constraint_bounds_lower.append(0.0)
                constraint_bounds_upper.append(0.0)
                
            elif constraint.name == "acceleration_periodicity":
                # a(0) - a(2π) = 0
                expr = acceleration[0] - acceleration[-1]
                constraint_expressions.append(expr)
                constraint_bounds_lower.append(0.0)
                constraint_bounds_upper.append(0.0)
                
            elif constraint.name == "tdc_position":
                # x(0) = 0
                expr = self.position_vars[0]
                constraint_expressions.append(expr)
                constraint_bounds_lower.append(0.0)
                constraint_bounds_upper.append(0.0)
                
            elif constraint.name == "stroke_length":
                # Constrain position at estimated BDC evaluation node
                eval_theta = float(constraint.evaluation_points[0])
                bdc_idx = int(np.argmin(np.abs(self.grid.nodes - eval_theta)))
                expr = self.position_vars[bdc_idx]
                constraint_expressions.append(expr)
                stroke = constraint.target_value
                constraint_bounds_lower.append(stroke * 0.95)  # Allow small tolerance
                constraint_bounds_upper.append(stroke * 1.05)
                
            elif "dwell_velocity" in constraint.name:
                # Velocity constraints at dwell points
                for eval_point in constraint.evaluation_points:
                    # Find closest node
                    node_idx = np.argmin(np.abs(self.grid.nodes - eval_point))
                    expr = velocity[node_idx]
                    constraint_expressions.append(expr)
                    constraint_bounds_lower.append(constraint.lower_bound)
                    constraint_bounds_upper.append(constraint.upper_bound)
                    
            elif constraint.name == "acceleration_magnitude":
                # Acceleration bounds at all nodes
                for i in range(self.grid.node_count):
                    expr = acceleration[i]
                    constraint_expressions.append(expr)
                    constraint_bounds_lower.append(constraint.lower_bound)
                    constraint_bounds_upper.append(constraint.upper_bound)
                    
            elif constraint.name == "velocity_magnitude":
                # Velocity bounds at all nodes
                for i in range(self.grid.node_count):
                    expr = velocity[i]
                    constraint_expressions.append(expr)
                    constraint_bounds_lower.append(constraint.lower_bound)
                    constraint_bounds_upper.append(constraint.upper_bound)
        
        # Add Litvin conjugacy constraints if enabled
        if self.enable_litvin_constraints and self.litvin_builder:
            logger.info("Adding Litvin conjugacy and manufacturability constraints")
            try:
                litvin_constraints = self.litvin_builder.build_litvin_constraints(
                    self.position_vars, velocity
                )
                constraint_expressions.extend(litvin_constraints['expressions'])
                constraint_bounds_lower.extend(litvin_constraints['bounds_lower'])
                constraint_bounds_upper.extend(litvin_constraints['bounds_upper'])
                logger.info(f"Added {litvin_constraints['num_constraints']} Litvin constraints")
            except Exception as e:
                logger.warning(f"Failed to add Litvin constraints: {e}")
                # Continue without Litvin constraints rather than failing completely
        
        # Pack constraints
        if constraint_expressions:
            self.constraints = ca.vertcat(*constraint_expressions)
            self.constraint_bounds = {
                'lower': ca.DM(constraint_bounds_lower),
                'upper': ca.DM(constraint_bounds_upper)
            }
        else:
            self.constraints = ca.DM([])
            self.constraint_bounds = {
                'lower': ca.DM([]),
                'upper': ca.DM([])
            }
        
        self.num_constraints = self.constraints.shape[0]
    
    def _build_casadi_problem(self):
        """Build the complete CasADi NLP problem."""
        self.casadi_problem = {
            'x': self.variables,
            'f': self.objective,
            'g': self.constraints
        }
    
    def get_nlp_info(self) -> Dict[str, Any]:
        """Get information about the NLP formulation."""
        return {
            "num_variables": self.num_variables,
            "num_constraints": self.num_constraints,
            "objective_type": "smoothness_regularized",
            "regularization_weight": self.regularization_weight,
            "grid_info": self.grid.get_grid_info()
        }
