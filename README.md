# PySWATCal

**Python SWAT Calibration & Analysis Tool**

A modern Python-based tool for SWAT/SWAT+ model calibration, sensitivity analysis, and uncertainty quantification.

## Features

- **Multiple Calibration Algorithms**: DDS, GLUE, PSO, Bayesian Optimization
- **Sensitivity Analysis**: Morris, Sobol, FAST methods
- **Parallel Processing**: Efficient multi-core execution
- **Interactive Visualizations**: Real-time results with Plotly
- **Modern UI**: Intuitive web interface built with Streamlit
- **Project Management**: Save/load projects in JSON format

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ductran27/PySWATCal.git
cd PySWATCal

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
streamlit run app.py
```

> On first launch Streamlit may ask for an email address; simply press Enter to skip.  
> This project ships with `.streamlit/config.toml` setting `browser.gatherUsageStats = false`
> so future runs skip the prompt automatically.

## Step-by-Step Calibration Guide

### Quick Start: Run Your First Calibration

Follow these steps to calibrate your SWAT model:

#### Step 1: Prepare Your Data

You need:
1. **SWAT Model Directory** - TxtInOut folder with your SWAT model files
2. **SWAT Executable** - Platform-appropriate SWAT executable
   - Windows: `.exe` file
   - Linux/macOS: Linux executable + Docker Desktop installed
3. **Observed Data** - Text file with observed streamflow (or other variable)

#### Step 2: Start the Application

```bash
# Activate your virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Launch the web interface
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

#### Step 3: Create a Project (Project Setup Page)

1. Click **"Project Setup"** in the sidebar
2. Fill in project details:
   - **Project Name**: e.g., "MyBasin_Calibration"
   - **Working Directory**: Where results will be saved
   - **TxtInOut Directory**: Path to your SWAT TxtInOut folder
   - **Model Type**: Select "SWAT" or "SWAT+"
   - **SWAT Executable**: Path to your SWAT executable
3. Click **"Create Project"**

#### Step 4: Add Calibration Parameters (Parameters Page)

1. Click **"Parameters"** in the sidebar
2. For each parameter to calibrate:
   - **Parameter Name**: e.g., "CN2", "ALPHA_BF"
   - **File Extension**: e.g., ".mgt", ".gw"
   - **Min/Max Values**: Set calibration bounds
   - **Change Type**: "relative", "replace", or "absolute"
3. Click **"Add Parameter"**
4. Repeat for all parameters (typically 5-20 parameters)

**Recommended parameters for streamflow calibration:**
- CN2 (.mgt): -0.25 to 0.25 (relative)
- ALPHA_BF (.gw): 0.01 to 1.0 (replace)
- GW_DELAY (.gw): 0 to 500 (replace)
- ESCO (.hru): 0.0 to 1.0 (replace)
- CH_N2 (.rte): 0.0 to 0.3 (replace)

#### Step 5: Run Calibration (Run Calibration Page)

1. Click **"Run Calibration"** in the sidebar
2. Configure calibration settings:
   - **Algorithm**: Choose DDS, GLUE, or PSO
   - **Iterations**: 100-500 (more = better but slower)
   - **Objective Function**: NSE, KGE, or custom
   - **Observed Data File**: Upload or select your observations
3. Click **"Start Calibration"**
4. Monitor progress in real-time

#### Step 6: View Results (Results Page)

1. Click **"Results"** in the sidebar
2. View performance metrics:
   - NSE, KGE, RMSE, PBIAS values
   - Parameter convergence plots
   - Observed vs. Simulated hydrographs
   - Flow duration curves
3. Download results and calibrated parameters

### Command-Line Calibration (Advanced)

For automated workflows or batch processing:

```bash
# Run calibration via Python script
python examples/demo_test.py

# Or create your own script (see Usage section below)
python my_calibration_script.py
```

## Usage

### Option 1: Python API (Programmatic Usage)

For researchers and developers who prefer command-line or script-based workflows:

```python
from pyswatcal import Project
from pyswatcal.core import FileManager, SWATRunner
from pyswatcal.calibration import DDS, GLUE, PSO
from pyswatcal.calibration import nse, kge, rmse
from pyswatcal.utils import parse_swat_output, extract_timeseries
from pathlib import Path
import numpy as np

# 1. Create a calibration project
project = Project.create(
    name="MyBasin_Calibration",
    working_dir=Path("./my_calibration"),
    txtinout_dir=Path("./my_swat_project/TxtInOut"),
    model_type="SWAT"
)

# 2. Add parameters to calibrate
project.add_parameter("CN2", ".mgt", -0.2, 0.2, "relative")
project.add_parameter("ALPHA_BF", ".gw", 0.0, 1.0, "replace")
project.add_parameter("GW_DELAY", ".gw", 0, 500, "replace")

# 3. Setup SWAT runner
fm = FileManager(project.txtinout_dir, project.working_dir)
runner = SWATRunner(Path("./swat.exe"), fm)

# 4. Load observed data
observed = np.loadtxt("observed_flow.txt")

# 5. Define objective function
def calibration_objective(params):
    # Run SWAT with parameter set
    result = runner.run_simulation(
        run_id=np.random.randint(1000000),
        parameters={
            "CN2": params[0],
            "ALPHA_BF": params[1],
            "GW_DELAY": params[2]
        }
    )
    
    if not result["success"]:
        return -999  # Penalty for failed runs
    
    # Read simulated output
    df = parse_swat_output(result["run_dir"], "reach", "SWAT")
    simulated = extract_timeseries(df, 'FLOW_OUTcms', entity_id=1, entity_column='REACH')
    
    # Calculate NSE
    return nse(observed, simulated[:len(observed)])

# 6. Run DDS calibration
bounds = [(-0.2, 0.2), (0.0, 1.0), (0, 500)]
dds = DDS(bounds, calibration_objective, n_iterations=100, maximize=True)
results = dds.optimize()

# 7. View results
print(f"Best NSE: {results['best_value']:.4f}")
print(f"Best CN2: {results['best_params'][0]:.4f}")
print(f"Best ALPHA_BF: {results['best_params'][1]:.4f}")
print(f"Best GW_DELAY: {results['best_params'][2]:.1f}")

# 8. Save project with results
project.results = results
project.save()
```

