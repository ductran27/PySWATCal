"""
SWAT output file parsers

Handles reading and parsing SWAT and SWAT+ output files including:
- output.rch (reach output)
- output.sub (subbasin output)
- output.hru (HRU output)
- SWAT+ equivalents (channel_sd_day.txt, basin_wb_day.txt, etc.)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SWATOutputParser:
    """
    Parser for SWAT (2012) output files
    
    Handles parsing of output.rch, output.sub, and output.hru files
    with support for different time steps (daily, monthly, yearly).
    """
    
    # Column definitions for SWAT output files
    REACH_COLUMNS = [
        'REACH', 'GIS', 'MON', 'AREAkm2', 'FLOW_INcms', 'FLOW_OUTcms',
        'EVAPcms', 'TLOSScms', 'SED_INtons', 'SED_OUTtons', 'SEDCONCmg/kg',
        'ORGN_INkg', 'ORGN_OUTkg', 'ORGP_INkg', 'ORGP_OUTkg', 'NO3_INkg',
        'NO3_OUTkg', 'NH4_INkg', 'NH4_OUTkg', 'NO2_INkg', 'NO2_OUTkg',
        'MINP_INkg', 'MINP_OUTkg', 'CHLA_INkg', 'CHLA_OUTkg', 'CBOD_INkg',
        'CBOD_OUTkg', 'DISOX_INkg', 'DISOX_OUTkg', 'SOLPST_INmg', 'SOLPST_OUTmg',
        'SORPST_INmg', 'SORPST_OUTmg', 'REACTPSTmg', 'VOLPSTmg', 'SETTLPSTmg',
        'RESUSP_PSTmg', 'DIFFUSEPSTmg', 'REACBEDPSTmg', 'BURYPSTmg',
        'BED_PSTmg', 'BACTP_OUTct', 'BACTLP_OUTct', 'CMETAL#1kg',
        'CMETAL#2kg', 'CMETAL#3kg', 'TOT Nkg', 'TOT Pkg', 'NO3ConcMg/l',
        'WTMPdegc'
    ]
    
    SUBBASIN_COLUMNS = [
        'SUB', 'GIS', 'MON', 'AREAkm2', 'PRECIPmm', 'SNOMELTmm', 'PETmm',
        'ETmm', 'SWmm', 'PERCmm', 'SURQmm', 'GW_Qmm', 'WYLDmm', 'SYLDt/ha',
        'ORGNkg/ha', 'ORGPkg/ha', 'NSURQkg/ha', 'SOLPkg/ha', 'SEDPkg/ha',
        'LAT Q(mm)', 'LATNO3kg/h', 'GWNO3kg/ha', 'CHOLAmic/L', 'CBODU mg/L',
        'DOXQ mg/L', 'TNO3kg'
    ]
    
    HRU_COLUMNS = [
        'LULC', 'HRU', 'GIS', 'SUB', 'MGT', 'MON', 'AREAkm2', 'PRECIPmm',
        'SNOFALLmm', 'SNOMELTmm', 'IRRmm', 'PETmm', 'ETmm', 'SW_INITmm',
        'SW_ENDmm', 'PERCmm', 'GW_RCHGmm', 'DA_RCHGmm', 'REVAPmm', 'SA_IRRmm',
        'DA_IRRmm', 'SA_STmm', 'DA_STmm', 'SURQ_GENmm', 'SURQ_CNTmm',
        'TLOSSmm', 'LATQmm', 'GW_Qmm', 'WYLDmm', 'DAILYCN', 'TMP_AVdgC',
        'TMP_MXdgC', 'TMP_MNdgC', 'SOL_TMPdgC', 'SOLARmj/m2', 'SYLDt/ha',
        'USLEt/ha', 'N_APPkg/ha', 'P_APPkg/ha', 'NAUTOkg/ha', 'PAUTOkg/ha',
        'NGRZkg/ha', 'PGRZkg/ha', 'NCFRTkg/ha', 'PCFRTkg/ha', 'NRAINkg/ha',
        'NFIXkg/ha', 'F-MNkg/ha', 'A-MNkg/ha', 'A-SNkg/ha', 'F-MPkg/ha',
        'AO-LPkg/ha', 'L-APkg/ha', 'A-SPkg/ha', 'DNITkg/ha', 'NUPkg/ha',
        'PUPkg/ha', 'ORGNkg/ha', 'ORGPkg/ha', 'SEDPkg/ha', 'NSURQkg/ha',
        'NLATQkg/ha', 'NO3Lkg/ha', 'NO3GWkg/ha', 'SOLPkg/ha', 'P_GWkg/ha',
        'W_STRS', 'TMP_STRS', 'N_STRS', 'P_STRS', 'BIOMt/ha', 'LAI',
        'YLDt/ha', 'BACTPct', 'BACTLPct', 'WTAB CLIm', 'WTAB SOLm',
        'SNOmm', 'CMUPkg/ha', 'CMTOTkg/ha', 'QTILEmm', 'TNO3kg/ha',
        'LNO3kg/ha', 'GW_Q_Dmm', 'LATQCNmg/L'
    ]
    
    def __init__(self):
        """Initialize SWAT output parser"""
        self.model_type = "SWAT"
    
    def parse_reach_output(
        self,
        file_path: Path,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Parse SWAT output.rch file
        
        Args:
            file_path: Path to output.rch file
            start_date: Filter start date (YYYY-MM-DD)
            end_date: Filter end date (YYYY-MM-DD)
            
        Returns:
            DataFrame with reach output data
            
        Example:
            >>> parser = SWATOutputParser()
            >>> df = parser.parse_reach_output(Path("output.rch"))
            >>> flow = df[df['REACH'] == 1]['FLOW_OUTcms']
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Read file, skip header lines (usually 9 lines)
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Find where data starts (after header)
            data_start = 0
            for i, line in enumerate(lines):
                if 'REACH' in line and 'GIS' in line and 'MON' in line:
                    data_start = i + 1
                    break
            
            if data_start == 0:
                raise ValueError("Could not find data header in output.rch")
            
            # Parse data
            data_lines = lines[data_start:]
            df = pd.read_csv(
                pd.io.common.StringIO(''.join(data_lines)),
                sep=r'\s+',
                names=self.REACH_COLUMNS[:len(lines[data_start].split())],
                skipinitialspace=True,
                on_bad_lines='skip'
            )
            
            # Add date column if possible
            if 'MON' in df.columns and start_date:
                df['DATE'] = self._reconstruct_dates(df, start_date)
            
            # Filter by date if requested
            if start_date and 'DATE' in df.columns:
                df = df[df['DATE'] >= start_date]
            if end_date and 'DATE' in df.columns:
                df = df[df['DATE'] <= end_date]
            
            logger.info(f"Parsed output.rch: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing output.rch: {e}")
            raise
    
    def parse_subbasin_output(
        self,
        file_path: Path,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Parse SWAT output.sub file
        
        Args:
            file_path: Path to output.sub file
            start_date: Filter start date
            end_date: Filter end date
            
        Returns:
            DataFrame with subbasin output data
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Similar parsing logic as reach output
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            data_start = 0
            for i, line in enumerate(lines):
                if 'SUB' in line and 'GIS' in line and 'MON' in line:
                    data_start = i + 1
                    break
            
            if data_start == 0:
                raise ValueError("Could not find data header in output.sub")
            
            data_lines = lines[data_start:]
            df = pd.read_csv(
                pd.io.common.StringIO(''.join(data_lines)),
                sep=r'\s+',
                names=self.SUBBASIN_COLUMNS[:len(lines[data_start].split())],
                skipinitialspace=True,
                on_bad_lines='skip'
            )
            
            logger.info(f"Parsed output.sub: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing output.sub: {e}")
            raise
    
    def parse_hru_output(
        self,
        file_path: Path,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Parse SWAT output.hru file
        
        Args:
            file_path: Path to output.hru file
            start_date: Filter start date
            end_date: Filter end date
            
        Returns:
            DataFrame with HRU output data
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            data_start = 0
            for i, line in enumerate(lines):
                if 'LULC' in line and 'HRU' in line:
                    data_start = i + 1
                    break
            
            if data_start == 0:
                raise ValueError("Could not find data header in output.hru")
            
            data_lines = lines[data_start:]
            df = pd.read_csv(
                pd.io.common.StringIO(''.join(data_lines)),
                sep=r'\s+',
                names=self.HRU_COLUMNS[:len(lines[data_start].split())],
                skipinitialspace=True,
                on_bad_lines='skip'
            )
            
            logger.info(f"Parsed output.hru: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing output.hru: {e}")
            raise
    
    def extract_reach_flow(
        self,
        file_path: Path,
        reach_id: int = 1,
        variable: str = 'FLOW_OUTcms'
    ) -> np.ndarray:
        """
        Extract flow timeseries for a specific reach
        
        Args:
            file_path: Path to output.rch file
            reach_id: Reach number to extract
            variable: Variable name to extract
            
        Returns:
            Array of flow values
        """
        df = self.parse_reach_output(file_path)
        reach_data = df[df['REACH'] == reach_id]
        
        if variable not in reach_data.columns:
            raise ValueError(f"Variable '{variable}' not found in output")
        
        return reach_data[variable].values
    
    def _reconstruct_dates(self, df: pd.DataFrame, start_date: str) -> pd.Series:
        """
        Reconstruct dates from MON column and start date
        
        Args:
            df: DataFrame with MON column
            start_date: Simulation start date (YYYY-MM-DD)
            
        Returns:
            Series of dates
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            dates = []
            
            for idx, row in df.iterrows():
                # Assuming MON is month number from start
                month_offset = int(row['MON']) - 1
                date = start + timedelta(days=30 * month_offset)  # Approximate
                dates.append(date)
            
            return pd.Series(dates, index=df.index)
            
        except Exception as e:
            logger.warning(f"Could not reconstruct dates: {e}")
            return pd.Series([None] * len(df), index=df.index)


