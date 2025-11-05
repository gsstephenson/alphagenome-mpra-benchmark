#!/usr/bin/env python3
"""
Master Pipeline: AlphaGenome vs MPRA Benchmark
Author: Generated for Layer Lab Rotation
Date: October 30, 2025

This script runs the complete benchmarking pipeline:
1. Prepare MPRA data
2. Run AlphaGenome predictions
3. Compute benchmark metrics and visualizations
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path('/mnt/work_1/gest9386/CU_Boulder/rotations/LAYER/GSE84888_MPRA')
CODE_DIR = BASE_DIR / 'code'

def run_script(script_name, description):
    """Run a Python script and handle errors."""
    print("\n" + "="*70)
    print(f"STEP: {description}")
    print("="*70)
    
    script_path = CODE_DIR / script_name
    
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        sys.exit(1)
    
    try:
        result = subprocess.run(
            ['python', str(script_path)],
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n✓ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} failed with error code {e.returncode}")
        print(f"Error: {e}")
        return False

def main():
    """Run the complete pipeline."""
    print("="*70)
    print("AlphaGenome vs MPRA Benchmarking Pipeline")
    print("="*70)
    print(f"\nWorking directory: {BASE_DIR}")
    print(f"Code directory: {CODE_DIR}")
    
    # Pipeline steps
    steps = [
        ('01_prepare_mpra_data.py', 'Data Preparation'),
        ('02_run_alphagenome_predictions.py', 'AlphaGenome Predictions'),
        ('03_benchmark_correlations.py', 'Benchmark Analysis'),
        ('04_pparg_paradox_investigation.py', 'PPARγ Paradox Investigation'),
        ('05_wildtype_validation.py', 'Wildtype Validation'),
    ]
    
    # Run each step
    for script, description in steps:
        success = run_script(script, description)
        if not success:
            print(f"\n{'='*70}")
            print(f"Pipeline failed at: {description}")
            print(f"{'='*70}")
            sys.exit(1)
    
    # Success message
    print("\n" + "="*70)
    print("PIPELINE COMPLETE!")
    print("="*70)
    print(f"\nAll outputs saved to: {BASE_DIR / 'outputs'}")
    print("\nGenerated files:")
    print("  01_prepared_data/")
    print("    - mpra_sequences_summary.csv")
    print("    - mpra_all_variants.csv")
    print("    - mpra_sample_100.csv")
    print("  02_alphagenome_predictions/")
    print("    - alphagenome_predictions_sample100.csv")
    print("  03_benchmark_results/")
    print("    - benchmark_summary.csv")
    print("    - scatter plots (6 files)")
    print("    - ROC curves (3 files)")
    print("    - correlation_heatmap.png")
    print("    - prediction_distributions.png")
    print("  04_pparg_results/")
    print("    - pparg_paradox_investigation.png")
    print("  05_wildtype_validation/")
    print("    - wildtype_vs_mutant_correlations.png")
    print("    - mutation_effect_distributions.png")
    print("    - correlation_comparison_summary.csv")
    print("\n" + "="*70)

if __name__ == '__main__':
    main()