### Option 2: Run Validation Tests

```bash
python examples/demo_test.py
```

This runs comprehensive validation using the included demo SWAT watershed.

## Project Structure

```
PySWATCal/
├── pyswatcal/          # Core Python package
│   ├── core/           # SWAT runner, file managers
│   ├── calibration/    # Calibration algorithms
│   ├── sensitivity/    # Sensitivity analysis
│   ├── utils/          # Utilities and helpers
│   └── ui/             # User interface components
├── tests/              # Unit and integration tests
├── docs/               # Documentation
├── examples/           # Example projects
└── app.py              # Main Streamlit application
```

## Cross-Platform Support

### Running SWAT on macOS and Linux

SWAT executables are platform-specific, with most distributions providing only Windows binaries. PySWATCal addresses this limitation through Docker integration, enabling SWAT execution on macOS and Linux without requiring virtual machines.

### Platform Compatibility

SWAT model executables come in different formats:
- **Windows**: `.exe` files (most commonly distributed)
- **Linux**: ELF binaries (available from SWAT developers)
- **macOS**: Native binaries are rarely available

Traditionally, macOS and Linux users needed virtual machines or dual-boot configurations to run SWAT models.

### Docker Integration

PySWATCal includes Docker support that works automatically based on your system configuration:

**Automatic detection**: The `SWATRunner` class detects your platform and executable type, then selects the appropriate execution method.

**Platform behavior:**
- **Windows**: Runs `.exe` files natively without Docker
- **Linux**: Runs Linux binaries natively without Docker
- **macOS**: Automatically uses Docker to run Linux binaries in a container
- **Any platform with incompatible executable**: Falls back to Docker automatically

This approach requires no manual configuration - users simply provide their SWAT executable, and PySWATCal handles the rest.

### Setting Up Docker for SWAT

#### Prerequisites

1. **Install Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop/
   - Available for macOS, Windows, and Linux
   - Free for personal use

2. **Obtain Linux SWAT Executable**
   - Request from SWAT development team
   - Or compile from source for Linux

#### Docker Configuration

PySWATCal includes a `Dockerfile.swat` that sets up the Ubuntu environment with required Fortran libraries:

```dockerfile
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y libgfortran5
WORKDIR /swat
CMD ["./swat_executable"]
```

The `SWATRunner` class automatically:
- Builds the Docker image when needed
- Mounts your SWAT model files as volumes
- Executes SWAT in the container
- Retrieves results back to your host system

#### Usage Example with Docker

```python
from pyswatcal.core import FileManager, SWATRunner
from pathlib import Path

# Point to your Linux SWAT executable
swat_linux_exe = Path("./swat_linux_executable")

# Initialize with Docker support (automatic on macOS/Linux)
fm = FileManager(txtinout_dir, working_dir)
runner = SWATRunner(swat_linux_exe, fm)

# Run simulation - Docker handles everything automatically
result = runner.run_simulation(run_id=1, parameters=params)

# Results are in your working directory as usual
```

### Benefits of Docker Approach

**Cross-platform**: Same code runs on macOS, Linux, and Windows  
**No VM overhead**: Lightweight compared to traditional virtual machines  
**Reproducible**: Consistent environment across all systems  
**Integrated**: Works seamlessly with PySWATCal's workflow  
**Fast**: Near-native performance  

### Validated Configuration

This approach has been successfully tested with:
- **Host OS**: macOS (Apple Silicon and Intel)
- **SWAT Version**: rev688 Linux executable
- **Basin**: USGS basin 05459500 (Iowa River at Wapello, IA)
- **Performance**: Real calibration metrics obtained (NSE, KGE, RMSE, PBIAS)

## Requirements

- Python 3.10+
- SWAT or SWAT+ executable (Windows, Linux, or via Docker)
- **Docker Desktop** (required for macOS/Linux users with Linux SWAT executables)
- 4GB+ RAM recommended for parallel processing

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

- SWAT model developers at Texas A&M University
- Inspired by R-SWAT for workflow design
- Built with modern Python scientific stack

## Citation

If you use PySWATCal in your research, please cite:

```
Tran, T.N.D. (2025). PySWATCal: Python SWAT Calibration & Analysis Tool. 
https://github.com/ductran27/PySWATCal
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Support

- 📧 Email: syu3cs@virginia.edu
- 💬 Issues: [GitHub Issues](https://github.com/ductran27/PySWATCal/issues)
- 📖 Documentation: [docs/](docs/)

---

**Version**: 0.2.0  
**Status**: Stable - Docker Integration & Cross-Platform Support
