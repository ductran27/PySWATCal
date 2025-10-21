"""
Project setup page for PySWATCal web interface
"""

import streamlit as st
from pathlib import Path
from pyswatcal import Project
from pyswatcal.utils.file_parsers import parse_file_cio, validate_txtinout_directory


def show():
    """Display project setup page"""
    
    st.title("Project Setup")
    st.markdown("Configure your SWAT calibration project")
    
    # Project creation or loading
    tab1, tab2 = st.tabs(["Create New Project", "Load Existing Project"])
    
    with tab1:
        show_create_project()
    
    with tab2:
        show_load_project()


def show_create_project():
    """Show create project interface"""
    
    st.subheader("Create New Project")
    
    # Project name
    project_name = st.text_input(
        "Project Name",
        value="My_SWAT_Calibration",
        help="Enter a name for your calibration project"
    )
    
    # Project description
    description = st.text_area(
        "Description (optional)",
        help="Brief description of the calibration project"
    )
    
    # Model type
    model_type = st.radio(
        "Model Type",
        ["SWAT", "SWAT+"],
        help="Select your SWAT model version"
    )
    
    # Working directory
    working_dir = st.text_input(
        "Working Directory",
        value=str(Path.cwd() / "calibration_work"),
        help="Directory where calibration files will be stored"
    )
    
    # TxtInOut directory
    txtinout_dir = st.text_input(
        "TxtInOut Directory",
        help="Path to your SWAT TxtInOut directory containing model files"
    )
    
    # Validate TxtInOut if provided
    if txtinout_dir:
        txtinout_path = Path(txtinout_dir)
        is_valid, message = validate_txtinout_directory(txtinout_path)
        
        if is_valid:
            st.success(message)
            
            # Show simulation info if valid
            try:
                config = parse_file_cio(txtinout_path / "file.cio")
                st.info(f"Simulation period: {config.get('start_date', 'N/A')} to {config.get('end_date', 'N/A')}")
                st.info(f"Number of years: {config.get('n_years', 'N/A')}")
            except Exception as e:
                st.warning(f"Could not read file.cio: {e}")
        else:
            st.error(message)
    
    # SWAT executable
    swat_exe = st.text_input(
        "SWAT Executable (optional)",
        help="Path to SWAT executable file (can be set later)"
    )
    
    # Create button
    if st.button("Create Project", type="primary"):
        if not project_name:
            st.error("Please enter a project name")
        elif not txtinout_dir:
            st.error("Please specify TxtInOut directory")
        else:
            try:
                # Create project
                project = Project.create(
                    name=project_name,
                    working_dir=Path(working_dir),
                    txtinout_dir=Path(txtinout_dir),
                    model_type=model_type,
                    description=description
                )
                
                if swat_exe:
                    project.swat_executable = Path(swat_exe)
                
                # Save to session state
                st.session_state.project = project
                
                # Save to disk
                project.save()
                
                st.success(f"Project '{project_name}' created successfully!")
                st.info(f"Project saved to: {project.working_dir / (project.name + '.json')}")
                
            except Exception as e:
                st.error(f"Error creating project: {e}")


def show_load_project():
    """Show load project interface"""
    
    st.subheader("Load Existing Project")
    
    project_file = st.text_input(
        "Project File",
        help="Path to project JSON file"
    )
    
    if st.button("Load Project"):
        if not project_file:
            st.error("Please specify a project file")
        else:
            try:
                project = Project.load(Path(project_file))
                st.session_state.project = project
                
                st.success(f"Project '{project.name}' loaded successfully!")
                
                # Display project info
                st.subheader("Project Information")
                st.write(f"**Name**: {project.name}")
                st.write(f"**Model Type**: {project.model_type}")
                st.write(f"**Parameters**: {len(project.parameters)}")
                st.write(f"**Status**: {project.status}")
                st.write(f"**Created**: {project.created}")
                
            except Exception as e:
                st.error(f"Error loading project: {e}")
    
    # Show current project if loaded
    if st.session_state.project is not None:
        st.markdown("---")
        st.subheader("Current Project")
        
        project = st.session_state.project
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Name**: {project.name}")
            st.write(f"**Model**: {project.model_type}")
            st.write(f"**Status**: {project.status}")
        with col2:
            st.write(f"**Parameters**: {len(project.parameters)}")
            st.write(f"**Method**: {project.calibration_method}")
            st.write(f"**Iterations**: {project.n_iterations}")
        
        if st.button("Clear Project"):
            st.session_state.project = None
            st.rerun()
