"""
Generalized Likelihood Uncertainty Estimation (GLUE)

Implementation of the GLUE methodology for uncertainty analysis in watershed modeling.

Reference:
    Beven, K., & Binley, A. (1992). The future of distributed models: model calibration
    and uncertainty prediction. Hydrological processes, 6(3), 279-298.
"""

import numpy as np
from typing import Callable, List, Tuple, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class GLUE:
    """
    Generalized Likelihood Uncertainty Estimation (GLUE)
    
    GLUE is a Monte Carlo-based methodology for uncertainty estimation.
    It treats all parameter sets as behavioral (acceptable) if they exceed
    a threshold performance criterion.
    
    Key Features:
    - Uncertainty quantification
    - Behavioral parameter identification
    - 95% prediction uncertainty bounds
    - No assumption of single optimal parameter set
    
    Attributes:
        bounds: Parameter bounds as list of (min, max) tuples
        objective_function: Function to evaluate model performance
        threshold: Behavioral threshold for objective function
        n_samples: Number of parameter sets to sample
    """
    
    def __init__(
        self,
        bounds: List[Tuple[float, float]],
        objective_function: Callable,
        threshold: float,
        n_samples: int = 1000,
        maximize: bool = True,
        seed: Optional[int] = None
    ):
        """
        Initialize GLUE analysis
        
        Args:
            bounds: List of (min, max) tuples for each parameter
            objective_function: Function to evaluate (takes array, returns float)
            threshold: Threshold for behavioral classification
            n_samples: Number of parameter sets to sample
            maximize: Whether higher objective values are better
            seed: Random seed for reproducibility
        """
        self.bounds = bounds
        self.n_params = len(bounds)
        self.objective_function = objective_function
        self.threshold = threshold
        self.n_samples = n_samples
        self.maximize = maximize
        self.seed = seed
        
        # Validate inputs
        if n_samples < 10:
            raise ValueError("n_samples should be at least 10")
        
        for i, (lower, upper) in enumerate(bounds):
            if lower >= upper:
                raise ValueError(f"Invalid bounds for parameter {i}: [{lower}, {upper}]")
        
        if seed is not None:
            np.random.seed(seed)
        
        # Storage for results
        self.parameter_sets = None
        self.objective_values = None
        self.behavioral_mask = None
        self.likelihood_weights = None
        
        logger.info(f"Initialized GLUE: {self.n_params} parameters, {n_samples} samples")
    
    def run(
        self,
        sampling_method: str = "lhs",
        likelihood_function: str = "threshold"
    ) -> Dict[str, Any]:
        """
        Run GLUE analysis
        
        Args:
            sampling_method: Method for sampling parameter space ('lhs', 'random')
            likelihood_function: Method for calculating likelihoods
                - 'threshold': Binary (behavioral/non-behavioral)
                - 'linear': Linear weighting above threshold
                - 'exponential': Exponential weighting
            
        Returns:
            Dictionary containing GLUE results
        """
        logger.info("Starting GLUE analysis")
        start_time = datetime.now()
        
        try:
            # Generate parameter samples
            self.parameter_sets = self._generate_samples(sampling_method)
            
            # Evaluate all parameter sets
            self.objective_values = np.zeros(self.n_samples)
            
            logger.info(f"Evaluating {self.n_samples} parameter sets...")
            for i in range(self.n_samples):
                self.objective_values[i] = self.objective_function(self.parameter_sets[i])
                
                if (i + 1) % max(1, self.n_samples // 10) == 0:
                    progress = 100 * (i + 1) / self.n_samples
                    logger.info(f"Progress: {progress:.0f}%")
            
            # Identify behavioral simulations
            self._identify_behavioral()
            
            # Calculate likelihood weights
            self._calculate_likelihoods(likelihood_function)
            
            # Calculate uncertainty bounds
            bounds_95 = self._calculate_uncertainty_bounds(percentile=95)
            bounds_90 = self._calculate_uncertainty_bounds(percentile=90)
            
            # Calculate statistics
            n_behavioral = self.behavioral_mask.sum()
            behavioral_rate = 100 * n_behavioral / self.n_samples
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"GLUE completed: {n_behavioral}/{self.n_samples} behavioral "
                f"({behavioral_rate:.1f}%), Duration: {duration:.2f}s"
            )
            
            results = {
                'parameter_sets': self.parameter_sets,
                'objective_values': self.objective_values,
                'behavioral_mask': self.behavioral_mask,
                'likelihood_weights': self.likelihood_weights,
                'n_behavioral': n_behavioral,
                'behavioral_rate': behavioral_rate,
                'threshold': self.threshold,
                'bounds_95': bounds_95,
                'bounds_90': bounds_90,
                'best_params': self.parameter_sets[np.argmax(self.objective_values)],
                'best_value': np.max(self.objective_values),
                'duration': duration,
                'success': True
            }
            
            return results
            
        except Exception as e:
            logger.error(f"GLUE analysis failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_samples(self, method: str = "lhs") -> np.ndarray:
        """Generate parameter samples"""
        if method == "lhs":
            from pyswatcal.calibration.sampling import latin_hypercube_sampling
            return latin_hypercube_sampling(self.bounds, self.n_samples, self.seed)
        else:
            # Uniform random sampling
            samples = np.zeros((self.n_samples, self.n_params))
            for i, (lower, upper) in enumerate(self.bounds):
                samples[:, i] = np.random.uniform(lower, upper, self.n_samples)
            return samples
    
    def _identify_behavioral(self) -> None:
        """Identify behavioral parameter sets based on threshold"""
        if self.maximize:
            self.behavioral_mask = self.objective_values >= self.threshold
        else:
            self.behavioral_mask = self.objective_values <= self.threshold
    
    def _calculate_likelihoods(self, method: str = "threshold") -> None:
        """Calculate likelihood weights for behavioral simulations"""
        weights = np.zeros(self.n_samples)
        
        if method == "threshold":
            # Binary weighting
            weights[self.behavioral_mask] = 1.0
            
        elif method == "linear":
            # Linear weighting above threshold
            if self.maximize:
                values = self.objective_values - self.threshold
                values[values < 0] = 0
            else:
                values = self.threshold - self.objective_values
                values[values < 0] = 0
            weights = values
            
        elif method == "exponential":
            # Exponential weighting
            if self.maximize:
                diff = self.objective_values - self.threshold
            else:
                diff = self.threshold - self.objective_values
            weights = np.exp(diff)
            weights[~self.behavioral_mask] = 0
        
        # Normalize weights
        total = weights.sum()
        if total > 0:
            weights = weights / total
        
        self.likelihood_weights = weights
    
    def _calculate_uncertainty_bounds(self, percentile: float = 95) -> Dict[str, np.ndarray]:
        """
        Calculate uncertainty bounds for parameters
        
        Args:
            percentile: Percentile for bounds (e.g., 95 for 95% bounds)
            
        Returns:
            Dictionary with lower and upper bounds for each parameter
        """
        behavioral_params = self.parameter_sets[self.behavioral_mask]
        
        if len(behavioral_params) == 0:
            return {'lower': None, 'upper': None}
        
        lower_percentile = (100 - percentile) / 2
        upper_percentile = 100 - lower_percentile
        
        lower_bounds = np.percentile(behavioral_params, lower_percentile, axis=0)
        upper_bounds = np.percentile(behavioral_params, upper_percentile, axis=0)
        
        return {
            'lower': lower_bounds,
            'upper': upper_bounds,
            'median': np.median(behavioral_params, axis=0)
        }
    
    def get_behavioral_parameters(self) -> np.ndarray:
        """Get all behavioral parameter sets"""
        if self.behavioral_mask is None:
            raise ValueError("GLUE analysis not run yet")
        return self.parameter_sets[self.behavioral_mask]
    
    def get_behavioral_statistics(self) -> Dict[str, Any]:
        """Get statistics of behavioral parameter sets"""
        behavioral = self.get_behavioral_parameters()
        
        stats = {
            'n_behavioral': len(behavioral),
            'rate': 100 * len(behavioral) / self.n_samples,
            'mean': behavioral.mean(axis=0),
            'std': behavioral.std(axis=0),
            'min': behavioral.min(axis=0),
            'max': behavioral.max(axis=0),
            'median': np.median(behavioral, axis=0)
        }
        
        return stats
    
    def __repr__(self) -> str:
        """String representation"""
        direction = "maximize" if self.maximize else "minimize"
        return (
            f"GLUE(n_params={self.n_params}, "
            f"n_samples={self.n_samples}, "
            f"threshold={self.threshold}, "
            f"{direction})"
        )


def glue_analysis(
    objective_function: Callable,
    bounds: List[Tuple[float, float]],
    threshold: float,
    n_samples: int = 1000,
    maximize: bool = True,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Convenience function for GLUE analysis
    
    Args:
        objective_function: Function to evaluate
        bounds: Parameter bounds
        threshold: Behavioral threshold
        n_samples: Number of samples
        maximize: Whether to maximize
        seed: Random seed
        
    Returns:
        GLUE results dictionary
    """
    glue = GLUE(
        bounds=bounds,
        objective_function=objective_function,
        threshold=threshold,
        n_samples=n_samples,
        maximize=maximize,
        seed=seed
    )
    
    return glue.run()
