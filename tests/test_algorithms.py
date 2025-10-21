"""
Tests for calibration algorithms
"""

import pytest
import numpy as np
from pyswatcal.calibration.algorithms import DDS, GLUE, PSO


def simple_quadratic(x):
    """Simple test function: minimize sum of squares"""
    return -np.sum(x ** 2)


def rosenbrock(x):
    """Rosenbrock function for testing"""
    return -(100 * (x[1] - x[0]**2)**2 + (1 - x[0])**2)


class TestDDS:
    """Test suite for DDS algorithm"""
    
    def test_dds_initialization(self):
        """Test DDS can be initialized"""
        bounds = [(0, 1), (-5, 5)]
        dds = DDS(bounds, simple_quadratic, n_iterations=10)
        assert dds.n_params == 2
        assert dds.n_iterations == 10
    
    def test_dds_optimize(self):
        """Test DDS can run optimization"""
        bounds = [(-5, 5), (-5, 5)]
        dds = DDS(bounds, rosenbrock, n_iterations=20, maximize=True)
        results = dds.optimize()
        
        assert results['success']
        assert 'best_params' in results
        assert 'best_value' in results
        assert len(results['best_params']) == 2
    
    def test_dds_history(self):
        """Test DDS records history"""
        bounds = [(0, 1)]
        dds = DDS(bounds, simple_quadratic, n_iterations=10)
        results = dds.optimize()
        
        assert len(results['history']['iteration']) == 11  # 0 to n_iterations
        assert len(results['history']['best_value']) == 11


class TestGLUE:
    """Test suite for GLUE algorithm"""
    
    def test_glue_initialization(self):
        """Test GLUE can be initialized"""
        bounds = [(0, 1), (-5, 5)]
        glue = GLUE(bounds, simple_quadratic, threshold=-1.0, n_samples=50)
        assert glue.n_params == 2
        assert glue.n_samples == 50
    
    def test_glue_run(self):
        """Test GLUE can run analysis"""
        bounds = [(-2, 2), (-2, 2)]
        glue = GLUE(bounds, simple_quadratic, threshold=-2.0, n_samples=100)
        results = glue.run()
        
        assert results['success']
        assert 'behavioral_mask' in results
        assert 'likelihood_weights' in results
        assert results['n_behavioral'] > 0


class TestPSO:
    """Test suite for PSO algorithm"""
    
    def test_pso_initialization(self):
        """Test PSO can be initialized"""
        bounds = [(0, 1), (-5, 5)]
        pso = PSO(bounds, simple_quadratic, n_particles=10, n_iterations=10)
        assert pso.n_params == 2
        assert pso.n_particles == 10
    
    def test_pso_optimize(self):
        """Test PSO can run optimization"""
        bounds = [(-5, 5), (-5, 5)]
        pso = PSO(bounds, rosenbrock, n_particles=20, n_iterations=30, maximize=True)
        results = pso.optimize()
        
        assert results['success']
        assert 'best_params' in results
        assert 'best_value' in results
        assert len(results['best_params']) == 2
    
    def test_pso_bounds(self):
        """Test PSO respects parameter bounds"""
        bounds = [(0, 1), (0, 1)]
        pso = PSO(bounds, simple_quadratic, n_particles=10, n_iterations=5)
        results = pso.optimize()
        
        # Check all best parameters are within bounds
        for i, (lower, upper) in enumerate(bounds):
            assert lower <= results['best_params'][i] <= upper


if __name__ == "__main__":
    pytest.main([__file__])
