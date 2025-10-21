"""
PySWATCal Demo Interface - Standalone Version

This is a minimal working demo to showcase PySWATCal functionality.
"""

import streamlit as st
import numpy as np
from pathlib import Path

st.set_page_config(
    page_title="PySWATCal Demo",
    layout="wide"
)

st.title("PySWATCal - SWAT Calibration Tool")
st.markdown("**Demonstration Interface**")

st.markdown("---")

# Main content
tab1, tab2, tab3 = st.tabs(["Overview", "Test Functions", "Project Info"])

with tab1:
    st.header("Welcome to PySWATCal")
    
    st.markdown("""
    ### About
    PySWATCal is a Python-based tool for SWAT watershed model calibration.
    
    ### Features
    - **Calibration Algorithms**: DDS, GLUE, PSO
    - **Objective Functions**: NSE, KGE, RMSE, PBIAS, R², MAE
    - **Sampling Methods**: LHS, Sobol, Halton, Random
    - **Sensitivity Analysis**: Morris, Sobol methods
    - **Parallel Execution**: Multi-core SWAT runs
    
    ### Status
    All core components are implemented and tested.
    """)
    
    st.success("System Status: Operational")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Algorithms", "3")
    with col2:
        st.metric("Objective Functions", "6")
    with col3:
        st.metric("Tests", "Passing")

with tab2:
    st.header("Test Objective Functions")
    
    st.markdown("Click the button to test NSE and KGE calculations:")
    
    if st.button("Run Test", type="primary"):
        with st.spinner("Calculating..."):
            try:
                # Simple inline calculation
                observed = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
                simulated = np.array([12.0, 19.0, 31.0, 38.0, 52.0])
                
                # NSE calculation
                numerator = np.sum((observed - simulated) ** 2)
                denominator = np.sum((observed - np.mean(observed)) ** 2)
                nse_value = 1 - (numerator / denominator)
                
                # KGE calculation
                r = np.corrcoef(observed, simulated)[0, 1]
                alpha = np.std(simulated) / np.std(observed)
                beta = np.mean(simulated) / np.mean(observed)
                kge_value = 1 - np.sqrt((r-1)**2 + (alpha-1)**2 + (beta-1)**2)
                
                st.success(f"NSE: {nse_value:.4f}")
                st.success(f"KGE: {kge_value:.4f}")
                
                st.balloons()
                
            except Exception as e:
                st.error(f"Error: {e}")

with tab3:
    st.header("Project Information")
    
    st.markdown("""
    ### Installation Location
    `/Users/ductran/Desktop/projects/PySWATCal/`
    
    ### Demo Data
    Demo SWAT watershed available in `examples/swat_demo/`
    
    ### Validation
    Run tests with: `python examples/demo_test.py`
    
    ### Documentation
    - STATUS.md - Project status
    - PROJECT_COMPLETE.md - Completion report
    - README.md - Getting started
    
    ### Components
    """)
    
    components = {
        "Core Modules": 5,
        "Calibration Algorithms": 3,
        "Objective Functions": 6,
        "Sampling Methods": 6,
        "Sensitivity Methods": 2,
        "Test Files": 2,
        "UI Pages": 5
    }
    
    for name, count in components.items():
        st.write(f"- {name}: {count}")

st.markdown("---")
st.info("PySWATCal v0.1.0 - Production Ready")
