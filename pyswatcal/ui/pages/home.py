"""
Home page for PySWATCal web interface
"""

import streamlit as st
from pathlib import Path


def show():
    """Display home page"""
    
    st.title("PySWATCal")
    st.subheader("SWAT Model Calibration and Analysis Tool")
    
    st.markdown("""
    ## Welcome to PySWATCal
    
    PySWATCal is a modern Python-based tool for calibrating SWAT and SWAT+ watershed models.
    It provides automated parameter optimization, sensitivity analysis, and uncertainty quantification.
    
    ### Key Features
    
    **Calibration Algorithms**
    - Dynamically Dimensioned Search (DDS)
    - Generalized Likelihood Uncertainty Estimation (GLUE)
    - Particle Swarm Optimization (PSO)
    
    **Objective Functions**
    - Nash-Sutcliffe Efficiency (NSE)
    - Kling-Gupta Efficiency (KGE)
    - Root Mean Square Error (RMSE)
    - Percent Bias (PBIAS)
    - R-squared and Mean Absolute Error
    
    **Sampling Methods**
    - Latin Hypercube Sampling
    - Sobol Sequences
    - Halton Sequences
    - Random and Grid Sampling
    
    **Analysis Tools**
    - Parallel execution for speed
    - Sensitivity analysis (Morris, Sobol)
    - Uncertainty quantification
    - Results visualization
    
    ### Getting Started
    
    1. **Project Setup**: Create a new calibration project
    2. **Parameters**: Define parameters to calibrate
    3. **Run Calibration**: Execute optimization
    4. **Results**: Analyze and visualize results
    
    ### System Requirements
    
    - Python 3.10 or higher
    - SWAT or SWAT+ executable
    - Minimum 4GB RAM recommended
    - Multi-core processor for parallel execution
    
    ### Scientific Foundation
    
    All algorithms are implemented based on peer-reviewed publications:
    - DDS: Tolson and Shoemaker (2007)
    - LHS: McKay et al. (1979)
    - NSE: Nash and Sutcliffe (1970)
    - KGE: Gupta et al. (2009)
    
    ### Support
    
    Documentation, examples, and support are available in the GitHub repository.
    """)
    
    # Quick stats if project loaded
    if st.session_state.project is not None:
        st.success("Project loaded: " + st.session_state.project.name)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Parameters", len(st.session_state.project.parameters))
        with col2:
            st.metric("Model Type", st.session_state.project.model_type)
        with col3:
            status = st.session_state.project.status
            st.metric("Status", status.capitalize())
