"""
Sobol sensitivity analysis

Implementation using SALib for variance-based global sensitivity analysis.

Reference:
    Sobol, I. M. (2001). Global sensitivity indices for nonlinear mathematical models
    and their Monte Carlo estimates. Mathematics and computers in simulation, 55(1-3), 271-280.
"""

import numpy as np
from typing import Callable, List, Tuple, Dict, Any, Optional
import logging
from SALib.sample import saltelli
from SALib.analyze import sobol

logger = logging.getLogger(__name__)


class SobolAnalysis:
    """
    Sobol variance-based sensitivity analysis
    
    Computes first-order and total-order Sobol sensitivity indices
    for quantitative parameter importance ranking.
    
    Key Features:
    - Quantitative sensitivity indices
    - First-order effects (individual parameter)
    - Total-order effects (with interactions)
    - Variance decomposition
    
    Attributes:
        bounds: Parameter bounds
        objective_function: Function to analyze
        n_samples: Base sample size for Saltelli sampling
    """
    
    def __init__(
        self,
        bounds: List[Tuple[float, float]],
        objective_function: Callable,
        parameter_names: Optional[List[str]] = None,
        n_samples: int = 1024,
        seed: Optional[int] = None
    ):
        """
        Initialize Sobol analysis
        
        Args:
            bounds: List of (min, max) tuples for parameters
            objective_function: Function to evaluate
            parameter_names: Names of parameters
            n_samples: Base sample size (actual samples will be n*(2D+2))
            seed: Random seed
        """
        self.bounds = bounds
        self.n_params = len(bounds)
        self.objective_function = objective_function
        self.n_samples = n_samples
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
        
        # Actual number of samples will be n_samples * (2 * D + 2)
        total_samples = n_samples * (2 * self.n_params + 2)
        
        logger.info(
            f"Initialized Sobol analysis: {self.n_params} parameters, "
            f"{total_samples} total samples"
        )
    
    def run(self, calc_second_order: bool = False) -> Dict[str, Any]:
        """
        Run Sobol sensitivity analysis
        
        Args:
            calc_second_order: Whether to calculate second-order indices
            
        Returns:
            Dictionary containing sensitivity results
        """
        logger.info("Starting Sobol sensitivity analysis")
        
        try:
            # Generate samples using Saltelli sampling scheme
            parameter_values = saltelli.sample(
                self.problem,
                N=self.n_samples,
                calc_second_order=calc_second_order,
                seed=self.seed
            )
            
            n_samples = len(parameter_values)
            logger.info(f"Generated {n_samples} sample points")
            
            # Evaluate model at all sample points
            outputs = np.zeros(n_samples)
            
            for i, params in enumerate(parameter_values):
                outputs[i] = self.objective_function(params)
                
                if (i + 1) % max(1, n_samples // 20) == 0:
                    progress = 100 * (i + 1) / n_samples
                    logger.info(f"Progress: {progress:.0f}%")
            
            # Analyze results
            Si = sobol.analyze(
                self.problem,
                outputs,
                calc_second_order=calc_second_order,
                seed=self.seed
            )
            
            # Package results
            results = {
                'S1': Si['S1'],  # First-order indices
                'S1_conf': Si['S1_conf'],  # Confidence intervals for S1
                'ST': Si['ST'],  # Total-order indices
                'ST_conf': Si['ST_conf'],  # Confidence intervals for ST
                'parameter_names': self.parameter_names,
                'n_samples': n_samples,
                'success': True
            }
            
            # Add second-order indices if calculated
            if calc_second_order and 'S2' in Si:
                results['S2'] = Si['S2']
                results['S2_conf'] = Si['S2_conf']
            
            # Rank parameters by total-order index
            ranking = np.argsort(Si['ST'])[::-1]
            results['ranking'] = ranking
            results['ranked_parameters'] = [self.parameter_names[i] for i in ranking]
            
            logger.info("Sobol analysis completed")
            return results
            
        except Exception as e:
            logger.error(f"Sobol analysis failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_sensitivity_indices(self) -> Dict[str, Dict[str, float]]:
        """
        Get sensitivity indices in dict form
        
        Returns:
            Dictionary with S1 and ST for each parameter
        """
        results = self.run()
        
        if not results['success']:
            raise ValueError("Analysis failed")
        
        indices = {}
        for i, name in enumerate(self.parameter_names):
            indices[name] = {
                'S1': results['S1'][i],
                'ST': results['ST'][i],
                'S1_conf': results['S1_conf'][i],
                'ST_conf': results['ST_conf'][i]
            }
        
        return indices
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"SobolAnalysis(n_params={self.n_params}, "
            f"n_samples={self.n_samples})"
        )


def sobol_indices(
    objective_function: Callable,
    bounds: List[Tuple[float, float]],
    parameter_names: Optional[List[str]] = None,
    n_samples: int = 1024
) -> Dict[str, Any]:
    """
    Convenience function for Sobol analysis
    
    Args:
        objective_function: Function to analyze
        bounds: Parameter bounds
        parameter_names: Parameter names
        n_samples: Base sample size
        
    Returns:
        Sensitivity analysis results
    """
    sobol_analysis = SobolAnalysis(
        bounds=bounds,
        objective_function=objective_function,
        parameter_names=parameter_names,
        n_samples=n_samples
    )
    
    return sobol_analysis.run()
