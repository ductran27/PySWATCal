"""
Tests for objective functions
"""

import pytest
import numpy as np
from pyswatcal.calibration.objective_functions import nse, kge, rmse, pbias, r_squared, mae


class TestObjectiveFunctions:
    """Test suite for objective functions"""
    
    def test_nse_perfect(self):
        """Test NSE with perfect match"""
        observed = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        simulated = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = nse(observed, simulated)
        assert abs(result - 1.0) < 1e-10
    
    def test_nse_mean_model(self):
        """Test NSE equals 0 when simulation equals mean"""
        observed = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mean_val = observed.mean()
        simulated = np.array([mean_val] * 5)
        
        result = nse(observed, simulated)
        assert abs(result) < 1e-10
    
    def test_kge_perfect(self):
        """Test KGE with perfect match"""
        observed = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        simulated = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = kge(observed, simulated)
        assert abs(result - 1.0) < 1e-10
    
    def test_rmse_perfect(self):
        """Test RMSE with perfect match"""
        observed = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        simulated = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = rmse(observed, simulated)
        assert abs(result) < 1e-10
    
    def test_pbias_perfect(self):
        """Test PBIAS with perfect match"""
        observed = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        simulated = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = pbias(observed, simulated)
        assert abs(result) < 1e-10
    
    def test_r_squared_perfect(self):
        """Test R-squared with perfect match"""
        observed = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        simulated = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = r_squared(observed, simulated)
        assert abs(result - 1.0) < 1e-10
    
    def test_mae_perfect(self):
        """Test MAE with perfect match"""
        observed = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        simulated = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = mae(observed, simulated)
        assert abs(result) < 1e-10
    
    def test_nse_realistic(self):
        """Test NSE with realistic data"""
        observed = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        simulated = np.array([12.0, 19.0, 31.0, 38.0, 52.0])
        
        result = nse(observed, simulated)
        assert 0.9 < result < 1.0
    
    def test_nan_handling_ignore(self):
        """Test NaN handling with ignore option"""
        observed = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        simulated = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = nse(observed, simulated, handle_nan='ignore')
        assert not np.isnan(result)
    
    def test_shape_mismatch(self):
        """Test error on shape mismatch"""
        observed = np.array([1.0, 2.0, 3.0])
        simulated = np.array([1.0, 2.0, 3.0, 4.0])
        
        with pytest.raises(ValueError):
            nse(observed, simulated)


if __name__ == "__main__":
    pytest.main([__file__])
