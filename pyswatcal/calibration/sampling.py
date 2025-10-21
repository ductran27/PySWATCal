"""
Parameter sampling methods for calibration

Implements various sampling strategies:
- Latin Hypercube Sampling (LHS)
- Sobol Sequence
- Random Sampling
- Uniform Grid
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from scipy.stats import qmc
import logging

logger = logging.getLogger(__name__)


def latin_hypercube_sampling(
    bounds: List[Tuple[float, float]],
    n_samples: int,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate samples using Latin Hypercube Sampling (LHS)
    
    LHS ensures good coverage of the parameter space by dividing
    each parameter dimension into n_samples equally probable intervals
    and sampling once from each interval.
    
    Args:
        bounds: List of (min, max) tuples for each parameter
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility
        
    Returns:
        Array of shape (n_samples, n_parameters) with sampled values
        
    Example:
        >>> bounds = [(0, 1), (-10, 10), (0.5, 1.5)]
        >>> samples = latin_hypercube_sampling(bounds, n_samples=100)
        >>> samples.shape
        (100, 3)
    """
    n_params = len(bounds)
    
    # Create LHS sampler
    sampler = qmc.LatinHypercube(d=n_params, seed=seed)
    
    # Generate samples in [0, 1]^d
    samples_unit = sampler.random(n=n_samples)
    
    # Scale to actual bounds
    samples = np.zeros_like(samples_unit)
    for i, (lower, upper) in enumerate(bounds):
        samples[:, i] = lower + (upper - lower) * samples_unit[:, i]
    
    logger.info(f"Generated {n_samples} LHS samples for {n_params} parameters")
    return samples


def sobol_sampling(
    bounds: List[Tuple[float, float]],
    n_samples: int,
    seed: Optional[int] = None,
    scramble: bool = True
) -> np.ndarray:
    """
    Generate samples using Sobol sequence
    
    Sobol sequence is a low-discrepancy quasi-random sequence that
    provides better space-filling properties than random sampling.
    
    Args:
        bounds: List of (min, max) tuples for each parameter
        n_samples: Number of samples to generate (should be power of 2 for best results)
        seed: Random seed for reproducibility
        scramble: Whether to scramble the sequence (recommended)
        
    Returns:
        Array of shape (n_samples, n_parameters) with sampled values
        
    Note:
        For best results, n_samples should be a power of 2 (e.g., 64, 128, 256)
    """
    n_params = len(bounds)
    
    # Create Sobol sampler
    sampler = qmc.Sobol(d=n_params, scramble=scramble, seed=seed)
    
    # Generate samples in [0, 1]^d
    samples_unit = sampler.random(n=n_samples)
    
    # Scale to actual bounds
    samples = np.zeros_like(samples_unit)
    for i, (lower, upper) in enumerate(bounds):
        samples[:, i] = lower + (upper - lower) * samples_unit[:, i]
    
    logger.info(f"Generated {n_samples} Sobol samples for {n_params} parameters")
    return samples