class SWATPlusOutputParser:
    """
    Parser for SWAT+ output files
    
    Handles parsing of channel_sd_day.txt, basin_wb_day.txt, and other
    SWAT+ output files.
    """
    
    def __init__(self):
        """Initialize SWAT+ output parser"""
        self.model_type = "SWAT+"
    
    def parse_channel_output(
        self,
        file_path: Path,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Parse SWAT+ channel_sd_day.txt file
        
        Args:
            file_path: Path to channel_sd_day.txt file
            start_date: Filter start date
            end_date: Filter end date
            
        Returns:
            DataFrame with channel output data
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # SWAT+ files typically have header in first few lines
            df = pd.read_csv(
                file_path,
                sep=r'\s+',
                skiprows=3,  # Skip header lines
                skipinitialspace=True,
                on_bad_lines='skip'
            )
            
            logger.info(f"Parsed channel_sd_day.txt: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing channel_sd_day.txt: {e}")
            raise
    
    def parse_basin_output(
        self,
        file_path: Path,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Parse SWAT+ basin_wb_day.txt file
        
        Args:
            file_path: Path to basin_wb_day.txt file
            start_date: Filter start date
            end_date: Filter end date
            
        Returns:
            DataFrame with basin water balance data
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            df = pd.read_csv(
                file_path,
                sep=r'\s+',
                skiprows=3,
                skipinitialspace=True,
                on_bad_lines='skip'
            )
            
            logger.info(f"Parsed basin_wb_day.txt: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing basin_wb_day.txt: {e}")
            raise
    
    def extract_channel_flow(
        self,
        file_path: Path,
        channel_id: int = 1,
        variable: str = 'flo_out'
    ) -> np.ndarray:
        """
        Extract flow timeseries for a specific channel
        
        Args:
            file_path: Path to channel output file
            channel_id: Channel number
            variable: Variable name
            
        Returns:
            Array of flow values
        """
        df = self.parse_channel_output(file_path)
        
        # Filter by channel ID if column exists
        if 'gis_id' in df.columns:
            channel_data = df[df['gis_id'] == channel_id]
        else:
            channel_data = df
        
        if variable not in channel_data.columns:
            available = ', '.join(channel_data.columns)
            raise ValueError(f"Variable '{variable}' not found. Available: {available}")
        
        return channel_data[variable].values


def parse_swat_output(
    output_dir: Path,
    output_type: str = "reach",
    model_type: str = "SWAT",
    **kwargs
) -> pd.DataFrame:
    """
    Convenience function to parse SWAT output files
    
    Args:
        output_dir: Directory containing output files
        output_type: Type of output ("reach", "subbasin", "hru")
        model_type: "SWAT" or "SWAT+"
        **kwargs: Additional arguments passed to parser
        
    Returns:
        DataFrame with parsed output data
        
    Example:
        >>> df = parse_swat_output(Path("./run_1"), output_type="reach")
        >>> flow = df[df['REACH'] == 1]['FLOW_OUTcms']
    """
    if model_type == "SWAT":
        parser = SWATOutputParser()
        
        if output_type == "reach":
            file_path = output_dir / "output.rch"
            return parser.parse_reach_output(file_path, **kwargs)
        elif output_type == "subbasin":
            file_path = output_dir / "output.sub"
            return parser.parse_subbasin_output(file_path, **kwargs)
        elif output_type == "hru":
            file_path = output_dir / "output.hru"
            return parser.parse_hru_output(file_path, **kwargs)
        else:
            raise ValueError(f"Unknown output_type: {output_type}")
            
    else:  # SWAT+
        parser = SWATPlusOutputParser()
        
        if output_type == "channel":
            file_path = output_dir / "channel_sd_day.txt"
            return parser.parse_channel_output(file_path, **kwargs)
        elif output_type == "basin":
            file_path = output_dir / "basin_wb_day.txt"
            return parser.parse_basin_output(file_path, **kwargs)
        else:
            raise ValueError(f"Unknown output_type for SWAT+: {output_type}")


def parse_swat_plus_output(
    output_dir: Path,
    output_type: str = "channel",
    **kwargs
) -> pd.DataFrame:
    """
    Convenience function specifically for SWAT+ outputs
    
    Args:
        output_dir: Directory containing SWAT+ output files
        output_type: Type of output ("channel", "basin", "aquifer", "hru")
        **kwargs: Additional arguments
        
    Returns:
        DataFrame with parsed output
    """
    return parse_swat_output(output_dir, output_type, model_type="SWAT+", **kwargs)


def extract_timeseries(
    df: pd.DataFrame,
    variable: str,
    entity_id: Optional[int] = None,
    entity_column: str = 'REACH'
) -> np.ndarray:
    """
    Extract timeseries for a specific variable and entity
    
    Args:
        df: DataFrame from parsed output
        variable: Variable name to extract
        entity_id: Entity ID (reach, sub, HRU) - if None, use all
        entity_column: Column name for entity ID
        
    Returns:
        Array of values
        
    Example:
        >>> df = parse_swat_output(Path("output"), "reach")
        >>> flow = extract_timeseries(df, 'FLOW_OUTcms', entity_id=1, entity_column='REACH')
    """
    if variable not in df.columns:
        available = ', '.join(df.columns)
        raise ValueError(f"Variable '{variable}' not found. Available: {available}")
    
    if entity_id is not None and entity_column in df.columns:
        filtered = df[df[entity_column] == entity_id]
    else:
        filtered = df
    
    return filtered[variable].values


def get_available_variables(file_path: Path, model_type: str = "SWAT") -> List[str]:
    """
    Get list of available variables in an output file
    
    Args:
        file_path: Path to output file
        model_type: "SWAT" or "SWAT+"
        
    Returns:
        List of variable names
    """
    try:
        if model_type == "SWAT":
            parser = SWATOutputParser()
            if 'rch' in file_path.name:
                return parser.REACH_COLUMNS
            elif 'sub' in file_path.name:
                return parser.SUBBASIN_COLUMNS
            elif 'hru' in file_path.name:
                return parser.HRU_COLUMNS
        else:
            # Parse first few lines to get column names
            df = pd.read_csv(file_path, sep=r'\s+', nrows=1, skiprows=3)
            return df.columns.tolist()
            
    except Exception as e:
        logger.error(f"Error getting variables: {e}")
        return []
