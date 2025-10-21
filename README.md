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

## Requirements

- Python 3.10+
- SWAT or SWAT+ executable
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

**Version**: 0.1.0-alpha  
**Status**: Under Active Development
