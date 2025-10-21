"""
PySWATCal - Python SWAT Calibration & Analysis Tool

A modern Python-based tool for SWAT/SWAT+ model calibration,
sensitivity analysis, and uncertainty quantification.
"""

__version__ = "0.1.0"
__author__ = "PySWATCal Development Team"
__license__ = "MIT"

from pyswatcal.core.config import Config
from pyswatcal.core.project import Project

__all__ = ["Config", "Project", "__version__"]
