"""
Parameters configuration page
"""

import streamlit as st
import pandas as pd


def show():
    """Display parameters configuration page"""
    
    st.title("Parameter Configuration")
    
    if st.session_state.project is None:
        st.warning("Please create or load a project first")
        return
    
    project = st.session_state.project
    
    st.markdown(f"**Current Project**: {project.name}")
    st.markdown("---")
    
    # Add new parameter section
    st.subheader("Add Parameter")
    
    col1, col2 = st.columns(2)
    
    with col1:
        param_name = st.text_input("Parameter Name", help="e.g., CN2, ALPHA_BF, GW_DELAY")
        file_type = st.selectbox(
            "File Type",
            [".mgt", ".gw", ".hru", ".sol", ".rte", ".bsn", ".sub"],
            help="File extension where parameter is located"
        )
        change_type = st.selectbox(
            "Change Type",
            ["relative", "replace", "absolute"],
            help="How to apply parameter changes"
        )
    
    with col2:
        min_value = st.number_input("Minimum Value", value=-0.2)
        max_value = st.number_input("Maximum Value", value=0.2)
        description = st.text_input("Description (optional)")
    
    if st.button("Add Parameter"):
        if not param_name:
            st.error("Please enter parameter name")
        elif min_value >= max_value:
            st.error("Minimum value must be less than maximum value")
        else:
            try:
                project.add_parameter(
                    name=param_name,
                    file_type=file_type,
                    min_value=min_value,
                    max_value=max_value,
                    change_type=change_type,
                    description=description
                )
                st.success(f"Added parameter: {param_name}")
                project.save()
                st.rerun()
            except Exception as e:
                st.error(f"Error adding parameter: {e}")
    
    # Display current parameters
    st.markdown("---")
    st.subheader("Current Parameters")
    
    if len(project.parameters) == 0:
        st.info("No parameters defined yet")
    else:
        # Create DataFrame for display
        param_data = []
        for param in project.parameters:
            param_data.append({
                "Parameter": param.name,
                "File Type": param.file_type,
                "Min": param.min_value,
                "Max": param.max_value,
                "Change Type": param.change_type,
                "Description": param.description
            })
        
        df = pd.DataFrame(param_data)
        st.dataframe(df, use_container_width=True)
        
        # Remove parameter
        st.markdown("### Remove Parameter")
        param_to_remove = st.selectbox(
            "Select parameter to remove",
            [p.name for p in project.parameters]
        )
        
        if st.button("Remove Selected Parameter"):
            if project.remove_parameter(param_to_remove):
                st.success(f"Removed parameter: {param_to_remove}")
                project.save()
                st.rerun()
            else:
                st.error(f"Parameter not found: {param_to_remove}")
    
    # Calibration settings
    st.markdown("---")
    st.subheader("Calibration Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        method = st.selectbox(
            "Calibration Method",
            ["DDS", "GLUE", "PSO"],
            help="Optimization algorithm to use"
        )
        project.calibration_method = method
    
    with col2:
        iterations = st.number_input(
            "Number of Iterations",
            min_value=10,
            max_value=10000,
            value=100,
            help="Total number of simulations to run"
        )
        project.n_iterations = iterations
    
    workers = st.slider(
        "Parallel Workers",
        min_value=1,
        max_value=16,
        value=4,
        help="Number of parallel SWAT simulations"
    )
    project.n_workers = workers
    
    if st.button("Save Settings"):
        project.save()
        st.success("Settings saved")
