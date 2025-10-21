"""
Morris sensitivity analysis (Elementary Effects method)

Implementation using SALib for global sensitivity analysis.

Reference:
    Morris, M. D. (1991). Factorial sampling plans for preliminary computational experiments.
    Technometrics, 33(2), 161-174.
"""

import numpy as np
from typing import Callable, List, Tuple, Dict, Any, Optional
import logging
from SALib.sample import morris as morris_sample
from SALib.analyze import morris as morris_analyze

logger = logging.getLogger(__name__)


class MorrisAnalysis:
    """
    Morris method for global sensitivity analysis
    
    Also known as Elementary Effects method. Provides qualitative
    sensitivity rankings with low computational cost.
    
    Key Features:
    - Qualitative sensitivity ranking
    - Identifies important parameters
    - Computationally efficient
    - Detects parameter interactions
    
    Attributes:
        bounds: Parameter bounds
        objective_function: Function to analyze
        num_levels: Number of grid levels (default: 4)
        num_trajectories: Number of trajectories (default: 10)
    """
    
    def __init__(
        self,
        bounds: List[Tuple[float, float]],
        objective_function: Callable,
        parameter_names: Optional[List[str]] = None,
        num_levels: int = 4,
        num_trajectories: int = 10,
        seed: Optional[int] = None
    ):
        """
        Initialize Morris analysis
        
        Args:
            bounds: List of (min, max) tuples for parameters
            objective_function: Function to evaluate
            parameter_names: Names of parameters
            num_levels: Number of grid levels for sampling
            num_trajectories: Number of trajectories to generate
            seed: Random seed
        """
        self.bounds = bounds
        self.n_params = len(bounds)
        self.objective_function = objective_function
        self.num_levels = num_levels
        self.num_trajectories = num_trajectories
        self.seed = seed
        
        if parameter_names is None:
            self.parameter_names = [f"param_{i}" for i in range(self.n_params)]
        else:
            self.parameter_names = parameter_names
        
        # Create problem definition for SALib
        self.problem = {
            'num_vars': self.n_params,
            'names': self.parameter_names,
            'bounds': bounds
        }
        
        logger.info(
            f"Initialized Morris analysis: {self.n_params} parameters, "
            f"{num_trajectories} trajectories"
        )
    
    def run(self) -> Dict[str, Any]:
        """
        Run Morris sensitivity analysis
        
        Returns:
            Dictionary containing sensitivity results
        """
        logger.info("Starting Morris sensitivity analysis")
        
        try:
            # Generate samples
            parameter_values = morris_sample.sample(
                self.problem,
                N=self.num_trajectories,
                num_levels=self.num_levels,
                seed=self.seed
            )
            
            n_samples = len(parameter_values)
            logger.info(f"Generated {n_samples} sample points")
            
            # Evaluate model at all sample points
            outputs = np.zeros(n_samples)
            
            for i, params in enumerate(parameter_values):
                outputs[i] = self.objective_function(params)
                
                if (i + 1) % max(1, n_samples // 10) == 0:
                    progress = 100 * (i + 1) / n_samples
                    logger.info(f"Progress: {progress:.0f}%")
            
            # Analyze results
            Si = morris_analyze.analyze(
                self.problem,
                parameter_values,
                outputs,
                num_levels=self.num_levels,
                seed=self.seed
            )
            
            # Package results
            results = {
                'mu': Si['mu'],  # Mean of absolute elementary effects
                'mu_star': Si['mu_star'],  # Mean of absolute elementary effects
                'sigma': Si['sigma'],  # Standard deviation of elementary effects
                'mu_star_conf': Si['mu_star_conf'],  # Confidence interval
                'parameter_names': self.parameter_names,
                'n_samples': n_samples,
                'success': True
            }
            
            # Rank parameters by importance
            ranking = np.argsort(Si['mu_star'])[::-1]
            results['ranking'] = ranking
            results['ranked_parameters'] = [self.parameter_names[i] for i in ranking]
            
            logger.info("Morris analysis completed")
            return results
            
        except Exception as e:
            logger.error(f"Morris analysis failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_sensitivity_indices(self) -> Dict[str, np.ndarray]:
        """
        Get sensitivity indices in dict form
        
        Returns:
            Dictionary with mu, mu_star, and sigma for each parameter
        """
        results = self.run()
        
        if not results['success']:
            raise ValueError("Analysis failed")
        
        indices = {}
        for i, name in enumerate(self.parameter_names):
            indices[name] = {
                'mu': results['mu'][i],
                'mu_star': results['mu_star'][i],
                'sigma': results['sigma'][i]
            }
        
        return indices
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"MorrisAnalysis(n_params={self.n_params}, "
            f"trajectories={self.num_trajectories})"
        )


def morris_screening(
    objective_function: Callable,
    bounds: List[Tuple[float, float]],
    parameter_names: Optional[List[str]] = None,
    num_trajectories: int = 10
) -> Dict[str, Any]:
    """
    Convenience function for Morris screening
    
    Args:
        objective_function: Function to analyze
        bounds: Parameter bounds
        parameter_names: Parameter names
        num_trajectories: Number of trajectories
        
    Returns:
        Sensitivity analysis results
    """
    morris = MorrisAnalysis(
        bounds=bounds,
        objective_function=objective_function,
        parameter_names=parameter_names,
        num_trajectories=num_trajectories
    )
    
    return morris.run()
