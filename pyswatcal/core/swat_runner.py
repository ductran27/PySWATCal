"""
SWAT model execution engine
"""

import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from pyswatcal.core.file_manager import FileManager

logger = logging.getLogger(__name__)


class SWATExecutionError(Exception):
    """Raised when SWAT execution fails"""
    pass


class SWATRunner:
    """
    Executes SWAT/SWAT+ simulations
    
    Handles running SWAT executable with proper setup and error handling.
    """
    
    def __init__(
        self,
        swat_executable: Path,
        file_manager: FileManager,
        timeout: int = 300
    ):
        """
        Initialize SWATRunner
        
        Args:
            swat_executable: Path to SWAT/SWAT+ executable
            file_manager: FileManager instance
            timeout: Maximum execution time in seconds
        """
        self.swat_executable = Path(swat_executable)
        self.file_manager = file_manager
        self.timeout = timeout
        
        if not self.swat_executable.exists():
            raise FileNotFoundError(f"SWAT executable not found: {self.swat_executable}")
        
        if not self.swat_executable.is_file():
            raise ValueError(f"SWAT executable is not a file: {self.swat_executable}")
        
        logger.info(f"Initialized SWATRunner with executable: {self.swat_executable}")
    
    def run_simulation(
        self,
        run_id: int,
        parameters: Optional[Dict[str, float]] = None,
        capture_output: bool = True
    ) -> Dict[str, Any]:
        """
        Run a SWAT simulation
        
        Args:
            run_id: Unique identifier for this simulation run
            parameters: Dictionary of parameter names and values to apply
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Dictionary containing:
                - success: Boolean indicating if simulation completed
                - run_dir: Path to run directory
                - duration: Execution time in seconds
                - stdout: Standard output (if captured)
                - stderr: Standard error (if captured)
                - error: Error message (if failed)
        """
        start_time = time.time()
        
        # Create run directory
        run_dir = self.file_manager.create_run_directory(run_id)
        logger.info(f"Starting simulation run {run_id} in {run_dir}")
        
        try:
            # Copy TxtInOut files to run directory
            self.file_manager.copy_txtinout(run_dir)
            
            # Apply parameter changes if provided
            if parameters:
                self._apply_parameters(parameters, run_dir)
            
            # Execute SWAT
            result = self._execute_swat(run_dir, capture_output)
            
            duration = time.time() - start_time
            
            if result["returncode"] == 0:
                logger.info(f"Run {run_id} completed successfully in {duration:.2f}s")
                return {
                    "success": True,
                    "run_id": run_id,
                    "run_dir": run_dir,
                    "duration": duration,
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                }
            else:
                error_msg = f"SWAT returned non-zero exit code: {result['returncode']}"
                logger.error(f"Run {run_id} failed: {error_msg}")
                return {
                    "success": False,
                    "run_id": run_id,
                    "run_dir": run_dir,
                    "duration": duration,
                    "error": error_msg,
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                }
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            error_msg = f"Simulation timed out after {self.timeout}s"
            logger.error(f"Run {run_id} failed: {error_msg}")
            return {
                "success": False,
                "run_id": run_id,
                "run_dir": run_dir,
                "duration": duration,
                "error": error_msg,
            }
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Run {run_id} failed: {error_msg}", exc_info=True)
            return {
                "success": False,
                "run_id": run_id,
                "run_dir": run_dir,
                "duration": duration,
                "error": error_msg,
            }
    
    def _apply_parameters(self, parameters: Dict[str, float], run_dir: Path) -> None:
        """
        Apply parameter changes to SWAT files
        
        Args:
            parameters: Dictionary of parameter names and values
            run_dir: Directory containing SWAT files to modify
        """
        logger.debug(f"Applying {len(parameters)} parameter changes")
        
        # This is a simplified implementation
        # In practice, you would need to know which file each parameter belongs to
        # and apply the changes accordingly
        
        for param_name, param_value in parameters.items():
            try:
                # Determine which file contains this parameter
                # This would need to be more sophisticated in practice
                file_pattern = self._get_file_pattern_for_parameter(param_name)
                
                if file_pattern:
                    files = list(run_dir.glob(file_pattern))
                    for file_path in files:
                        self._update_parameter_in_file(
                            file_path,
                            param_name,
                            param_value
                        )
                else:
                    logger.warning(f"Unknown file location for parameter: {param_name}")
                    
            except Exception as e:
                logger.error(f"Error applying parameter {param_name}: {e}")
                raise
    
    def _get_file_pattern_for_parameter(self, param_name: str) -> Optional[str]:
        """
        Get file pattern for a given parameter
        
        Args:
            param_name: Parameter name
            
        Returns:
            File pattern (glob) or None
        """
        # Common SWAT parameter locations
        # This is a simplified mapping - in practice would be more comprehensive
        param_file_map = {
            "CN2": "*.mgt",
            "SOL_AWC": "*.sol",
            "SOL_K": "*.sol",
            "SOL_BD": "*.sol",
            "ALPHA_BF": "*.gw",
            "GW_DELAY": "*.gw",
            "GWQMN": "*.gw",
            "GW_REVAP": "*.gw",
            "REVAPMN": "*.gw",
            "RCHRG_DP": "*.gw",
            "ESCO": "*.hru",
            "EPCO": "*.hru",
            "CH_N2": "*.rte",
            "CH_K2": "*.rte",
            "ALPHA_BNK": "*.rte",
            "SURLAG": "*.bsn",
            "SMFMX": "*.bsn",
            "SMFMN": "*.bsn",
            "TIMP": "*.bsn",
        }
        
        return param_file_map.get(param_name)
    
    def _update_parameter_in_file(
        self,
        file_path: Path,
        param_name: str,
        param_value: float
    ) -> None:
        """
        Update parameter in a specific file
        
        Args:
            file_path: Path to file to modify
            param_name: Parameter name
            param_value: New parameter value
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            modified_lines = []
            for line in lines:
                if param_name in line:
                    # Parse and update the line
                    # SWAT files typically have format: value | parameter_name | description
                    parts = line.split('|')
                    if len(parts) >= 2:
                        try:
                            old_value = float(parts[0].strip())
                            # Apply the change (assuming relative change)
                            new_value = old_value * (1 + param_value)
                            parts[0] = f"{new_value:16.3f}"
                            modified_line = '|'.join(parts)
                            modified_lines.append(modified_line)
                            logger.debug(f"Updated {param_name} in {file_path.name}: {old_value} -> {new_value}")
                            continue
                        except (ValueError, IndexError):
                            pass
                
                modified_lines.append(line)
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(modified_lines)
                
        except Exception as e:
            logger.error(f"Error updating {file_path}: {e}")
            raise
    
    def _execute_swat(self, run_dir: Path, capture_output: bool = True) -> Dict[str, Any]:
        """
        Execute SWAT executable
        
        Args:
            run_dir: Directory to run SWAT in
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Prepare command
            cmd = [str(self.swat_executable)]
            
            # Execute SWAT
            logger.debug(f"Executing: {' '.join(cmd)} in {run_dir}")
            
            if capture_output:
                result = subprocess.run(
                    cmd,
                    cwd=run_dir,
                    timeout=self.timeout,
                    capture_output=True,
                    text=True
                )
                return {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            else:
                result = subprocess.run(
                    cmd,
                    cwd=run_dir,
                    timeout=self.timeout
                )
                return {
                    "returncode": result.returncode,
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"SWAT execution timed out after {self.timeout}s")
            raise
            
        except Exception as e:
            logger.error(f"Error executing SWAT: {e}")
            raise
    
    def validate_output(self, run_dir: Path) -> bool:
        """
        Validate that SWAT produced expected output files
        
        Args:
            run_dir: Directory containing SWAT outputs
            
        Returns:
            True if outputs are valid, False otherwise
        """
        output_files = self.file_manager.get_output_files(run_dir)
        
        if not output_files:
            logger.warning(f"No output files found in {run_dir}")
            return False
        
        # Check that output files are not empty
        for output_type, file_path in output_files.items():
            if file_path.stat().st_size == 0:
                logger.warning(f"Output file {output_type} is empty: {file_path}")
                return False
        
        logger.debug(f"Found {len(output_files)} valid output files")
        return True
    
    def get_simulation_summary(self, run_dir: Path) -> Dict[str, Any]:
        """
        Get summary information about a simulation
        
        Args:
            run_dir: Directory containing simulation results
            
        Returns:
            Dictionary with summary information
        """
        output_files = self.file_manager.get_output_files(run_dir)
        
        summary = {
            "run_dir": str(run_dir),
            "output_files": {k: str(v) for k, v in output_files.items()},
            "n_output_files": len(output_files),
            "valid": self.validate_output(run_dir),
        }
        
        return summary
    
    def __repr__(self) -> str:
        """String representation"""
        return f"SWATRunner(executable={self.swat_executable.name}, timeout={self.timeout}s)"
