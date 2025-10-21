"""
Dynamically Dimensioned Search (DDS) Algorithm

Implementation of the DDS optimization algorithm for watershed model calibration.

Reference:
    Tolson, B. A., & Shoemaker, C. A. (2007). Dynamically dimensioned search 
    algorithm for computationally efficient watershed model calibration. 
    Water Resources Research, 43(1).
"""

import numpy as np
from typing import Callable, List, Tuple, Dict, Any, Optional
import logging
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DDS:
    """
    Dynamically Dimensioned Search (DDS) Algorithm
    
    DDS is a heuristic global optimization algorithm designed for
    calibrating computationally expensive simulation models. It dynamically
    adjusts the search dimension as the optimization progresses.
    
    Key Features:
    - Single-objective optimization
    - Global search algorithm
    - Handles computationally expensive functions
    - Requires minimal parameter tuning
    - No derivative information needed
    
    Attributes:
        bounds: Parameter bounds as list of (min, max) tuples
        objective_function: Function to minimize/maximize
        n_iterations: Maximum number of iterations
        r: Perturbation parameter (typically 0.2)
        maximize: Whether to maximize (True) or minimize (False)
    """
    
    def __init__(
        self,
        bounds: List[Tuple[float, float]],
        objective_function: Callable,
        n_iterations: int = 100,
        r: float = 0.2,
        maximize: bool = True,
        seed: Optional[int] = None
    ):
        """
        Initialize DDS algorithm
        
        Args:
            bounds: List of (min, max) tuples for each parameter
            objective_function: Function to optimize (takes array, returns float)
            n_iterations: Maximum number of iterations
            r: Perturbation parameter (0 < r < 1, typically 0.2)
            maximize: Whether to maximize objective function
            seed: Random seed for reproducibility
        """
        self.bounds = bounds
        self.n_params = len(bounds)
        self.objective_function = objective_function
        self.n_iterations = n_iterations
        self.r = r
        self.maximize = maximize
        self.seed = seed
        
        # Validate inputs
        if not 0 < r < 1:
            raise ValueError(f"Perturbation parameter r must be between 0 and 1, got {r}")
        
        if n_iterations < 1:
            raise ValueError(f"n_iterations must be at least 1, got {n_iterations}")
        
        for i, (lower, upper) in enumerate(bounds):
            if lower >= upper:
                raise ValueError(f"Invalid bounds for parameter {i}: [{lower}, {upper}]")
        
        # Set random seed
        if seed is not None:
            np.random.seed(seed)
        
        # Initialize tracking
        self.best_params = None
        self.best_value = None
        self.history = {
            'iteration': [],
            'objective_value': [],
            'best_value': [],
            'n_perturbed_params': [],
            'parameters': []
        }
        
        logger.info(f"Initialized DDS: {self.n_params} parameters, {n_iterations} iterations")
    
    def optimize(
        self,
        initial_params: Optional[np.ndarray] = None,
        callback: Optional[Callable] = None,
        checkpoint_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Run DDS optimization
        
        Args:
            initial_params: Initial parameter values (if None, random initialization)
            callback: Function called after each iteration with (iteration, params, value)
            checkpoint_dir: Directory to save checkpoints (if provided)
            
        Returns:
            Dictionary containing:
                - best_params: Best parameter values found
                - best_value: Best objective function value
                - n_evaluations: Total number of function evaluations
                - history: Optimization history
                - success: Whether optimization completed successfully
        """
        logger.info("Starting DDS optimization")
        start_time = datetime.now()
        
        try:
            # Initialize parameters
            if initial_params is None:
                current_params = self._random_initial()
            else:
                current_params = np.array(initial_params)
                self._validate_params(current_params)
            
            # Evaluate initial parameters
            current_value = self.objective_function(current_params)
            
            # Initialize best
            self.best_params = current_params.copy()
            self.best_value = current_value
            
            # Store initial
            self._update_history(0, current_params, current_value, 0)
            
            logger.info(f"Initial value: {current_value:.6f}")
            
            # Main optimization loop
            for iteration in range(1, self.n_iterations + 1):
                # Calculate probability of perturbing each parameter
                prob = 1 - np.log(iteration) / np.log(self.n_iterations)
                
                # Select parameters to perturb
                perturb_mask = np.random.random(self.n_params) < prob
                
                # Ensure at least one parameter is perturbed
                if not perturb_mask.any():
                    perturb_mask[np.random.randint(self.n_params)] = True
                
                n_perturbed = perturb_mask.sum()
                
                # Generate new parameter set
                new_params = self._perturb_parameters(
                    self.best_params,
                    perturb_mask
                )
                
                # Evaluate new parameters
                new_value = self.objective_function(new_params)
                
                # Check if new parameters are better
                is_better = self._is_better(new_value, self.best_value)
                
                if is_better:
                    self.best_params = new_params.copy()
                    self.best_value = new_value
                    logger.debug(f"Iteration {iteration}: New best = {new_value:.6f}")
                
                # Update history
                self._update_history(
                    iteration,
                    new_params,
                    new_value,
                    n_perturbed
                )
                
                # Callback
                if callback is not None:
                    callback(iteration, self.best_params, self.best_value)
                
                # Checkpoint
                if checkpoint_dir is not None and iteration % 10 == 0:
                    self._save_checkpoint(checkpoint_dir, iteration)
                
                # Progress logging
                if iteration % max(1, self.n_iterations // 10) == 0:
                    progress = 100 * iteration / self.n_iterations
                    logger.info(
                        f"Progress: {progress:.0f}% - "
                        f"Best value: {self.best_value:.6f} - "
                        f"Perturbed: {n_perturbed}/{self.n_params}"
                    )
            
            # Final results
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"DDS optimization completed: "
                f"Best value = {self.best_value:.6f}, "
                f"Duration = {duration:.2f}s"
            )
            
            return {
                'best_params': self.best_params,
                'best_value': self.best_value,
                'n_evaluations': self.n_iterations,
                'history': self.history,
                'success': True,
                'duration': duration
            }
            
        except Exception as e:
            logger.error(f"DDS optimization failed: {e}", exc_info=True)
            return {
                'best_params': self.best_params,
                'best_value': self.best_value,
                'n_evaluations': len(self.history['iteration']),
                'history': self.history,
                'success': False,
                'error': str(e)
            }
    
    def _random_initial(self) -> np.ndarray:
        """Generate random initial parameters within bounds"""
        params = np.zeros(self.n_params)
        for i, (lower, upper) in enumerate(self.bounds):
            params[i] = np.random.uniform(lower, upper)
        return params
    
    def _validate_params(self, params: np.ndarray) -> None:
        """Validate parameter values are within bounds"""
        if len(params) != self.n_params:
            raise ValueError(
                f"Expected {self.n_params} parameters, got {len(params)}"
            )
        
        for i, (value, (lower, upper)) in enumerate(zip(params, self.bounds)):
            if not lower <= value <= upper:
                raise ValueError(
                    f"Parameter {i} value {value} outside bounds [{lower}, {upper}]"
                )
    
    def _perturb_parameters(
        self,
        params: np.ndarray,
        perturb_mask: np.ndarray
    ) -> np.ndarray:
        """
        Perturb selected parameters
        
        Uses reflection to keep parameters within bounds
        """
        new_params = params.copy()
        
        for i in range(self.n_params):
            if perturb_mask[i]:
                lower, upper = self.bounds[i]
                
                # Standard deviation for perturbation
                sigma = self.r * (upper - lower)
                
                # Generate perturbation
                perturbation = np.random.normal(0, sigma)
                new_value = params[i] + perturbation
                
                # Reflection at bounds
                while new_value < lower or new_value > upper:
                    if new_value < lower:
                        new_value = lower + (lower - new_value)
                    if new_value > upper:
                        new_value = upper - (new_value - upper)
                
                new_params[i] = new_value
        
        return new_params
    
    def _is_better(self, new_value: float, current_value: float) -> bool:
        """Check if new value is better than current"""
        if self.maximize:
            return new_value > current_value
        else:
            return new_value < current_value
    
    def _update_history(
        self,
        iteration: int,
        params: np.ndarray,
        value: float,
        n_perturbed: int
    ) -> None:
        """Update optimization history"""
        self.history['iteration'].append(iteration)
        self.history['objective_value'].append(value)
        self.history['best_value'].append(self.best_value)
        self.history['n_perturbed_params'].append(n_perturbed)
        self.history['parameters'].append(params.tolist())
    
    def _save_checkpoint(self, checkpoint_dir: Path, iteration: int) -> None:
        """Save optimization checkpoint"""
        checkpoint_dir = Path(checkpoint_dir)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            'iteration': iteration,
            'best_params': self.best_params.tolist(),
            'best_value': float(self.best_value),
            'history': self.history,
            'timestamp': datetime.now().isoformat()
        }
        
        checkpoint_file = checkpoint_dir / f"dds_checkpoint_iter_{iteration}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        logger.debug(f"Saved checkpoint to {checkpoint_file}")
    
    def get_convergence_plot_data(self) -> Dict[str, List]:
        """
        Get data for convergence plot
        
        Returns:
            Dictionary with iterations and best values
        """
        return {
            'iterations': self.history['iteration'],
            'best_values': self.history['best_value']
        }
    
    def get_parameter_evolution(self) -> Dict[str, List]:
        """
        Get parameter evolution over iterations
        
        Returns:
            Dictionary with parameter indices and their values over time
        """
        params_array = np.array(self.history['parameters'])
        evolution = {}
        
        for i in range(self.n_params):
            evolution[f'param_{i}'] = params_array[:, i].tolist()
        
        return evolution
    
    def __repr__(self) -> str:
        """String representation"""
        direction = "maximize" if self.maximize else "minimize"
        return (
            f"DDS(n_params={self.n_params}, "
            f"n_iterations={self.n_iterations}, "
            f"r={self.r}, "
            f"{direction})"
        )


def dds_calibration(
    objective_function: Callable,
    bounds: List[Tuple[float, float]],
    n_iterations: int = 100,
    r: float = 0.2,
    maximize: bool = True,
    initial_params: Optional[np.ndarray] = None,
    seed: Optional[int] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Convenience function for DDS calibration
    
    Args:
        objective_function: Function to optimize
        bounds: Parameter bounds
        n_iterations: Number of iterations
        r: Perturbation parameter
        maximize: Whether to maximize
        initial_params: Initial parameter values
        seed: Random seed
        verbose: Whether to print progress
        
    Returns:
        Optimization results dictionary
    """
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    dds = DDS(
        bounds=bounds,
        objective_function=objective_function,
        n_iterations=n_iterations,
        r=r,
        maximize=maximize,
        seed=seed
    )
    
    results = dds.optimize(initial_params=initial_params)
    
    if verbose:
        print("\n" + "="*60)
        print("DDS Optimization Results")
        print("="*60)
        print(f"Best objective value: {results['best_value']:.6f}")
        print(f"Best parameters: {results['best_params']}")
        print(f"Total evaluations: {results['n_evaluations']}")
        print(f"Duration: {results['duration']:.2f}s")
        print("="*60)
    
    return results
