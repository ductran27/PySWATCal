"""
SWAT file parsers for configuration and parameter files
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def parse_file_cio(file_path: Path) -> Dict[str, Any]:
    """
    Parse SWAT file.cio to extract simulation configuration
    
    Args:
        file_path: Path to file.cio
        
    Returns:
        Dictionary containing simulation parameters
        
    Example:
        >>> config = parse_file_cio(Path("TxtInOut/file.cio"))
        >>> print(config['n_years'])
        13
        >>> print(config['start_date'])
        2000-01-01
    """
    if not file_path.exists():
        raise FileNotFoundError(f"file.cio not found: {file_path}")
    
    config = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Parse key parameters from file.cio
        for line in lines:
            parts = line.split('|')
            if len(parts) >= 2:
                value_part = parts[0].strip()
                comment_part = parts[1].strip()
                
                try:
                    # Extract number of years
                    if 'NBYR' in comment_part:
                        config['n_years'] = int(value_part)
                    
                    # Extract beginning year
                    elif 'IYR' in comment_part:
                        config['start_year'] = int(value_part)
                    
                    # Extract beginning julian day
                    elif 'IDAF' in comment_part:
                        config['start_day'] = int(value_part)
                    
                    # Extract ending julian day
                    elif 'IDAL' in comment_part:
                        config['end_day'] = int(value_part)
                    
                    # Extract years to skip
                    elif 'NYSKIP' in comment_part:
                        config['skip_years'] = int(value_part)
                    
                    # Extract print code
                    elif 'IPRINT' in comment_part:
                        config['print_code'] = int(value_part)
                    
                except (ValueError, IndexError):
                    pass
        
        # Calculate actual simulation dates
        if 'start_year' in config and 'start_day' in config:
            start_date = datetime(config['start_year'], 1, 1) + timedelta(days=config['start_day'] - 1)
            config['start_date'] = start_date.strftime('%Y-%m-%d')
        
        if 'start_year' in config and 'n_years' in config and 'end_day' in config:
            end_year = config['start_year'] + config['n_years'] - 1
            end_date = datetime(end_year, 1, 1) + timedelta(days=config['end_day'] - 1)
            config['end_date'] = end_date.strftime('%Y-%m-%d')
        
        # Calculate evaluation period (after warmup)
        if 'skip_years' in config and 'start_year' in config and 'start_day' in config:
            eval_year = config['start_year'] + config['skip_years']
            eval_date = datetime(eval_year, 1, 1) + timedelta(days=config['start_day'] - 1)
            config['eval_start_date'] = eval_date.strftime('%Y-%m-%d')
        
        logger.info(f"Parsed file.cio: {config.get('n_years', 'N/A')} years simulation")
        return config
        
    except Exception as e:
        logger.error(f"Error parsing file.cio: {e}")
        raise


def parse_parameter_file(file_path: Path, model_type: str = "SWAT") -> pd.DataFrame:
    """
    Parse SWAT parameter file (swatParam.txt or cal_parms.cal)
    
    Args:
        file_path: Path to parameter file
        model_type: "SWAT" or "SWAT+"
        
    Returns:
        DataFrame with parameter information
        
    Example:
        >>> params = parse_parameter_file(Path("swatParam.txt"))
        >>> print(params.columns)
        ['parameter', 'file_type', 'min', 'max', 'description']
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Parameter file not found: {file_path}")
    
    try:
        if model_type == "SWAT":
            # Parse swatParam.txt format
            # Format: NAME    FILE    MIN    MAX    DESCRIPTION
            df = pd.read_csv(
                file_path,
                sep=r'\s+',
                comment='#',
                names=['parameter', 'file_type', 'min_value', 'max_value', 'description'],
                skipinitialspace=True
            )
        else:  # SWAT+
            # Parse cal_parms.cal format
            # Different format for SWAT+
            df = pd.read_csv(
                file_path,
                sep=r'\s+',
                comment='#',
                skipinitialspace=True
            )
        
        logger.info(f"Parsed {len(df)} parameters from {file_path.name}")
        return df
        
    except Exception as e:
        logger.error(f"Error parsing parameter file: {e}")
        raise


def extract_basin_info(txtinout_dir: Path) -> Dict[str, Any]:
    """
    Extract basin information from SWAT project
    
    Args:
        txtinout_dir: Path to TxtInOut directory
        
    Returns:
        Dictionary with basin information
    """
    basin_info = {
        'n_subbasins': 0,
        'n_hrus': 0,
        'n_reaches': 0,
    }
    
    try:
        # Count .sub files
        sub_files = list(txtinout_dir.glob("*.sub"))
        basin_info['n_subbasins'] = len(sub_files)
        
        # Count .hru files
        hru_files = list(txtinout_dir.glob("*.hru"))
        basin_info['n_hrus'] = len(hru_files)
        
        # Count .rte files
        rte_files = list(txtinout_dir.glob("*.rte"))
        basin_info['n_reaches'] = len(rte_files)
        
        logger.info(
            f"Basin info: {basin_info['n_subbasins']} subbasins, "
            f"{basin_info['n_hrus']} HRUs, {basin_info['n_reaches']} reaches"
        )
        
    except Exception as e:
        logger.warning(f"Error extracting basin info: {e}")
    
    return basin_info


def validate_txtinout_directory(txtinout_dir: Path) -> Tuple[bool, str]:
    """
    Validate that TxtInOut directory contains required SWAT files
    
    Args:
        txtinout_dir: Path to TxtInOut directory
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not txtinout_dir.exists():
        return False, f"Directory does not exist: {txtinout_dir}"
    
    if not txtinout_dir.is_dir():
        return False, f"Not a directory: {txtinout_dir}"
    
    # Check for file.cio
    if not (txtinout_dir / "file.cio").exists():
        return False, "file.cio not found - not a valid SWAT TxtInOut directory"
    
    # Check for basin file
    if not (txtinout_dir / "basins.bsn").exists():
        return False, "basins.bsn not found"
    
    # Check for at least one .hru file
    hru_files = list(txtinout_dir.glob("*.hru"))
    if not hru_files:
        return False, "No .hru files found"
    
    return True, "Valid SWAT TxtInOut directory"


def read_swat_date_format(date_str: str, time_str: str = "00:00") -> datetime:
    """
    Parse SWAT date format
    
    Args:
        date_str: Date string (YYYY-MM-DD or YYYYMMDD or julian)
        time_str: Time string (HH:MM)
        
    Returns:
        datetime object
    """
    try:
        # Try YYYY-MM-DD format
        if '-' in date_str:
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        # Try YYYYMMDD format
        elif len(date_str) == 8:
            return datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H:%M")
        # Try year and julian day
        else:
            year, jday = date_str.split()
            base = datetime(int(year), 1, 1)
            return base + timedelta(days=int(jday) - 1)
    except Exception as e:
        logger.warning(f"Error parsing date '{date_str}': {e}")
        return None
