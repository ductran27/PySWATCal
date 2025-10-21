"""
Sensitivity analysis modules for PySWATCal
"""

from pyswatcal.sensitivity.morris import MorrisAnalysis
from pyswatcal.sensitivity.sobol import SobolAnalysis

__all__ = ["MorrisAnalysis", "SobolAnalysis"]
