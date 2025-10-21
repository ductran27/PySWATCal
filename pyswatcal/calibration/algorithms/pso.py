"""
Particle Swarm Optimization (PSO)

Implementation of PSO for watershed model calibration.

Reference:
    Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization.
    Proceedings of ICNN'95-International Conference on Neural Networks, 4, 1942-1948.
"""

import numpy as np
from typing import Callable, List, Tuple, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PSO:
    """
    Particle Swarm Optimization (PSO)
    
    PSO is a population-based stochastic optimization algorithm inspired by
    social behavior of bird flocking or fish schooling.
    
    Key Features:
    - Population-based global optimization
    - Good balance between exploration and exploitation
    - Minimal parameters to tune
    - Suitable for continuous optimization problems
    
    Attributes:
        bounds: Parameter bounds as list of (min, max) tuples
        objective_function: Function to optimize
        n_particles: Number of particles in swarm
        n_iterations: Maximum number of iterations
        w: Inertia weight
        c1: Cognitive parameter (personal best attraction)
        c2: Social parameter (global best attraction)
    """
    
    def __init__(
        self,
        bounds: List[Tuple[float, float]],
        objective_function: Callable,
        n_particles: int = 30,
        n_iterations: int = 100,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 1.5,
        maximize: bool = True,
        seed: Optional[int] = None
    ):
        """
        Initialize PSO algorithm
        
        Args:
            bounds: List of (min, max) tuples for each parameter
            objective_function: Function to optimize (takes array, returns float)
            n_particles: Number of particles in swarm
            n_iterations: Maximum number of iterations
            w: Inertia weight (typically 0.4-0.9)
            c1: Cognitive coefficient (typically 1.5-2.0)
            c2: Social coefficient (typically 1.5-2.0)
            maximize: Whether to maximize objective function
            seed: Random seed for reproducibility
        """
        self.bounds = bounds
        self.n_params = len(bounds)
        self.objective_function = objective_function
        self.n_particles = n_particles
        self.n_iterations = n_iterations
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.maximize = maximize
        self.seed = seed
        
        # Validate inputs
        if n_particles < 2:
            raise ValueError("n_particles must be at least 2")
        
        if n_iterations < 1:
            raise ValueError("n_iterations must be at least 1")
        
        for i, (lower, upper) in enumerate(bounds):
            if lower >= upper:
                raise ValueError(f"Invalid bounds for parameter {i}: [{lower}, {upper}]")
        
        if seed is not None:
            np.random.seed(seed)
        
        # Initialize tracking
        self.global_best_position = None
        self.global_best_value = None
        self.history = {
            'iteration': [],
            'global_best_value': [],
            'swarm_best_value': [],
            'swarm_mean_value': []
        }
        
        logger.info(
            f"Initialized PSO: {self.n_params} parameters, "
            f"{n_particles} particles, {n_iterations} iterations"
        )
    
    def optimize(self) -> Dict[str, Any]:
        """
        Run PSO optimization
        
        Returns:
            Dictionary containing optimization results
        """
        logger.info("Starting PSO optimization")
        start_time = datetime.now()
        
        try:
            # Initialize swarm
            positions, velocities = self._initialize_swarm()
            
            # Evaluate initial positions
            fitness = np.zeros(self.n_particles)
            for i in range(self.n_particles):
                fitness[i] = self.objective_function(positions[i])
            
            # Initialize personal bests
            personal_best_positions = positions.copy()
            personal_best_fitness = fitness.copy()
            
            # Initialize global best
            best_idx = np.argmax(fitness) if self.maximize else np.argmin(fitness)
            self.global_best_position = positions[best_idx].copy()
            self.global_best_value = fitness[best_idx]
            
            logger.info(f"Initial global best: {self.global_best_value:.6f}")
            
            # Main optimization loop
            for iteration in range(self.n_iterations):
                for i in range(self.n_particles):
                    # Update velocity
                    r1, r2 = np.random.random(2)
                    
                    cognitive = self.c1 * r1 * (personal_best_positions[i] - positions[i])
                    social = self.c2 * r2 * (self.global_best_position - positions[i])
                    velocities[i] = self.w * velocities[i] + cognitive + social
                    
                    # Update position
                    positions[i] = positions[i] + velocities[i]
                    
                    # Apply bounds
                    positions[i] = self._apply_bounds(positions[i])
                    
                    # Evaluate
                    fitness[i] = self.objective_function(positions[i])
                    
                    # Update personal best
                    if self._is_better(fitness[i], personal_best_fitness[i]):
                        personal_best_positions[i] = positions[i].copy()
                        personal_best_fitness[i] = fitness[i]
                    
                    # Update global best
                    if self._is_better(fitness[i], self.global_best_value):
                        self.global_best_position = positions[i].copy()
                        self.global_best_value = fitness[i]
                
                # Record history
                self._update_history(iteration, fitness)
                
                # Progress logging
                if (iteration + 1) % max(1, self.n_iterations // 10) == 0:
                    progress = 100 * (iteration + 1) / self.n_iterations
                    logger.info(
                        f"Progress: {progress:.0f}% - "
                        f"Global best: {self.global_best_value:.6f}"
                    )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"PSO completed: Best value = {self.global_best_value:.6f}, "
                f"Duration = {duration:.2f}s"
            )
            
            return {
                'best_params': self.global_best_position,
                'best_value': self.global_best_value,
                'n_evaluations': self.n_particles * self.n_iterations,
                'history': self.history,
                'success': True,
                'duration': duration
            }
            
        except Exception as e:
            logger.error(f"PSO optimization failed: {e}", exc_info=True)
            return {
                'best_params': self.global_best_position,
                'best_value': self.global_best_value,
                'n_evaluations': len(self.history['iteration']) * self.n_particles,
                'history': self.history,
                'success': False,
                'error': str(e)
            }
    
    def _initialize_swarm(self) -> Tuple[np.ndarray, np.ndarray]:
        """Initialize particle positions and velocities"""
        positions = np.zeros((self.n_particles, self.n_params))
        velocities = np.zeros((self.n_particles, self.n_params))
        
        for i, (lower, upper) in enumerate(self.bounds):
            # Random initial positions
            positions[:, i] = np.random.uniform(lower, upper, self.n_particles)
            
            # Random initial velocities
            v_max = 0.2 * (upper - lower)
            velocities[:, i] = np.random.uniform(-v_max, v_max, self.n_particles)
        
        return positions, velocities
    
    def _apply_bounds(self, position: np.ndarray) -> np.ndarray:
        """Apply parameter bounds to position"""
        bounded = position.copy()
        for i, (lower, upper) in enumerate(self.bounds):
            bounded[i] = np.clip(bounded[i], lower, upper)
        return bounded
    
    def _is_better(self, new_value: float, current_value: float) -> bool:
        """Check if new value is better than current"""
        if self.maximize:
            return new_value > current_value
        else:
            return new_value < current_value
    
    def _update_history(self, iteration: int, fitness: np.ndarray) -> None:
        """Update optimization history"""
        self.history['iteration'].append(iteration)
        self.history['global_best_value'].append(self.global_best_value)
        self.history['swarm_best_value'].append(np.max(fitness) if self.maximize else np.min(fitness))
        self.history['swarm_mean_value'].append(np.mean(fitness))
    
    def __repr__(self) -> str:
        """String representation"""
        direction = "maximize" if self.maximize else "minimize"
        return (
            f"PSO(n_params={self.n_params}, "
            f"n_particles={self.n_particles}, "
            f"n_iterations={self.n_iterations}, "
            f"{direction})"
        )


def pso_optimization(
    objective_function: Callable,
    bounds: List[Tuple[float, float]],
    n_particles: int = 30,
    n_iterations: int = 100,
    maximize: bool = True,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Convenience function for PSO optimization
    
    Args:
        objective_function: Function to optimize
        bounds: Parameter bounds
        n_particles: Number of particles
        n_iterations: Number of iterations
        maximize: Whether to maximize
        seed: Random seed
        
    Returns:
        Optimization results dictionary
    """
    pso = PSO(
        bounds=bounds,
        objective_function=objective_function,
        n_particles=n_particles,
        n_iterations=n_iterations,
        maximize=maximize,
        seed=seed
    )
    
    return pso.optimize()
