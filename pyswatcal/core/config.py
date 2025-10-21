"""
Configuration management for PySWATCal
"""

from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator, ConfigDict
import yaml
import json


class Config(BaseModel):
    """
    Global configuration for PySWATCal
    
    Attributes:
        working_dir: Working directory for project files
        max_workers: Maximum number of parallel workers
        cache_dir: Directory for caching results
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        swat_timeout: Timeout for SWAT simulations in seconds
    """
    
    working_dir: Path = Field(default=Path.cwd())
    max_workers: int = Field(default=-1, ge=-1)  # -1 means auto-detect
    cache_dir: Optional[Path] = None
    log_level: str = Field(default="INFO")
    swat_timeout: int = Field(default=300, gt=0)  # 5 minutes default
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @validator("working_dir", "cache_dir", pre=True)
    def validate_path(cls, v: Any) -> Optional[Path]:
        """Convert string to Path and validate"""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v)
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @validator("max_workers")
    def validate_max_workers(cls, v: int) -> int:
        """Validate max_workers"""
        import os
        if v == -1:
            # Auto-detect: use number of CPU cores
            return os.cpu_count() or 1
        return v
    
    def model_post_init(self, __context: Any) -> None:
        """Initialize after model creation"""
        # Create directories if they don't exist
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        if self.cache_dir is None:
            self.cache_dir = self.working_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_yaml(cls, file_path: Path) -> "Config":
        """
        Load configuration from YAML file
        
        Args:
            file_path: Path to YAML configuration file
            
        Returns:
            Config instance
        """
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    @classmethod
    def from_json(cls, file_path: Path) -> "Config":
        """
        Load configuration from JSON file
        
        Args:
            file_path: Path to JSON configuration file
            
        Returns:
            Config instance
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    def to_yaml(self, file_path: Path) -> None:
        """
        Save configuration to YAML file
        
        Args:
            file_path: Path to save YAML file
        """
        data = self.model_dump(mode='json')
        # Convert Path objects to strings for YAML serialization
        data = {k: str(v) if isinstance(v, Path) else v for k, v in data.items()}
        
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
    
    def to_json(self, file_path: Path) -> None:
        """
        Save configuration to JSON file
        
        Args:
            file_path: Path to save JSON file
        """
        data = self.model_dump(mode='json')
        # Convert Path objects to strings for JSON serialization
        data = {k: str(v) if isinstance(v, Path) else v for k, v in data.items()}
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary
        
        Returns:
            Dictionary representation
        """
        return self.model_dump(mode='json')


# Default global configuration instance
_default_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance
    
    Returns:
        Global Config instance
    """
    global _default_config
    if _default_config is None:
        _default_config = Config()
    return _default_config


def set_config(config: Config) -> None:
    """
    Set the global configuration instance
    
    Args:
        config: Config instance to set as global
    """
    global _default_config
    _default_config = config


def reset_config() -> None:
    """Reset configuration to default"""
    global _default_config
    _default_config = Config()
