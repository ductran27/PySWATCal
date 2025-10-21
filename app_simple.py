"""
Simple PySWATCal Streamlit Interface - Minimal Version

Simplified version to test if basic Streamlit functionality works.
"""

import streamlit as st
from pathlib import Path
import sys

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Main application entry point"""
    
    st.set_page_config(
        page_title="PySWATCal",
        page_icon="💧",
        layout="wide"
    )
    
    st.title("PySWATCal - SWAT Calibration Tool")
    st.subheader("Python-based SWAT Model Calibration and Analysis")
    
    st.markdown("""
    ## Welcome to PySWATCal
    
    This is a modern Python tool for calibrating SWAT and SWAT+ watershed models.
    
    ### Features
    - Three calibration algorithms: DDS, GLUE, PSO
    - Six objective functions: NSE, KGE, RMSE, PBIAS, R², MAE
    - Multiple sampling methods: LHS, Sobol, Halton
    - Sensitivity analysis: Morris, Sobol
    - Parallel execution support
    - Interactive results visualization
    
    ### Status
    **All core components implemented and tested**
    
    - Core infrastructure: Complete
    - Calibration algorithms: Complete  
    - Sensitivity analysis: Complete
    - Output parsers: Complete
    - Demo data: Available
    - Tests: All passing
    
    ### Quick Test
    """)
    
    if st.button("Test Objective Functions"):
        try:
            from pyswatcal.calibration import nse, kge
            import numpy as np
            
            observed = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
            simulated = np.array([12.0, 19.0, 31.0, 38.0, 52.0])
            
            nse_val = nse(observed, simulated)
            kge_val = kge(observed, simulated)
            
            st.success(f"NSE: {nse_val:.4f}")
            st.success(f"KGE: {kge_val:.4f}")
            st.balloons()
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.markdown("""
    ### Documentation
    
    Complete documentation is available in the project directory:
    - STATUS.md - Current project status
    - PROJECT_COMPLETE.md - Full completion report
    - README.md - Getting started guide
    
    ### Demo Data
    
    Demo SWAT watershed (Little River) is available in the examples directory.
    Run `python examples/demo_test.py` to validate the installation.
    """)


if __name__ == "__main__":
    main()
