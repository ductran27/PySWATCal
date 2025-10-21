"""
Parallel execution engine for running multiple SWAT simulations

Handles multi-process execution of SWAT with progress tracking,
error handling, and resource management.
"""

import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import time
from datetime import datetime
from tqdm import tqdm

from pyswatcal.core.swat_runner import SWATRunner
from pyswatcal.core.file_manager import FileManager

logger = logging.getLogger(__name__)


class ParallelSWATRunner:
    """
    Parallel execution engine for SWAT simulations
    
    Manages multiple SWAT runs in parallel using process pooling.
    Provides progress tracking, error handling, and result aggregation.
    
    Attributes:
        swat_runner: SWATRunner instance
        n_workers: Number of parallel workers
        show_progress: Whether to show progress bar
    """
    
    def __init__(
        self,
        swat_runner: SWATRunner,
        n_workers: Optional[int] = None,
        show_progress: bool = True
    ):
        """
        Initialize parallel runner
        
        Args:
            swat_runner: SWATRunner instance for executing SWAT
            n_workers: Number of parallel workers (None = auto-detect)
            show_progress: Whether to show progress bar
        """
        self.swat_runner = swat_runner
        self.show_progress = show_progress
        
        # Auto-detect number of workers
        if n_workers is None:
            n_workers = max(1, cpu_count() - 1)  # Leave one core free
        
        self.n_workers = min(n_workers, cpu_count())
        
        logger.info(f"Initialized ParallelSWATRunner with {self.n_workers} workers")
    
    def run_parallel(
        self,
        parameter_sets: np.ndarray,
        callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Run SWAT simulations in parallel
        
        Args:
            parameter_sets: Array of shape (n_runs, n_parameters)
            callback: Optional callback function called after each completion
            
        Returns:
            List of result dictionaries from each simulation
        """
        n_runs = len(parameter_sets)
        logger.info(f"Starting {n_runs} parallel SWAT runs with {self.n_workers} workers")
        
        start_time = time.time()
        results = [None] * n_runs
        
        # Create tasks
        tasks = []
        for i, params in enumerate(parameter_sets):
            param_dict = self._params_array_to_dict(params)
            tasks.append((i, param_dict))
        
        # Execute in parallel
        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._run_single, run_id, params): (run_id, params)
                for run_id, params in tasks
            }
            
            # Process completed tasks
            if self.show_progress:
                pbar = tqdm(total=n_runs, desc="Running SWAT", unit="sim")
            
            completed = 0
            for future in as_completed(future_to_task):
                run_id, params = future_to_task[future]
                
                try:
                    result = future.result()
                    results[run_id] = result
                    
                    # Callback
                    if callback is not None:
                        callback(run_id, params, result)
                    
                except Exception as e:
                    logger.error(f"Run {run_id} failed: {e}")
                    results[run_id] = {
                        'success': False,
                        'run_id': run_id,
                        'error': str(e)
                    }
                
                completed += 1
                if self.show_progress:
                    pbar.update(1)
                    # Update description with success rate
                    n_success = sum(1 for r in results[:completed] if r and r.get('success'))
                    pbar.set_postfix({
                        'success': f"{n_success}/{completed}",
                        'rate': f"{n_success/completed*100:.1f}%"
                    })
            
            if self.show_progress:
                pbar.close()
        
        duration = time.time() - start_time
        n_success = sum(1 for r in results if r and r.get('success'))
        
        logger.info(
            f"Parallel execution completed: "
            f"{n_success}/{n_runs} successful, "
            f"Duration: {duration:.2f}s"
        )
        
        return results
    
    def _run_single(self, run_id: int, parameters: Dict[str, float]) -> Dict[str, Any]:
        """
        Run a single SWAT simulation
        
        This method is called in separate processes
        """
        try:
            result = self.swat_runner.run_simulation(
                run_id=run_id,
                parameters=parameters,
                capture_output=False  # Don't capture output in parallel mode
            )
            return result
        except Exception as e:
            logger.error(f"Error in run {run_id}: {e}")
            return {
                'success': False,
                'run_id': run_id,
                'error': str(e)
            }
    
    def _params_array_to_dict(self, params: np.ndarray) -> Dict[str, float]:
        """
        Convert parameter array to dictionary
        
        This is a simplified version - in practice, you'd need
        to map indices to parameter names
        """
        # Placeholder - needs to be connected to project parameters
        param_names = [f"param_{i}" for i in range(len(params))]
        return dict(zip(param_names, params))
    
    def estimate_runtime(self, n_runs: int, avg_runtime: float) -> Dict[str, float]:
        """
        Estimate total runtime for parallel execution
        
        Args:
            n_runs: Number of runs to execute
            avg_runtime: Average runtime per simulation (seconds)
            
        Returns:
            Dictionary with estimated times
        """
        # Sequential time
        sequential_time = n_runs * avg_runtime
        
        # Parallel time (accounting for overhead)
        parallel_efficiency = 0.85  # Typical efficiency factor
        parallel_time = (n_runs / self.n_workers) * avg_runtime / parallel_efficiency
        
        # Speedup
        speedup = sequential_time / parallel_time
        
        return {
            'n_runs': n_runs,
            'n_workers': self.n_workers,
            'avg_runtime_per_sim': avg_runtime,
            'estimated_sequential_time': sequential_time,
            'estimated_parallel_time': parallel_time,
            'estimated_speedup': speedup,
            'parallel_efficiency': parallel_efficiency
        }
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ParallelSWATRunner(n_workers={self.n_workers})"


class BatchRunner:
    """
    Batch runner for multiple calibration runs
    
    Manages execution of multiple calibration experiments
    with different settings or initial conditions.
    """
    
    def __init__(
        self,
        swat_runner: SWATRunner,
        output_dir: Path,
        n_workers: Optional[int] = None
    ):
        """
        Initialize batch runner
        
        Args:
            swat_runner: SWATRunner instance
            output_dir: Directory to save batch results
            n_workers: Number of parallel workers
        """
        self.swat_runner = swat_runner
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.parallel_runner = ParallelSWATRunner(
            swat_runner=swat_runner,
            n_workers=n_workers
        )
        
        self.batch_results = []
    
    def run_batch(
        self,
        parameter_sets_list: List[np.ndarray],
        batch_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Run multiple batches of simulations
        
        Args:
            parameter_sets_list: List of parameter set arrays
            batch_names: Optional names for each batch
            
        Returns:
            List of batch results
        """
        n_batches = len(parameter_sets_list)
        
        if batch_names is None:
            batch_names = [f"batch_{i}" for i in range(n_batches)]
        
        logger.info(f"Starting {n_batches} batches")
        
        for i, (params, name) in enumerate(zip(parameter_sets_list, batch_names)):
            logger.info(f"Running batch {i+1}/{n_batches}: {name}")
            
            start_time = time.time()
            results = self.parallel_runner.run_parallel(params)
            duration = time.time() - start_time
            
            batch_result = {
                'batch_name': name,
                'batch_index': i,
                'n_runs': len(params),
                'results': results,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }
            
            self.batch_results.append(batch_result)
            
            # Save batch results
            self._save_batch_result(batch_result)
        
        return self.batch_results
    
    def _save_batch_result(self, batch_result: Dict[str, Any]) -> None:
        """Save batch result to file"""
        import json
        
        filename = f"{batch_result['batch_name']}.json"
        filepath = self.output_dir / filename
        
        # Convert numpy arrays to lists for JSON serialization
        serializable_result = self._make_json_serializable(batch_result)
        
        with open(filepath, 'w') as f:
            json.dump(serializable_result, f, indent=2)
        
        logger.info(f"Saved batch results to {filepath}")
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert object to JSON-serializable format"""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, Path):
            return str(obj)
        else:
            return obj
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all batch runs
        
        Returns:
            Summary dictionary
        """
        if not self.batch_results:
            return {'n_batches': 0}
        
        total_runs = sum(b['n_runs'] for b in self.batch_results)
        total_duration = sum(b['duration'] for b in self.batch_results)
        
        success_counts = []
        for batch in self.batch_results:
            n_success = sum(1 for r in batch['results'] if r.get('success'))
            success_counts.append(n_success)
        
        return {
            'n_batches': len(self.batch_results),
            'total_runs': total_runs,
            'total_duration': total_duration,
            'success_counts': success_counts,
            'batch_names': [b['batch_name'] for b in self.batch_results]
        }


def run_parallel_simulations(
    swat_runner: SWATRunner,
    parameter_sets: np.ndarray,
    n_workers: Optional[int] = None,
    show_progress: bool = True
) -> List[Dict[str, Any]]:
    """
    Convenience function for parallel SWAT runs
    
    Args:
        swat_runner: SWATRunner instance
        parameter_sets: Parameter sets to run
        n_workers: Number of workers
        show_progress: Show progress bar
        
    Returns:
        List of simulation results
    """
    parallel_runner = ParallelSWATRunner(
        swat_runner=swat_runner,
        n_workers=n_workers,
        show_progress=show_progress
    )
    
    return parallel_runner.run_parallel(parameter_sets)
