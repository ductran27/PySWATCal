"""
Objective functions for model calibration

Implements common objective functions used in hydrological model calibration:
- NSE (Nash-Sutcliffe Efficiency)
- KGE (Kling-Gupta Efficiency)
- RMSE (Root Mean Square Error)
- PBIAS (Percent Bias)
- R² (Coefficient of Determination)
"""

import numpy as np
from typing import Union, Callable, Dict, Any
from enum import Enum


class ObjectiveFunctionType(str, Enum):
    """Types of objective functions"""
    NSE = "NSE"
    KGE = "KGE"
    RMSE = "RMSE"
    PBIAS = "PBIAS"
    R2 = "R2"


def nse(observed: np.ndarray, simulated: np.ndarray, handle_nan: str = "ignore") -> float:
    """
    Calculate Nash-Sutcliffe Efficiency (NSE)
    
    NSE = 1 - sum((obs - sim)²) / sum((obs - mean(obs))²)
    
    Range: -∞ to 1, where 1 is perfect, 0 means model is as good as mean,
    negative values mean model is worse than mean.
    
    Args:
        observed: Observed values
        simulated: Simulated values
        handle_nan: How to handle NaN values ('ignore', 'raise', 'propagate')
        
    Returns:
        NSE value
        
    Reference:
        Nash & Sutcliffe (1970). River flow forecasting through conceptual models
        part I — A discussion of principles. Journal of Hydrology, 10(3), 282-290.
    """
    observed, simulated = _validate_inputs(observed, simulated, handle_nan)
    
    if len(observed) == 0:
        return np.nan
    
    numerator = np.sum((observed - simulated) ** 2)
    denominator = np.sum((observed - np.mean(observed)) ** 2)
    
    if denominator == 0:
        return np.nan
    
    return 1 - (numerator / denominator)


def kge(
    observed: np.ndarray,
    simulated: np.ndarray,
    handle_nan: str = "ignore",
    weights: tuple = (1.0, 1.0, 1.0)
) -> float:
    """
    Calculate Kling-Gupta Efficiency (KGE)
    
    KGE = 1 - sqrt((r-1)² + (α-1)² + (β-1)²)
    where:
        r = correlation coefficient
        α = std(sim) / std(obs)
        β = mean(sim) / mean(obs)
    
    Range: -∞ to 1, where 1 is perfect
    
    Args:
        observed: Observed values
        simulated: Simulated values
        handle_nan: How to handle NaN values
        weights: Weights for (r, α, β) components
        
    Returns:
        KGE value
        
    Reference:
        Gupta et al. (2009). Decomposition of the mean squared error and NSE 
        performance criteria: Implications for improving hydrological modelling.
        Journal of Hydrology, 377(1-2), 80-91.
    """
    observed, simulated = _validate_inputs(observed, simulated, handle_nan)
    
    if len(observed) == 0:
        return np.nan
    
    # Correlation coefficient
    r = np.corrcoef(observed, simulated)[0, 1]
    
    # Variability ratio
    alpha = np.std(simulated) / np.std(observed) if np.std(observed) != 0 else np.nan
    
    # Bias ratio
    beta = np.mean(simulated) / np.mean(observed) if np.mean(observed) != 0 else np.nan
    
    if np.isnan(alpha) or np.isnan(beta) or np.isnan(r):
        return np.nan
    
    # Weighted Euclidean distance
    w_r, w_alpha, w_beta = weights
    ed = np.sqrt(
        w_r * (r - 1) ** 2 +
        w_alpha * (alpha - 1) ** 2 +
        w_beta * (beta - 1) ** 2
    )
    
    return 1 - ed


def rmse(observed: np.ndarray, simulated: np.ndarray, handle_nan: str = "ignore") -> float:
    """
    Calculate Root Mean Square Error (RMSE)
    
    RMSE = sqrt(mean((obs - sim)²))
    
    Range: 0 to ∞, where 0 is perfect
    Lower values are better.
    
    Args:
        observed: Observed values
        simulated: Simulated values
        handle_nan: How to handle NaN values
        
    Returns:
        RMSE value
    """
    observed, simulated = _validate_inputs(observed, simulated, handle_nan)
    
    if len(observed) == 0:
        return np.nan
    
    return np.sqrt(np.mean((observed - simulated) ** 2))


def pbias(observed: np.ndarray, simulated: np.ndarray, handle_nan: str = "ignore") -> float:
    """
    Calculate Percent Bias (PBIAS)
    
    PBIAS = 100 * sum(sim - obs) / sum(obs)
    
    Range: -∞ to ∞, where 0 is perfect
    Positive values indicate model overestimation.
    Negative values indicate model underestimation.
    
    Args:
        observed: Observed values
        simulated: Simulated values
        handle_nan: How to handle NaN values
        
    Returns:
        PBIAS value (percentage)
    """
    observed, simulated = _validate_inputs(observed, simulated, handle_nan)
    
    if len(observed) == 0:
        return np.nan
    
    sum_obs = np.sum(observed)
    if sum_obs == 0:
        return np.nan
    
    return 100 * np.sum(simulated - observed) / sum_obs


def r_squared(observed: np.ndarray, simulated: np.ndarray, handle_nan: str = "ignore") -> float:
    """
    Calculate Coefficient of Determination (R²)
    
    R² = (correlation coefficient)²
    
    Range: 0 to 1, where 1 is perfect
    
    Args:
        observed: Observed values
        simulated: Simulated values
        handle_nan: How to handle NaN values
        
    Returns:
        R² value
    """
    observed, simulated = _validate_inputs(observed, simulated, handle_nan)
    
    if len(observed) == 0:
        return np.nan
    
    correlation = np.corrcoef(observed, simulated)[0, 1]
    return correlation ** 2


