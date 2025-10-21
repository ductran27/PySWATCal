"""
File management for SWAT model files
"""

import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """
    Manages SWAT file operations including copying, reading, and writing
    
    Handles file operations for both SWAT and SWAT+ models.
    """
    
    def __init__(self, txtinout_dir: Path, working_dir: Path):
        """
        Initialize FileManager
        
        Args:
            txtinout_dir: Path to TxtInOut directory (source files)
            working_dir: Path to working directory (for temporary files)
        """
        self.txtinout_dir = Path(txtinout_dir)
        self.working_dir = Path(working_dir)
        
        if not self.txtinout_dir.exists():
            raise ValueError(f"TxtInOut directory does not exist: {self.txtinout_dir}")
        
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect model type
        self.model_type = self._detect_model_type()
        logger.info(f"Detected model type: {self.model_type}")
    
    def _detect_model_type(self) -> str:
        """
        Detect if this is SWAT or SWAT+ project
        
        Returns:
            "SWAT" or "SWAT+"
        """
        # Check for SWAT+ specific files
        swat_plus_files = ["time.sim", "print.prt", "codes.bsn"]
        
        for file in swat_plus_files:
            if (self.txtinout_dir / file).exists():
                return "SWAT+"
        
        # Check for SWAT specific files
        if (self.txtinout_dir / "file.cio").exists():
            return "SWAT"
        
        raise ValueError("Unable to determine model type from TxtInOut directory")
    
    def create_run_directory(self, run_id: int) -> Path:
        """
        Create a directory for a simulation run
        
        Args:
            run_id: Unique identifier for this run
            
        Returns:
            Path to created directory
        """
        run_dir = self.working_dir / f"run_{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir
    
    def copy_txtinout(self, destination: Path, exclude_files: Optional[List[str]] = None) -> None:
        """
        Copy TxtInOut directory to destination
        
        Args:
            destination: Destination directory
            exclude_files: List of filenames to exclude from copying
        """
        if exclude_files is None:
            exclude_files = []
        
        destination.mkdir(parents=True, exist_ok=True)
        
        # Copy all files
        for item in self.txtinout_dir.iterdir():
            if item.name not in exclude_files:
                if item.is_file():
                    shutil.copy2(item, destination / item.name)
                elif item.is_dir():
                    shutil.copytree(item, destination / item.name, dirs_exist_ok=True)
        
        logger.debug(f"Copied TxtInOut to {destination}")
    
    def read_file(self, filename: str, directory: Optional[Path] = None) -> List[str]:
        """
        Read a file and return lines
        
        Args:
            filename: Name of file to read
            directory: Directory containing file (default: txtinout_dir)
            
        Returns:
            List of lines from file
        """
        if directory is None:
            directory = self.txtinout_dir
        
        file_path = directory / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            return lines
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    def write_file(self, filename: str, lines: List[str], directory: Optional[Path] = None) -> None:
        """
        Write lines to a file
        
        Args:
            filename: Name of file to write
            lines: List of lines to write
            directory: Directory to write to (default: working_dir)
        """
        if directory is None:
            directory = self.working_dir
        
        file_path = directory / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            logger.debug(f"Wrote file: {file_path}")
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            raise
    
    def update_parameter_in_file(
        self,
        filename: str,
        parameter_name: str,
        new_value: float,
        change_type: str = "replace",
        directory: Optional[Path] = None
    ) -> None:
        """
        Update a parameter value in a SWAT file
        
        Args:
            filename: Name of file to modify
            parameter_name: Name of parameter to change
            new_value: New parameter value
            change_type: How to apply the change (replace, relative, absolute)
            directory: Directory containing file
        """
        lines = self.read_file(filename, directory)
        modified_lines = []
        
        for line in lines:
            # Check if this line contains the parameter
            if parameter_name in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    try:
                        old_value = float(parts[0].strip())
                        
                        if change_type == "replace":
                            updated_value = new_value
                        elif change_type == "relative":
                            updated_value = old_value * (1 + new_value)
                        elif change_type == "absolute":
                            updated_value = old_value + new_value
                        else:
                            raise ValueError(f"Unknown change_type: {change_type}")
                        
                        # Reconstruct line with new value
                        parts[0] = f"{updated_value:.6f}".rjust(len(parts[0]))
                        modified_line = '|'.join(parts)
                        modified_lines.append(modified_line)
                        logger.debug(f"Updated {parameter_name} from {old_value} to {updated_value}")
                        continue
                    except (ValueError, IndexError):
                        pass
            
            modified_lines.append(line)
        
        self.write_file(filename, modified_lines, directory)
    
    def get_file_list(self, extension: Optional[str] = None) -> List[Path]:
        """
        Get list of files in TxtInOut directory
        
        Args:
            extension: Filter by file extension (e.g., ".hru", ".rch")
            
        Returns:
            List of file paths
        """
        if extension:
            files = list(self.txtinout_dir.glob(f"*{extension}"))
        else:
            files = [f for f in self.txtinout_dir.iterdir() if f.is_file()]
        
        return sorted(files)
    
    def backup_file(self, filename: str, suffix: str = ".bak") -> Path:
        """
        Create a backup of a file
        
        Args:
            filename: Name of file to backup
            suffix: Suffix for backup file
            
        Returns:
            Path to backup file
        """
        source = self.txtinout_dir / filename
        backup = source.with_suffix(source.suffix + suffix)
        
        if source.exists():
            shutil.copy2(source, backup)
            logger.info(f"Created backup: {backup}")
            return backup
        else:
            raise FileNotFoundError(f"Source file not found: {source}")
    
    def clean_run_directories(self, keep_recent: int = 5) -> int:
        """
        Clean up old run directories
        
        Args:
            keep_recent: Number of recent directories to keep
            
        Returns:
            Number of directories removed
        """
        run_dirs = sorted(
            [d for d in self.working_dir.iterdir() if d.is_dir() and d.name.startswith("run_")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        removed = 0
        for dir_to_remove in run_dirs[keep_recent:]:
            try:
                shutil.rmtree(dir_to_remove)
                removed += 1
                logger.info(f"Removed old run directory: {dir_to_remove}")
            except Exception as e:
                logger.warning(f"Failed to remove {dir_to_remove}: {e}")
        
        return removed
    
    def get_output_files(self, run_dir: Path) -> Dict[str, Path]:
        """
        Get paths to SWAT output files
        
        Args:
            run_dir: Directory containing SWAT outputs
            
        Returns:
            Dictionary mapping output type to file path
        """
        output_files = {}
        
        if self.model_type == "SWAT":
            # Common SWAT output files
            output_patterns = {
                "reach": "output.rch",
                "subbasin": "output.sub",
                "hru": "output.hru",
                "water_balance": "output.std",
            }
        else:  # SWAT+
            output_patterns = {
                "channel": "channel_sd_day.txt",
                "basin": "basin_wb_day.txt",
                "aquifer": "aquifer_day.txt",
                "hru": "hru_ls_day.txt",
            }
        
        for key, filename in output_patterns.items():
            file_path = run_dir / filename
            if file_path.exists():
                output_files[key] = file_path
        
        return output_files
    
    def __repr__(self) -> str:
        """String representation"""
        return f"FileManager(model={self.model_type}, txtinout={self.txtinout_dir})"
