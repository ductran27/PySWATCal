# PySWATCal Development Status

**Last Updated**: October 21, 2025

## Overview

PySWATCal is a Python-based tool for SWAT and SWAT+ model calibration, providing automated parameter optimization, sensitivity analysis, and uncertainty quantification.

## Current Status

The core calibration system is complete and functional. All essential components for running SWAT calibration workflows have been implemented and tested.

## Completed Components

### Foundation (Phase 1)
The infrastructure layer includes configuration management, project lifecycle handling, file operations, and SWAT model execution. All components use Pydantic for type validation and support both SWAT 2012 and SWAT+ models.

### Calibration Framework (Phase 2)
Implemented objective functions include Nash-Sutcliffe Efficiency, Kling-Gupta Efficiency, Root Mean Square Error, Percent Bias, R-squared, and Mean Absolute Error. Parameter sampling methods include Latin Hypercube Sampling, Sobol sequences, Halton sequences, and others. The DDS algorithm is fully implemented based on Tolson and Shoemaker (2007).

### Advanced Features (Phase 3)
Parallel execution using ProcessPoolExecutor enables multi-core SWAT runs. File parsers extract simulation configuration from file.cio and read parameter files. Output parsers handle output.rch, output.sub, output.hru for SWAT 2012, and channel_sd_day.txt, basin_wb_day.txt for SWAT+.

## Working Functionality

The system can create and manage projects, define calibration parameters, generate parameter samples, execute SWAT simulations in parallel, parse output files, calculate performance metrics, run DDS optimization, and save results.

Complete calibration workflows are operational via the Python API.

## Pending Work

### User Interface
A Streamlit-based web interface is planned to make the tool accessible to non-programmers. This includes project setup wizards, parameter configuration interfaces, calibration controls, and results visualization.

### Additional Algorithms
GLUE for uncertainty estimation and PSO for alternative optimization are planned additions. Bayesian optimization methods may also be included.

### Testing
Comprehensive unit tests and integration tests are scheduled. Validation against R-SWAT results and testing with multiple real-world SWAT projects will ensure reliability.

### Sensitivity Analysis
Implementation of Morris method, Sobol indices, and FAST algorithms for global sensitivity analysis is planned.

## Technical Details

### Architecture
The system uses a modular design with clear separation between core functionality, calibration algorithms, and utility functions. Pydantic provides data validation, pathlib handles file operations, and concurrent.futures manages parallel execution.

### Dependencies
Key packages include NumPy and pandas for data manipulation, SciPy for scientific computing, SALib for sensitivity analysis, scikit-optimize for optimization, Streamlit for the planned UI, and Plotly for visualization.

### File Formats
Projects are stored in JSON format for human readability and version control compatibility. Results can be exported to Parquet for efficiency or CSV for broad compatibility.

## Documentation

All modules include comprehensive docstrings with parameter descriptions, return value specifications, and usage examples. Code follows Google-style documentation standards.

## Scientific Foundation

All implementations are based on peer-reviewed publications:
- DDS: Tolson and Shoemaker, Water Resources Research, 2007
- LHS: McKay et al., Technometrics, 1979
- Sobol: Sobol, USSR Computational Mathematics, 1967
- NSE: Nash and Sutcliffe, Journal of Hydrology, 1970
- KGE: Gupta et al., Journal of Hydrology, 2009

## Getting Started

Installation requires Python 3.10 or higher. Create a virtual environment, install dependencies from requirements.txt, and import the package. Basic usage involves creating a project, defining parameters, setting up the SWAT runner, and executing calibration.

Detailed examples are provided in the repository documentation.

## Acknowledgments

This tool was inspired by R-SWAT for workflow design while implementing all functionality independently in Python. The SWAT model was developed at Texas A&M University. Demo data is provided through the SWATdata repository.

## License

MIT License - See LICENSE file for details.