def mae(observed: np.ndarray, simulated: np.ndarray, handle_nan: str = "ignore") -> float:
    """
    Calculate Mean Absolute Error (MAE)
    
    MAE = mean(|obs - sim|)
    
    Range: 0 to ∞, where 0 is perfect
    
    Args:
        observed: Observed values
        simulated: Simulated values
        handle_nan: How to handle NaN values
        
    Returns:
        MAE value
    """
    observed, simulated = _validate_inputs(observed, simulated, handle_nan)
    
    if len(observed) == 0:
        return np.nan
    
    return np.mean(np.abs(observed - simulated))


def _validate_inputs(
    observed: np.ndarray,
    simulated: np.ndarray,
    handle_nan: str = "ignore"
) -> tuple:
    """
    Validate and prepare inputs for objective function calculation
    
    Args:
        observed: Observed values
        simulated: Simulated values
        handle_nan: How to handle NaN values
        
    Returns:
        Tuple of (observed, simulated) arrays
    """
    # Convert to numpy arrays
    observed = np.asarray(observed, dtype=float)
    simulated = np.asarray(simulated, dtype=float)
    
    # Check shapes match
    if observed.shape != simulated.shape:
        raise ValueError(
            f"Shape mismatch: observed {observed.shape} vs simulated {simulated.shape}"
        )
    
    # Handle NaN values
    if handle_nan == "raise":
        if np.any(np.isnan(observed)) or np.any(np.isnan(simulated)):
            raise ValueError("NaN values found in input arrays")
    elif handle_nan == "ignore":
        # Remove pairs where either value is NaN
        mask = ~(np.isnan(observed) | np.isnan(simulated))
        observed = observed[mask]
        simulated = simulated[mask]
    elif handle_nan == "propagate":
        # Let NaN propagate through calculations
        pass
    else:
        raise ValueError(f"Unknown handle_nan option: {handle_nan}")
    
    return observed, simulated


class ObjectiveFunction:
    """
    Objective function wrapper for calibration
    
    Provides a unified interface for different objective functions
    with options for normalization, transformation, etc.
    """
    
    def __init__(
        self,
        function_type: Union[ObjectiveFunctionType, str, Callable],
        minimize: bool = False,
        transform: str = "none",
        weights: tuple = (1.0, 1.0, 1.0)
    ):
        """
        Initialize objective function
        
        Args:
            function_type: Type of objective function or custom callable
            minimize: Whether to minimize (True) or maximize (False)
            transform: Transformation to apply ('none', 'log', 'sqrt')
            weights: Weights for KGE components (if using KGE)
        """
        self.function_type = function_type
        self.minimize = minimize
        self.transform = transform
        self.weights = weights
        
        # Get the actual function
        if callable(function_type):
            self._function = function_type
            self.name = function_type.__name__
        else:
            function_map = {
                "NSE": nse,
                "KGE": kge,
                "RMSE": rmse,
                "PBIAS": pbias,
                "R2": r_squared,
                "MAE": mae,
            }
            if isinstance(function_type, str):
                function_type = function_type.upper()
            
            if function_type not in function_map:
                raise ValueError(f"Unknown objective function: {function_type}")
            
            self._function = function_map[function_type]
            self.name = function_type
    
    def calculate(
        self,
        observed: np.ndarray,
        simulated: np.ndarray,
        handle_nan: str = "ignore"
    ) -> float:
        """
        Calculate objective function value
        
        Args:
            observed: Observed values
            simulated: Simulated values
            handle_nan: How to handle NaN values
            
        Returns:
            Objective function value
        """
        # Apply transformation if specified
        if self.transform == "log":
            observed = np.log(observed + 1e-10)  # Add small value to avoid log(0)
            simulated = np.log(simulated + 1e-10)
        elif self.transform == "sqrt":
            observed = np.sqrt(np.maximum(observed, 0))
            simulated = np.sqrt(np.maximum(simulated, 0))
        
        # Calculate objective function
        if self.name == "KGE":
            value = self._function(observed, simulated, handle_nan, self.weights)
        else:
            value = self._function(observed, simulated, handle_nan)
        
        # Invert if minimizing (for functions where higher is better)
        if self.minimize and self.name in ["NSE", "KGE", "R2"]:
            value = -value
        elif not self.minimize and self.name in ["RMSE", "MAE"]:
            value = -value
        
        return value
    
    def __call__(self, observed: np.ndarray, simulated: np.ndarray) -> float:
        """Allow instance to be called like a function"""
        return self.calculate(observed, simulated)
    
    def __repr__(self) -> str:
        """String representation"""
        direction = "minimize" if self.minimize else "maximize"
        return f"ObjectiveFunction({self.name}, {direction})"


def calculate_multiple_objectives(
    observed: np.ndarray,
    simulated: np.ndarray,
    functions: list = None
) -> Dict[str, float]:
    """
    Calculate multiple objective functions at once
    
    Args:
        observed: Observed values
        simulated: Simulated values
        functions: List of objective function names or ObjectiveFunction instances
        
    Returns:
        Dictionary of objective function names and values
    """
    if functions is None:
        functions = ["NSE", "KGE", "RMSE", "PBIAS", "R2"]
    
    results = {}
    
    for func in functions:
        if isinstance(func, ObjectiveFunction):
            results[func.name] = func.calculate(observed, simulated)
        elif isinstance(func, str):
            obj_func = ObjectiveFunction(func)
            results[func] = obj_func.calculate(observed, simulated)
        else:
            raise ValueError(f"Invalid function type: {type(func)}")
    
    return results
