# Demo Data Documentation

## Source

The demo SWAT watershed data used in PySWATCal was obtained from the SWATdata repository:

**Repository**: https://github.com/chrisschuerz/SWATdata  
**License**: As specified in the SWATdata repository  
**Location in PySWATCal**: `examples/SWATdata/`

## Watershed Information

**Name**: Little River Experimental Watershed (LREW)  
**Location**: Headwater watershed (gauge J)  
**SWAT Version**: SWAT 2012 Revision 622  
**Simulation Period**: 2000-2012 (13 years)  
**Spatial Units**: 134 HRUs across multiple subbasins

## Reference

Bosch, D. D., Sheridan, J. M., Lowrance, R. R., Hubbard, R. K., Strickland, T. C., Feyereisen, G. W., and Sullivan, D. G. (2007). Little river experimental watershed database. Water Resources Research, 43(9). https://doi.org/10.1029/2006wr005844

## Purpose in PySWATCal

The demo data serves multiple purposes:
- Testing and validation of PySWATCal functionality
- Demonstrating complete calibration workflows
- Providing example project structure
- Enabling integration tests
- Training users on proper usage

## Data Structure

The demo includes:
- Complete TxtInOut directory with all SWAT input files
- HRU files (.hru) for 134 hydrologic response units
- Management files (.mgt) with land use operations
- Soil files (.sol) with soil properties
- Groundwater files (.gw) with aquifer parameters
- Routing files (.rte) for channel routing
- Basin file (basins.bsn) with watershed-level parameters
- Climate data files (precipitation, temperature)
- Configuration file (file.cio) with simulation settings

## Usage in PySWATCal

```python
from pathlib import Path
from pyswatcal import Project

# Use demo data
demo_path = Path("examples/swat_demo/swat2012_rev622_demo")

project = Project.create(
    name="Demo_Calibration",
    working_dir=Path("./work"),
    txtinout_dir=demo_path,
    model_type="SWAT"
)
```

## Validation Tests

The demo data is used in:
- `examples/demo_test.py` - Comprehensive validation script
- Integration tests for file parsers
- Project creation and management tests
- SWAT model type detection tests

## Acknowledgments

We thank the developers of SWATdata for providing this valuable resource for testing and demonstration purposes. The data represents a well-documented experimental watershed suitable for hydrological model validation.

## Additional Resources

For more information about the Little River Experimental Watershed and the SWATdata package, visit:
- SWATdata GitHub: https://github.com/chrisschuerz/SWATdata
- SWAT Model: https://swat.tamu.edu/
- Original watershed data: USDA-ARS Southeast Watershed Research Laboratory
