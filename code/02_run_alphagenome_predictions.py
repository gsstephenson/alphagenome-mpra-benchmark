#!/usr/bin/env python3
"""
Step 2: Run AlphaGenome predictions on MPRA sequences - VERSION 2
Author: Generated for Layer Lab Rotation
Date: October 30, 2025

VERSION 2 ENHANCEMENTS:
- Processes all 6,963 variants with 2KB genomic sequences
- Implements checkpointing to resume from failures
- Progress tracking with ETA
- Batch processing to manage memory
- Rate limiting to respect API quotas

This script:
1. Loads prepared MPRA sequences with 2KB genomic context
2. Runs AlphaGenome predictions for each sequence
3. Implements automatic checkpointing every 100 sequences
4. Collects multiple prediction metrics (DNase, CAGE, RNA-seq)
5. Saves predictions alongside MPRA measurements
6. Can resume from last checkpoint if interrupted
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import time
import json
from datetime import datetime

# Load environment and AlphaGenome
from dotenv import load_dotenv
from alphagenome.data import genome
from alphagenome.models import dna_client
from alphagenome.models import variant_scorers

# Set paths
BASE_DIR = Path('/mnt/work_1/gest9386/CU_Boulder/rotations/LAYER/GSE84888_MPRA')
DATA_DIR = BASE_DIR / 'outputs' / '01_prepared_data'
OUTPUT_DIR = BASE_DIR / 'outputs' / '02_alphagenome_predictions'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Checkpointing settings
CHECKPOINT_DIR = OUTPUT_DIR / 'checkpoints'
CHECKPOINT_DIR.mkdir(exist_ok=True)
CHECKPOINT_INTERVAL = 100  # Save every 100 sequences

# Load API key
env_path = Path('/mnt/work_1/gest9386/CU_Boulder/rotations/LAYER/Alpha_genome_quickstart_notebook/.env')
load_dotenv(env_path)
api_key = os.getenv('ALPHA_GENOME_API_KEY') or os.getenv('ALPHA_GENOME_KEY')

if not api_key:
    raise RuntimeError('Missing ALPHA_GENOME_API_KEY in environment. Check the .env file.')

print("Initializing AlphaGenome model...")
dna_model = dna_client.create(api_key)
print("✓ Model initialized")

def predict_for_sequence(sequence, variant_id, cell_line='K562'):
    """
    Run AlphaGenome predictions for a single 2048bp sequence.
    VERSION 2: Sequences are already 2048bp from genome extraction.
    Returns a dictionary of prediction scores.
    """
    # K562 is an erythroleukemia cell line
    ontology_term = 'EFO:0002067'  # K562 cell line
    
    predictions = {}
    predictions['variant_id'] = variant_id
    
    try:
        # Ensure sequence is exactly 2048bp (AlphaGenome requirement)
        if len(sequence) != 2048:
            raise ValueError(f"Sequence length is {len(sequence)}, expected 2048")
        
        # Predict DNase (chromatin accessibility)
        output_dnase = dna_model.predict_sequence(
            sequence=sequence,
            requested_outputs=[dna_client.OutputType.DNASE],
            ontology_terms=[ontology_term]
        )
        
        # Extract prediction values (average over the sequence)
        dnase_values = output_dnase.dnase.values
        predictions['dnase_mean'] = float(np.mean(dnase_values))
        predictions['dnase_max'] = float(np.max(dnase_values))
        predictions['dnase_center'] = float(np.mean(dnase_values[900:1100]))  # Central region
        
        # Predict RNA-seq (gene expression proxy)
        output_rna = dna_model.predict_sequence(
            sequence=sequence,
            requested_outputs=[dna_client.OutputType.RNA_SEQ],
            ontology_terms=[ontology_term]
        )
        
        rna_values = output_rna.rna_seq.values
        predictions['rna_mean'] = float(np.mean(rna_values))
        predictions['rna_max'] = float(np.max(rna_values))
        predictions['rna_center'] = float(np.mean(rna_values[900:1100]))
        
        # Predict CAGE (transcription start sites)
        output_cage = dna_model.predict_sequence(
            sequence=sequence,
            requested_outputs=[dna_client.OutputType.CAGE],
            ontology_terms=[ontology_term]
        )
        
        cage_values = output_cage.cage.values
        predictions['cage_mean'] = float(np.mean(cage_values))
        predictions['cage_max'] = float(np.max(cage_values))
        predictions['cage_center'] = float(np.mean(cage_values[900:1100]))
        
        predictions['success'] = True
        predictions['error'] = None
        
    except Exception as e:
        print(f"  Error predicting {variant_id}: {e}")
        predictions['success'] = False
        predictions['error'] = str(e)
        # Fill with NaN
        for key in ['dnase_mean', 'dnase_max', 'dnase_center',
                    'rna_mean', 'rna_max', 'rna_center',
                    'cage_mean', 'cage_max', 'cage_center']:
            predictions[key] = np.nan
    
    return predictions

def save_checkpoint(results_df, checkpoint_num, start_time):
    """Save checkpoint to disk."""
    checkpoint_file = CHECKPOINT_DIR / f'checkpoint_{checkpoint_num:04d}.csv'
    results_df.to_csv(checkpoint_file, index=False)
    
    elapsed = time.time() - start_time
    state = {
        'checkpoint_num': checkpoint_num,
        'n_sequences': len(results_df),
        'timestamp': datetime.now().isoformat(),
        'elapsed_seconds': elapsed
    }
    state_file = CHECKPOINT_DIR / f'checkpoint_{checkpoint_num:04d}_state.json'
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    return checkpoint_file

def load_latest_checkpoint():
    """Load the latest checkpoint if it exists."""
    checkpoint_files = sorted(CHECKPOINT_DIR.glob('checkpoint_*.csv'))
    if not checkpoint_files:
        return None, 0
    
    latest_file = checkpoint_files[-1]
    checkpoint_num = int(latest_file.stem.split('_')[1])
    df = pd.read_csv(latest_file)
    
    print(f"✓ Loaded checkpoint {checkpoint_num} with {len(df)} predictions")
    return df, len(df)

def process_all_sequences(df, resume_from=0):
    """
    Process all sequences with checkpointing and progress tracking.
    VERSION 2: Handles 6,963 sequences with automatic checkpointing.
    """
    results = []
    start_time = time.time()
    total = len(df)
    
    print(f"\nProcessing {total:,} sequences...")
    print(f"Starting from sequence {resume_from}")
    print(f"Checkpointing every {CHECKPOINT_INTERVAL} sequences")
    print(f"Estimated time: ~{(total - resume_from) * 3.6:.1f} seconds ({(total - resume_from) * 3.6 / 3600:.1f} hours)")
    print("="*60)
    
    for idx in range(resume_from, total):
        row = df.iloc[idx]
        
        # Get sequence
        sequence = row['sequence_2kb']
        variant_id = row['variant_id']
        
        if pd.isna(sequence) or len(sequence) != 2048:
            print(f"  Skipping invalid sequence at index {idx}: {variant_id}")
            continue
        
        # Progress update every 50 sequences
        if idx % 50 == 0:
            elapsed = time.time() - start_time
            if idx > resume_from:
                rate = elapsed / (idx - resume_from)
                remaining = (total - idx) * rate
                eta_str = time.strftime("%H:%M:%S", time.gmtime(remaining))
                elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
                print(f"Progress: {idx:,}/{total:,} ({100*idx/total:.1f}%) | "
                      f"Elapsed: {elapsed_str} | ETA: {eta_str}")
        
        # Run predictions
        preds = predict_for_sequence(sequence, variant_id)
        
        # Combine with original data
        result = {
            'variant_id': variant_id,
            'variant_name': row['variant_name'],
            'chromosome': row['chromosome'],
            'start': row['start'],
            'end': row['end'],
            'strand': row['strand'],
            'variant_seq': row['variant_seq'],
            'tf_info': row['tf_info'],
            'sequence_2kb': sequence,
            'pool': row['pool'],
            'mpra_log2_ratio': row['log2_ratio'],
            'mpra_activity': row['activity'],
            'mpra_rna_count': row['rna_count'],
            'mpra_dna_count': row['dna_count'],
            **preds
        }
        
        results.append(result)
        
        # Checkpoint every N sequences
        if (idx + 1) % CHECKPOINT_INTERVAL == 0:
            checkpoint_num = (idx + 1) // CHECKPOINT_INTERVAL
            results_df = pd.DataFrame(results)
            checkpoint_file = save_checkpoint(results_df, checkpoint_num, start_time)
            print(f"✓ Checkpoint saved: {checkpoint_file.name} ({len(results_df):,} sequences)")
        
        # Brief pause to avoid rate limiting
        time.sleep(0.05)
    
    return pd.DataFrame(results)

def main():
    """Main execution function - VERSION 2."""
    print("="*60)
    print("AlphaGenome Prediction Pipeline - VERSION 2")
    print("="*60)
    print("\nVERSION 2 FEATURES:")
    print("  - Processes all 6,963 variants with 2048bp sequences")
    print("  - Automatic checkpointing every 100 sequences")
    print("  - Resume capability from last checkpoint")
    print("  - Progress tracking with ETA")
    print("="*60)
    
    # Check for existing checkpoint
    print("\nChecking for existing checkpoints...")
    existing_results, resume_from = load_latest_checkpoint()
    
    # Load prepared data
    print("\nLoading prepared MPRA data...")
    input_file = DATA_DIR / 'mpra_variants_with_2kb_sequences.csv'
    
    if not input_file.exists():
        print(f"Data file not found: {input_file}")
        print("Run 01_prepare_mpra_data.py first!")
        sys.exit(1)
    
    df = pd.read_csv(input_file)
    print(f"✓ Loaded {len(df):,} sequences from {input_file.name}")
    
    # Check if already complete
    if existing_results is not None and len(existing_results) >= len(df):
        print(f"\n✓ All {len(df):,} sequences already processed!")
        print(f"Using existing results from checkpoint")
        results_df = existing_results
    else:
        # Process sequences
        print("\n" + "="*60)
        print("Running AlphaGenome predictions...")
        print("="*60)
        
        start_time = time.time()
        results_df = process_all_sequences(df, resume_from=resume_from)
        elapsed = time.time() - start_time
        
        print(f"\n✓ Completed {len(results_df):,} predictions in {elapsed/3600:.2f} hours")
    
    # Save final results
    output_file = OUTPUT_DIR / 'alphagenome_predictions_all_variants.csv'
    results_df.to_csv(output_file, index=False)
    
    print("\n" + "="*60)
    print("Predictions complete!")
    print("="*60)
    print(f"✓ Saved {len(results_df):,} predictions to: {output_file}")
    
    # Summary statistics
    print("\n" + "="*60)
    print("Prediction Summary:")
    print("="*60)
    print(f"  Total sequences: {len(results_df):,}")
    print(f"  Successful: {results_df['success'].sum():,}")
    print(f"  Failed: {(~results_df['success']).sum():,}")
    print(f"  Success rate: {100 * results_df['success'].mean():.1f}%")
    
    print("\nMPRA Activity (log2 ratio):")
    print(f"  Min:  {results_df['mpra_log2_ratio'].min():.3f}")
    print(f"  Max:  {results_df['mpra_log2_ratio'].max():.3f}")
    print(f"  Mean: {results_df['mpra_log2_ratio'].mean():.3f}")
    print(f"  Std:  {results_df['mpra_log2_ratio'].std():.3f}")
    
    print("\nAlphaGenome DNase Predictions (center region):")
    successful = results_df[results_df['success']]
    print(f"  Min:  {successful['dnase_center'].min():.6f}")
    print(f"  Max:  {successful['dnase_center'].max():.6f}")
    print(f"  Mean: {successful['dnase_center'].mean():.6f}")
    print(f"  Std:  {successful['dnase_center'].std():.6f}")
    
    print("\nAlphaGenome RNA-seq Predictions (center region):")
    print(f"  Min:  {successful['rna_center'].min():.6f}")
    print(f"  Max:  {successful['rna_center'].max():.6f}")
    print(f"  Mean: {successful['rna_center'].mean():.6f}")
    print(f"  Std:  {successful['rna_center'].std():.6f}")
    
    print("\nAlphaGenome CAGE Predictions (center region):")
    print(f"  Min:  {successful['cage_center'].min():.6f}")
    print(f"  Max:  {successful['cage_center'].max():.6f}")
    print(f"  Mean: {successful['cage_center'].mean():.6f}")
    print(f"  Std:  {successful['cage_center'].std():.6f}")
    
    print("\nNext step: Run 03_benchmark_correlations.py")

if __name__ == '__main__':
    main()
