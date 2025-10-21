"""
Demonstration and validation script using demo SWAT data

This script validates PySWATCal functionality using the included demo watershed.
"""

import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyswatcal import Project
from pyswatcal.core import FileManager
from pyswatcal.calibration import nse, kge, rmse
from pyswatcal.calibration.sampling import ParameterSampler
from pyswatcal.calibration.algorithms import DDS
from pyswatcal.utils.file_parsers import parse_file_cio, validate_txtinout_directory


def test_objective_functions():
    """Test objective functions with simple data"""
    print("\n" + "="*60)
    print("Testing Objective Functions")
    print("="*60)
    
    # Create test data
    observed = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    simulated = np.array([12.0, 19.0, 31.0, 38.0, 52.0])
    
    # Calculate all objectives
    nse_val = nse(observed, simulated)
    kge_val = kge(observed, simulated)
    rmse_val = rmse(observed, simulated)
    
    print(f"NSE: {nse_val:.4f} (expected: ~0.98)")
    print(f"KGE: {kge_val:.4f} (expected: ~0.99)")
    print(f"RMSE: {rmse_val:.4f} (expected: ~1.67)")
    
    assert 0.95 < nse_val < 1.0, "NSE value unexpected"
    assert 0.95 < kge_val < 1.0, "KGE value unexpected"
    assert 1.0 < rmse_val < 2.0, "RMSE value unexpected"
    
    print("Objective functions: PASSED\n")


def test_sampling():
    """Test parameter sampling methods"""
    print("="*60)
    print("Testing Parameter Sampling")
    print("="*60)
    
    bounds = [(0, 1), (-10, 10), (0.5, 1.5)]
    
    # Test LHS
    sampler = ParameterSampler(bounds, method="lhs", seed=42)
    samples = sampler.sample(50)
    
    print(f"LHS sampling: Generated {len(samples)} samples")
    print(f"Shape: {samples.shape}")
    print(f"Sample bounds check: {np.all(samples >= 0)} (column 0)")
    
    assert samples.shape == (50, 3), "Sample shape incorrect"
    assert np.all(samples[:, 0] >= 0) and np.all(samples[:, 0] <= 1), "Bounds violated"
    
    print("Parameter sampling: PASSED\n")


def test_dds_algorithm():
    """Test DDS optimization algorithm"""
    print("="*60)
    print("Testing DDS Algorithm")
    print("="*60)
    
    def sphere_function(x):
        """Simple sphere function"""
        return -np.sum(x ** 2)
    
    bounds = [(-5, 5), (-5, 5)]
    dds = DDS(bounds, sphere_function, n_iterations=20, maximize=True, seed=42)
    results = dds.optimize()
    
    print(f"DDS completed: Success = {results['success']}")
    print(f"Best value: {results['best_value']:.6f}")
    print(f"Best parameters: {results['best_params']}")
    print(f"Iterations: {results['n_evaluations']}")
    
    assert results['success'], "DDS failed"
    assert results['best_value'] > -1.0, "DDS did not find good solution"
    
    print("DDS algorithm: PASSED\n")


def test_demo_project():
    """Test with demo SWAT project"""
    print("="*60)
    print("Testing with Demo SWAT Project")
    print("="*60)
    
    # Path to demo SWAT project
    demo_path = Path(__file__).parent / "swat_demo" / "swat2012_rev622_demo"
    
    if not demo_path.exists():
        print(f"Demo project not found at: {demo_path}")
        print("Skipping demo project test")
        return
    
    # Validate TxtInOut
    is_valid, message = validate_txtinout_directory(demo_path)
    print(f"TxtInOut validation: {message}")
    assert is_valid, "Demo TxtInOut invalid"
    
    # Parse file.cio
    config = parse_file_cio(demo_path / "file.cio")
    print(f"Simulation years: {config.get('n_years', 'N/A')}")
    print(f"Start date: {config.get('start_date', 'N/A')}")
    print(f"End date: {config.get('end_date', 'N/A')}")
    
    assert 'n_years' in config, "Could not parse simulation years"
    
    # Create project
    project = Project.create(
        name="Demo_Test",
        working_dir=Path(__file__).parent / "test_work",
        txtinout_dir=demo_path,
        model_type="SWAT"
    )
    
    print(f"Project created: {project.name}")
    
    # Add test parameters
    project.add_parameter("CN2", ".mgt", -0.2, 0.2, "relative")
    project.add_parameter("ALPHA_BF", ".gw", 0.0, 1.0, "replace")
    
    print(f"Parameters added: {len(project.parameters)}")
    
    # Save and load
    save_path = project.save()
    print(f"Project saved to: {save_path}")
    
    loaded = Project.load(save_path)
    print(f"Project loaded: {loaded.name}")
    
    assert loaded.name == project.name, "Project load/save failed"
    
    print("Demo project test: PASSED\n")


def test_file_manager():
    """Test file manager with demo project"""
    print("="*60)
    print("Testing File Manager")
    print("="*60)
    
    demo_path = Path(__file__).parent / "swat_demo" / "swat2012_rev622_demo"
    work_path = Path(__file__).parent / "test_work"
    
    if not demo_path.exists():
        print("Demo project not found, skipping file manager test")
        return
    
    fm = FileManager(demo_path, work_path)
    print(f"Model type detected: {fm.model_type}")
    
    # Get file list
    hru_files = fm.get_file_list(extension=".hru")
    print(f"Found {len(hru_files)} HRU files")
    
    assert fm.model_type in ["SWAT", "SWAT+"], "Model type detection failed"
    assert len(hru_files) > 0, "No HRU files found"
    
    print("File manager: PASSED\n")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PySWATCal Validation Tests")
    print("="*60)
    
    try:
        test_objective_functions()
        test_sampling()
        test_dds_algorithm()
        test_demo_project()
        test_file_manager()
        
        print("="*60)
        print("ALL TESTS PASSED")
        print("="*60)
        print("\nPySWATCal is working correctly!")
        
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
