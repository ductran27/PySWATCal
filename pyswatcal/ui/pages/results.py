"""
Results visualization page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np


def show():
    """Display results page"""
    
    st.title("Calibration Results")
    
    if st.session_state.calibration_results is None:
        st.info("No calibration results available yet. Run a calibration first.")
        return
    
    results = st.session_state.calibration_results
    project = st.session_state.project
    
    st.markdown(f"**Project**: {project.name if project else 'Unknown'}")
    st.markdown("---")
    
    # Summary metrics
    st.subheader("Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Best Objective Value", f"{results['best_value']:.4f}")
    with col2:
        st.metric("Total Evaluations", results['n_evaluations'])
    with col3:
        st.metric("Duration", f"{results.get('duration', 0):.1f}s")
    with col4:
        status = "Success" if results.get('success', False) else "Failed"
        st.metric("Status", status)
    
    # Best parameters
    st.markdown("---")
    st.subheader("Best Parameters")
    
    if project and project.parameters:
        param_data = []
        for param, value in zip(project.parameters, results['best_params']):
            param_data.append({
                "Parameter": param.name,
                "Best Value": value,
                "Min Bound": param.min_value,
                "Max Bound": param.max_value,
                "File Type": param.file_type
            })
        
        df = pd.DataFrame(param_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.write("Best parameters:", results['best_params'])
    
    # Convergence plot
    if 'history' in results:
        st.markdown("---")
        st.subheader("Convergence Plot")
        
        history = results['history']
        
        fig = go.Figure()
        
        # Add trace for all evaluations
        fig.add_trace(go.Scatter(
            x=history['iteration'],
            y=history['objective_value'],
            mode='markers',
            name='All Evaluations',
            marker=dict(size=4, color='lightblue', opacity=0.5)
        ))
        
        # Add trace for best values
        fig.add_trace(go.Scatter(
            x=history['iteration'],
            y=history['best_value'],
            mode='lines+markers',
            name='Best Value',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title="Optimization Convergence",
            xaxis_title="Iteration",
            yaxis_title="Objective Function Value",
            hovermode='closest',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Parameter evolution
        st.markdown("---")
        st.subheader("Parameter Evolution")
        
        if project and project.parameters:
            params_array = np.array(history['parameters'])
            
            fig_params = go.Figure()
            
            for i, param in enumerate(project.parameters):
                fig_params.add_trace(go.Scatter(
                    x=history['iteration'],
                    y=params_array[:, i],
                    mode='lines',
                    name=param.name
                ))
            
            fig_params.update_layout(
                title="Parameter Values Over Iterations",
                xaxis_title="Iteration",
                yaxis_title="Parameter Value",
                hovermode='closest'
            )
            
            st.plotly_chart(fig_params, use_container_width=True)
    
    # Export options
    st.markdown("---")
    st.subheader("Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download Results (JSON)"):
            import json
            results_json = json.dumps(results, indent=2, default=str)
            st.download_button(
                "Click to Download",
                results_json,
                file_name="calibration_results.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("Download Best Parameters (CSV)"):
            if project and project.parameters:
                csv_data = "Parameter,Value\n"
                for param, value in zip(project.parameters, results['best_params']):
                    csv_data += f"{param.name},{value}\n"
                
                st.download_button(
                    "Click to Download",
                    csv_data,
                    file_name="best_parameters.csv",
                    mime="text/csv"
                )
