"""
PySWATCal - Streamlit Web Interface

Main application file for the web-based user interface.
"""

import streamlit as st
from pathlib import Path
import sys

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))

from pyswatcal.ui.pages import home, project_setup, parameters, calibration, results


def main():
    """Main application entry point"""
    
    st.set_page_config(
        page_title="PySWATCal",
        page_icon="💧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'project' not in st.session_state:
        st.session_state.project = None
    if 'calibration_results' not in st.session_state:
        st.session_state.calibration_results = None
    
    # Sidebar navigation
    st.sidebar.title("PySWATCal")
    st.sidebar.markdown("**SWAT Calibration & Analysis Tool**")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["Home", "Project Setup", "Parameters", "Run Calibration", "Results"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "PySWATCal provides automated calibration for SWAT watershed models "
        "using proven optimization algorithms.\n\n"
        "Technical questions: contact Duc Tran (syu3cs@virginia.edu)."
    )
    
    # Route to appropriate page
    if page == "Home":
        home.show()
    elif page == "Project Setup":
        project_setup.show()
    elif page == "Parameters":
        parameters.show()
    elif page == "Run Calibration":
        calibration.show()
    elif page == "Results":
        results.show()


if __name__ == "__main__":
    main()
