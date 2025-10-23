"""
SWAT model execution engine
"""

import subprocess
import logging
import platform
import shutil
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
        timeout: int = 300,
        use_docker: Optional[bool] = None
    ):
        """
        Initialize SWATRunner
        
        Args:
            swat_executable: Path to SWAT/SWAT+ executable
            file_manager: FileManager instance
            timeout: Maximum execution time in seconds
            use_docker: Force Docker usage (None=auto-detect, True=force, False=never)
        """
        self.swat_executable = Path(swat_executable)
        self.file_manager = file_manager
        self.timeout = timeout
        
        if not self.swat_executable.exists():
            raise FileNotFoundError(f"SWAT executable not found: {self.swat_executable}")
        
        if not self.swat_executable.is_file():
            raise ValueError(f"SWAT executable is not a file: {self.swat_executable}")
        
        # Auto-detect if Docker is needed
        if use_docker is None:
            self.use_docker = self._should_use_docker()
        else:
            self.use_docker = use_docker
        
        if self.use_docker:
            logger.info(f"Docker mode enabled for cross-platform execution")
            self._ensure_docker_image()
        
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
    
    def _should_use_docker(self) -> bool:
        """
        Determine if Docker should be used based on platform and executable type
        
        Returns:
            True if Docker should be used, False otherwise
        """
        # Check if on macOS or Linux
        current_platform = platform.system()
        
        # If Windows .exe on non-Windows, need Docker
        if self.swat_executable.suffix == '.exe' and current_platform != 'Windows':
            logger.info("Windows executable detected on non-Windows system - Docker required")
            return True
        
        # If Linux executable on macOS, need Docker
        if current_platform == 'Darwin' and self.swat_executable.suffix != '.exe':
            try:
                # Try to execute to see if it's compatible
                result = subprocess.run(
                    [str(self.swat_executable)],
                    capture_output=True,
                    timeout=1
                )
                return False  # Works natively
            except (OSError, subprocess.TimeoutExpired):
                logger.info("Executable not compatible with macOS - Docker required")
                return True
        
        return False
    
    def _ensure_docker_image(self) -> None:
        """Build Docker image if needed"""
        try:
            # Check if Docker is available
            result = subprocess.run(['docker', '--version'], capture_output=True)
            if result.returncode != 0:
                raise SWATExecutionError(
                    "Docker is required but not installed. "
                    "Install from: https://www.docker.com/products/docker-desktop/"
                )
            
            # Check if image exists
            result = subprocess.run(
                ['docker', 'images', '-q', 'swat-runner'],
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                logger.info("Building Docker image for SWAT...")
                dockerfile = Path(__file__).parent.parent.parent / "Dockerfile.swat"
                
                if not dockerfile.exists():
                    raise SWATExecutionError(f"Dockerfile not found: {dockerfile}")
                
                build_result = subprocess.run(
                    ['docker', 'build', '-f', str(dockerfile), '-t', 'swat-runner', '.'],
                    cwd=dockerfile.parent,
                    capture_output=True
                )
                
                if build_result.returncode != 0:
                    raise SWATExecutionError("Failed to build Docker image")
                
                logger.info("Docker image built successfully")
                
        except FileNotFoundError:
            raise SWATExecutionError(
                "Docker not found. Install from: https://www.docker.com/products/docker-desktop/"
            )
    
    def _execute_swat(self, run_dir: Path, capture_output: bool = True) -> Dict[str, Any]:
        """
        Execute SWAT executable (with Docker if needed)
        
        Args:
            run_dir: Directory to run SWAT in
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Dictionary with execution results
        """
        if self.use_docker:
            return self._execute_swat_docker(run_dir, capture_output)
        else:
            return self._execute_swat_native(run_dir, capture_output)
    
    def _execute_swat_native(self, run_dir: Path, capture_output: bool = True) -> Dict[str, Any]:
        """Execute SWAT natively (original implementation)"""
        try:
            cmd = [str(self.swat_executable)]
            logger.debug(f"Executing (native): {' '.join(cmd)} in {run_dir}")
            
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
    
    def _execute_swat_docker(self, run_dir: Path, capture_output: bool = True) -> Dict[str, Any]:
        """Execute SWAT in Docker container"""
        try:
            # Copy executable to run directory
            swat_in_run = run_dir / "swat_executable"
            shutil.copy2(self.swat_executable, swat_in_run)
            
            # Run in Docker
            logger.debug(f"Executing (Docker): SWAT in {run_dir}")
            
            result = subprocess.run(
                ['docker', 'run', '--rm', '-v', f'{run_dir.absolute()}:/swat', 'swat-runner'],
                capture_output=capture_output,
                text=True if capture_output else False,
                timeout=self.timeout
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Docker SWAT execution timed out after {self.timeout}s")
            raise
            
        except Exception as e:
            logger.error(f"Error executing SWAT in Docker: {e}")
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
