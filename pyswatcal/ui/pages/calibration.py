"""
Calibration execution page
"""

import streamlit as st
import numpy as np
from pathlib import Path
from pyswatcal.core import FileManager, SWATRunner
from pyswatcal.calibration import nse, kge, DDS
from pyswatcal.calibration.sampling import ParameterSampler
from pyswatcal.utils import parse_swat_output, extract_timeseries


def show():
    """Display calibration page"""
    
    st.title("Run Calibration")
    
    if st.session_state.project is None:
        st.warning("Please create or load a project first")
        return
    
    project = st.session_state.project
    
    if len(project.parameters) == 0:
        st.warning("Please add parameters to calibrate")
        return
    
    st.markdown(f"**Project**: {project.name}")
    st.markdown(f"**Method**: {project.calibration_method}")
    st.markdown(f"**Parameters**: {len(project.parameters)}")
    st.markdown("---")
    
    # Configuration
    st.subheader("Calibration Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Observed data upload
        observed_file = st.file_uploader(
            "Upload Observed Data",
            type=['txt', 'csv'],
            help="File with observed streamflow or other variable"
        )
        
        # Objective function
        objective_func = st.selectbox(
            "Objective Function",
            ["NSE", "KGE", "RMSE", "PBIAS"],
            help="Performance metric to optimize"
        )
    
    with col2:
        # Output variable
        output_var = st.text_input(
            "Output Variable",
            value="FLOW_OUTcms",
            help="Variable name in SWAT output"
        )
        
        # Reach/entity ID
        entity_id = st.number_input(
            "Reach/Subbasin ID",
            min_value=1,
            value=1,
            help="Reach or subbasin number to extract"
        )
    
    # SWAT executable
    if project.swat_executable is None:
        swat_exe = st.text_input(
            "SWAT Executable",
            help="Path to SWAT executable file"
        )
    else:
        swat_exe = str(project.swat_executable)
        st.info(f"Using executable: {swat_exe}")
    
    # Run button
    if st.button("Start Calibration", type="primary"):
        if observed_file is None:
            st.error("Please upload observed data file")
        elif not swat_exe or not Path(swat_exe).exists():
            st.error("Please specify valid SWAT executable")
        else:
            run_calibration(
                project,
                observed_file,
                objective_func,
                output_var,
                entity_id,
                swat_exe
            )


def run_calibration(project, observed_file, obj_func, output_var, entity_id, swat_exe):
    """Execute calibration workflow"""
    
    try:
        # Read observed data
        observed = np.loadtxt(observed_file)
        st.info(f"Loaded {len(observed)} observed values")
        
        # Setup
        fm = FileManager(project.txtinout_dir, project.working_dir)
        runner = SWATRunner(Path(swat_exe), fm)
        
        # Get parameter bounds
        bounds = [(p.min_value, p.max_value) for p in project.parameters]
        param_names = [p.name for p in project.parameters]
        
        # Define objective function
        def calibration_objective(params):
            # Create parameter dictionary
            param_dict = dict(zip(param_names, params))
            
            # Run SWAT
            result = runner.run_simulation(
                run_id=np.random.randint(1000000),
                parameters=param_dict
            )
            
            if not result["success"]:
                return -999 if obj_func in ["NSE", "KGE"] else 999
            
            # Read output
            df = parse_swat_output(result["run_dir"], "reach", "SWAT")
            simulated = extract_timeseries(df, output_var, entity_id, 'REACH')
            
            # Trim to match observed length
            simulated = simulated[:len(observed)]
            
            # Calculate objective
            if obj_func == "NSE":
                return nse(observed, simulated)
            elif obj_func == "KGE":
                return kge(observed, simulated)
            else:
                from pyswatcal.calibration import rmse, pbias
                if obj_func == "RMSE":
                    return -rmse(observed, simulated)
                else:
                    return -abs(pbias(observed, simulated))
        
        # Run calibration with progress
        with st.spinner(f"Running {project.calibration_method} calibration..."):
            if project.calibration_method == "DDS":
                dds = DDS(
                    bounds=bounds,
                    objective_function=calibration_objective,
                    n_iterations=project.n_iterations,
                    r=0.2,
                    maximize=obj_func in ["NSE", "KGE"]
                )
                results = dds.optimize()
            else:
                st.error(f"{project.calibration_method} not yet implemented in UI")
                return
        
        # Store results
        st.session_state.calibration_results = results
        project.results = results
        project.save()
        
        # Display results
        st.success("Calibration completed!")
        st.subheader("Results")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(f"Best {obj_func}", f"{results['best_value']:.4f}")
            st.metric("Iterations", results['n_evaluations'])
        with col2:
            st.metric("Duration", f"{results['duration']:.1f}s")
            st.metric("Success", "Yes" if results['success'] else "No")
        
        # Display best parameters
        st.subheader("Best Parameters")
        for name, value in zip(param_names, results['best_params']):
            st.write(f"**{name}**: {value:.6f}")
        
    except Exception as e:
        st.error(f"Calibration error: {e}")
        import traceback
        st.code(traceback.format_exc())
