"""
Project management for PySWATCal
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConfigDict
import json
import yaml
from enum import Enum


class ModelType(str, Enum):
    """Supported SWAT model types"""
    SWAT = "SWAT"
    SWAT_PLUS = "SWAT+"


class ProjectStatus(str, Enum):
    """Project status"""
    CREATED = "created"
    CONFIGURED = "configured"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Parameter(BaseModel):
    """
    SWAT parameter definition
    
    Attributes:
        name: Parameter name
        file_type: File type containing the parameter (.hru, .rch, .sub, etc.)
        min_value: Minimum value for calibration
        max_value: Maximum value for calibration
        change_type: Type of change (absolute, relative, replace)
        description: Parameter description
    """
    name: str
    file_type: str
    min_value: float
    max_value: float
    change_type: str = Field(default="relative")
    description: str = ""
    
    @validator("change_type")
    def validate_change_type(cls, v: str) -> str:
        """Validate change type"""
        valid_types = ["absolute", "relative", "replace"]
        if v not in valid_types:
            raise ValueError(f"change_type must be one of {valid_types}")
        return v
    
    @validator("min_value", "max_value")
    def validate_bounds(cls, v: float) -> float:
        """Validate parameter bounds"""
        if not isinstance(v, (int, float)):
            raise ValueError("Parameter bounds must be numeric")
        return float(v)


class Project(BaseModel):
    """
    PySWATCal project
    
    A project contains all information needed for SWAT calibration:
    - Model configuration
    - Parameters to calibrate
    - Calibration settings
    - Results
    """
    
    # Basic info
    name: str
    description: str = ""
    created: datetime = Field(default_factory=datetime.now)
    modified: datetime = Field(default_factory=datetime.now)
    version: str = "0.1.0"
    
    # Model configuration
    model_type: ModelType = ModelType.SWAT
    working_dir: Path
    txtinout_dir: Path
    swat_executable: Optional[Path] = None
    
    # Calibration configuration
    parameters: List[Parameter] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    warmup_years: int = Field(default=0, ge=0)
    
    # Calibration method
    calibration_method: str = "DDS"
    n_iterations: int = Field(default=100, gt=0)
    n_workers: int = Field(default=4, gt=0)
    
    # Output configuration
    output_variables: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Status
    status: ProjectStatus = ProjectStatus.CREATED
    
    # Results (populated after calibration)
    results: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
        protected_namespaces=()
    )
    
    @validator("working_dir", "txtinout_dir", "swat_executable", pre=True)
    def validate_path(cls, v: Any) -> Optional[Path]:
        """Convert string to Path"""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v)
        return v
    
    @validator("txtinout_dir")
    def validate_txtinout_dir(cls, v: Path) -> Path:
        """Validate TxtInOut directory exists"""
        if not v.exists():
            raise ValueError(f"TxtInOut directory does not exist: {v}")
        return v
    
    def model_post_init(self, __context: Any) -> None:
        """Initialize after model creation"""
        # Create working directory if it doesn't exist
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output directory
        output_dir = self.working_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Update modified timestamp
        self.modified = datetime.now()
    
    @classmethod
    def create(
        cls,
        name: str,
        working_dir: Path,
        txtinout_dir: Path,
        model_type: ModelType = ModelType.SWAT,
        **kwargs
    ) -> "Project":
        """
        Create a new project
        
        Args:
            name: Project name
            working_dir: Working directory path
            txtinout_dir: TxtInOut directory path
            model_type: SWAT or SWAT+
            **kwargs: Additional project parameters
            
        Returns:
            New Project instance
        """
        return cls(
            name=name,
            working_dir=Path(working_dir),
            txtinout_dir=Path(txtinout_dir),
            model_type=model_type,
            **kwargs
        )
    
    def add_parameter(
        self,
        name: str,
        file_type: str,
        min_value: float,
        max_value: float,
        change_type: str = "relative",
        description: str = ""
    ) -> None:
        """
        Add a parameter to calibrate
        
        Args:
            name: Parameter name
            file_type: File type (.hru, .rch, etc.)
            min_value: Minimum value
            max_value: Maximum value
            change_type: Type of change
            description: Parameter description
        """
        param = Parameter(
            name=name,
            file_type=file_type,
            min_value=min_value,
            max_value=max_value,
            change_type=change_type,
            description=description
        )
        self.parameters.append(param)
        self.modified = datetime.now()
    
    def remove_parameter(self, name: str) -> bool:
        """
        Remove a parameter
        
        Args:
            name: Parameter name to remove
            
        Returns:
            True if parameter was removed, False if not found
        """
        for i, param in enumerate(self.parameters):
            if param.name == name:
                self.parameters.pop(i)
                self.modified = datetime.now()
                return True
        return False
    
    def get_parameter(self, name: str) -> Optional[Parameter]:
        """
        Get a parameter by name
        
        Args:
            name: Parameter name
            
        Returns:
            Parameter if found, None otherwise
        """
        for param in self.parameters:
            if param.name == name:
                return param
        return None
    
    def save(self, file_path: Optional[Path] = None) -> Path:
        """
        Save project to JSON file
        
        Args:
            file_path: Path to save file (default: working_dir/project_name.json)
            
        Returns:
            Path to saved file
        """
        if file_path is None:
            file_path = self.working_dir / f"{self.name}.json"
        
        # Update modified timestamp
        self.modified = datetime.now()
        
        # Convert to dictionary
        data = self.model_dump(mode='json')
        
        # Convert Path objects to strings
        data = self._convert_paths_to_str(data)
        
        # Save to file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return file_path
    
    @classmethod
    def load(cls, file_path: Path) -> "Project":
        """
        Load project from JSON file
        
        Args:
            file_path: Path to project file
            
        Returns:
            Project instance
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return cls(**data)
    
    def export_yaml(self, file_path: Optional[Path] = None) -> Path:
        """
        Export project to YAML file
        
        Args:
            file_path: Path to save file
            
        Returns:
            Path to saved file
        """
        if file_path is None:
            file_path = self.working_dir / f"{self.name}.yaml"
        
        data = self.model_dump(mode='json')
        data = self._convert_paths_to_str(data)
        
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        return file_path
    
    def _convert_paths_to_str(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Path objects to strings recursively"""
        result = {}
        for key, value in data.items():
            if isinstance(value, Path):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = self._convert_paths_to_str(value)
            elif isinstance(value, list):
                result[key] = [
                    str(v) if isinstance(v, Path) else v
                    for v in value
                ]
            else:
                result[key] = value
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get project summary
        
        Returns:
            Dictionary with project summary
        """
        return {
            "name": self.name,
            "model_type": self.model_type,
            "status": self.status,
            "n_parameters": len(self.parameters),
            "calibration_method": self.calibration_method,
            "n_iterations": self.n_iterations,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
        }
    
    def __str__(self) -> str:
        """String representation"""
        return (
            f"Project: {self.name}\n"
            f"Type: {self.model_type}\n"
            f"Status: {self.status}\n"
            f"Parameters: {len(self.parameters)}\n"
            f"Method: {self.calibration_method}\n"
            f"Iterations: {self.n_iterations}"
        )