def uniform_random_sampling(
    bounds: List[Tuple[float, float]],
    n_samples: int,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate samples using uniform random sampling
    
    Simple random sampling from uniform distribution within bounds.
    
    Args:
        bounds: List of (min, max) tuples for each parameter
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility
        
    Returns:
        Array of shape (n_samples, n_parameters) with sampled values
    """
    if seed is not None:
        np.random.seed(seed)
    
    n_params = len(bounds)
    samples = np.zeros((n_samples, n_params))
    
    for i, (lower, upper) in enumerate(bounds):
        samples[:, i] = np.random.uniform(lower, upper, size=n_samples)
    
    logger.info(f"Generated {n_samples} random samples for {n_params} parameters")
    return samples


def uniform_grid_sampling(
    bounds: List[Tuple[float, float]],
    n_samples_per_dim: int
) -> np.ndarray:
    """
    Generate samples on a uniform grid
    
    Creates a regular grid of samples. Total number of samples will be
    n_samples_per_dim^n_parameters.
    
    Args:
        bounds: List of (min, max) tuples for each parameter
        n_samples_per_dim: Number of samples per dimension
        
    Returns:
        Array of shape (n_samples_per_dim^n_params, n_parameters)
        
    Warning:
        This can quickly become computationally expensive for high dimensions
    """
    n_params = len(bounds)
    
    # Create 1D grids for each parameter
    grids_1d = []
    for lower, upper in bounds:
        grids_1d.append(np.linspace(lower, upper, n_samples_per_dim))
    
    # Create meshgrid
    mesh = np.meshgrid(*grids_1d, indexing='ij')
    
    # Flatten and stack
    samples = np.column_stack([m.ravel() for m in mesh])
    
    n_total = n_samples_per_dim ** n_params
    logger.info(f"Generated {n_total} grid samples for {n_params} parameters")
    logger.warning(f"Grid sampling with {n_params} parameters creates {n_total} samples")
    
    return samples


def halton_sampling(
    bounds: List[Tuple[float, float]],
    n_samples: int,
    seed: Optional[int] = None,
    scramble: bool = True
) -> np.ndarray:
    """
    Generate samples using Halton sequence
    
    Halton sequence is another low-discrepancy quasi-random sequence.
    
    Args:
        bounds: List of (min, max) tuples for each parameter
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility
        scramble: Whether to scramble the sequence
        
    Returns:
        Array of shape (n_samples, n_parameters) with sampled values
    """
    n_params = len(bounds)
    
    # Create Halton sampler
    sampler = qmc.Halton(d=n_params, scramble=scramble, seed=seed)
    
    # Generate samples in [0, 1]^d
    samples_unit = sampler.random(n=n_samples)
    
    # Scale to actual bounds
    samples = np.zeros_like(samples_unit)
    for i, (lower, upper) in enumerate(bounds):
        samples[:, i] = lower + (upper - lower) * samples_unit[:, i]
    
    logger.info(f"Generated {n_samples} Halton samples for {n_params} parameters")
    return samples


def stratified_sampling(
    bounds: List[Tuple[float, float]],
    n_samples: int,
    n_strata_per_dim: int,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate samples using stratified sampling
    
    Divides each dimension into strata and samples from each stratum.
    
    Args:
        bounds: List of (min, max) tuples for each parameter
        n_samples: Number of samples to generate
        n_strata_per_dim: Number of strata per dimension
        seed: Random seed for reproducibility
        
    Returns:
        Array of shape (n_samples, n_parameters) with sampled values
    """
    if seed is not None:
        np.random.seed(seed)
    
    n_params = len(bounds)
    samples = []
    
    # Calculate samples per stratum
    n_strata_total = n_strata_per_dim ** n_params
    samples_per_stratum = max(1, n_samples // n_strata_total)
    
    # Generate strata indices
    strata_indices = np.array(np.unravel_index(
        range(n_strata_total),
        (n_strata_per_dim,) * n_params
    )).T
    
    for stratum_idx in strata_indices:
        for _ in range(samples_per_stratum):
            sample = []
            for i, (lower, upper) in enumerate(bounds):
                # Calculate stratum bounds
                stratum_width = (upper - lower) / n_strata_per_dim
                stratum_lower = lower + stratum_idx[i] * stratum_width
                stratum_upper = stratum_lower + stratum_width
                
                # Sample within stratum
                value = np.random.uniform(stratum_lower, stratum_upper)
                sample.append(value)
            
            samples.append(sample)
            
            if len(samples) >= n_samples:
                break
        
        if len(samples) >= n_samples:
            break
    
    samples = np.array(samples[:n_samples])
    logger.info(f"Generated {len(samples)} stratified samples for {n_params} parameters")
    return samples


class ParameterSampler:
    """
    Unified interface for parameter sampling
    
    Provides a consistent API for different sampling methods with
    additional utilities for parameter space exploration.
    """
    
    def __init__(
        self,
        bounds: List[Tuple[float, float]],
        method: str = "lhs",
        seed: Optional[int] = None
    ):
        """
        Initialize parameter sampler
        
        Args:
            bounds: List of (min, max) tuples for each parameter
            method: Sampling method ('lhs', 'sobol', 'random', 'grid', 'halton')
            seed: Random seed for reproducibility
        """
        self.bounds = bounds
        self.n_params = len(bounds)
        self.method = method.lower()
        self.seed = seed
        
        # Validate bounds
        for i, (lower, upper) in enumerate(bounds):
            if lower >= upper:
                raise ValueError(f"Invalid bounds for parameter {i}: [{lower}, {upper}]")
    
    def sample(self, n_samples: int, **kwargs) -> np.ndarray:
        """
        Generate samples using the configured method
        
        Args:
            n_samples: Number of samples to generate
            **kwargs: Additional method-specific arguments
            
        Returns:
            Array of shape (n_samples, n_parameters)
        """
        if self.method == "lhs":
            return latin_hypercube_sampling(self.bounds, n_samples, self.seed)
        elif self.method == "sobol":
            scramble = kwargs.get("scramble", True)
            return sobol_sampling(self.bounds, n_samples, self.seed, scramble)
        elif self.method == "random":
            return uniform_random_sampling(self.bounds, n_samples, self.seed)
        elif self.method == "grid":
            n_per_dim = int(np.ceil(n_samples ** (1 / self.n_params)))
            return uniform_grid_sampling(self.bounds, n_per_dim)
        elif self.method == "halton":
            scramble = kwargs.get("scramble", True)
            return halton_sampling(self.bounds, n_samples, self.seed, scramble)
        elif self.method == "stratified":
            n_strata = kwargs.get("n_strata_per_dim", 5)
            return stratified_sampling(self.bounds, n_samples, n_strata, self.seed)
        else:
            raise ValueError(f"Unknown sampling method: {self.method}")
    
    def get_bounds_array(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get bounds as numpy arrays
        
        Returns:
            Tuple of (lower_bounds, upper_bounds) arrays
        """
        lower = np.array([b[0] for b in self.bounds])
        upper = np.array([b[1] for b in self.bounds])
        return lower, upper
    
    def scale_to_unit(self, samples: np.ndarray) -> np.ndarray:
        """
        Scale samples from original bounds to [0, 1]^d
        
        Args:
            samples: Array of samples in original bounds
            
        Returns:
            Array of samples scaled to unit hypercube
        """
        scaled = np.zeros_like(samples)
        for i, (lower, upper) in enumerate(self.bounds):
            scaled[:, i] = (samples[:, i] - lower) / (upper - lower)
        return scaled
    
    def scale_from_unit(self, samples_unit: np.ndarray) -> np.ndarray:
        """
        Scale samples from [0, 1]^d to original bounds
        
        Args:
            samples_unit: Array of samples in unit hypercube
            
        Returns:
            Array of samples in original bounds
        """
        scaled = np.zeros_like(samples_unit)
        for i, (lower, upper) in enumerate(self.bounds):
            scaled[:, i] = lower + (upper - lower) * samples_unit[:, i]
        return scaled
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ParameterSampler(method='{self.method}', n_params={self.n_params}, seed={self.seed})"
