#!/usr/bin/env python3
"""
Step 2: Run AlphaGenome predictions on MPRA sequences
Author: Generated for Layer Lab Rotation
Date: October 30, 2025

This script:
1. Loads prepared MPRA sequences
2. Runs AlphaGenome predictions for each sequence
3. Collects multiple prediction metrics (DNase, CAGE, RNA-seq)
4. Saves predictions alongside MPRA measurements
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import time

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

# Load API key
env_path = Path('/mnt/work_1/gest9386/CU_Boulder/rotations/LAYER/Alpha_genome_quickstart_notebook/.env')
load_dotenv(env_path)
api_key = os.getenv('ALPHA_GENOME_API_KEY') or os.getenv('ALPHA_GENOME_API_KEY')

if not api_key:
    raise RuntimeError('Missing ALPHA_GENOME_API_KEY in environment. Check the .env file.')

print("Initializing AlphaGenome model...")
dna_model = dna_client.create(api_key)
print("✓ Model initialized")

def get_sequence_from_genome(chromosome, start, end, strand):
    """
    Fetch reference sequence from the genome.
    For this MPRA data, we'll use the embedded sequence in the name.
    """
    # Create interval
    interval = genome.Interval(chromosome, start, end)
    return interval

def pad_sequence_to_supported_length(sequence, target_length=2048):
    """
    Pad a short sequence to a supported AlphaGenome length.
    AlphaGenome supports: 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576
    """
    if len(sequence) >= target_length:
        # Truncate or use as-is if longer
        return sequence[:target_length]
    
    # Pad with N's symmetrically
    padding_needed = target_length - len(sequence)
    left_pad = padding_needed // 2
    right_pad = padding_needed - left_pad
    
    return 'N' * left_pad + sequence + 'N' * right_pad

def predict_for_sequence(sequence, cell_line='K562'):
    """
    Run AlphaGenome predictions for a single sequence.
    Returns a dictionary of prediction scores.
    """
    # Pad sequence to 2KB (smallest supported length)
    padded_seq = pad_sequence_to_supported_length(sequence, target_length=dna_client.SEQUENCE_LENGTH_2KB)
    
    # Choose ontology terms based on cell line
    # K562 is an erythroleukemia cell line
    ontology_term = 'EFO:0002067'  # K562 cell line
    
    predictions = {}
    
    try:
        # Predict DNase (chromatin accessibility)
        output_dnase = dna_model.predict_sequence(
            sequence=padded_seq,
            requested_outputs=[dna_client.OutputType.DNASE],
            ontology_terms=[ontology_term]
        )
        
        # Extract prediction values (average over the sequence)
        dnase_values = output_dnase.dnase.values
        predictions['dnase_mean'] = np.mean(dnase_values)
        predictions['dnase_max'] = np.max(dnase_values)
        predictions['dnase_center'] = np.mean(dnase_values[900:1100])  # Central region
        
        # Predict RNA-seq (gene expression proxy)
        output_rna = dna_model.predict_sequence(
            sequence=padded_seq,
            requested_outputs=[dna_client.OutputType.RNA_SEQ],
            ontology_terms=[ontology_term]
        )
        
        rna_values = output_rna.rna_seq.values
        predictions['rna_mean'] = np.mean(rna_values)
        predictions['rna_max'] = np.max(rna_values)
        predictions['rna_center'] = np.mean(rna_values[900:1100])
        
        # Predict CAGE (transcription start sites)
        output_cage = dna_model.predict_sequence(
            sequence=padded_seq,
            requested_outputs=[dna_client.OutputType.CAGE],
            ontology_terms=[ontology_term]
        )
        
        cage_values = output_cage.cage.values
        predictions['cage_mean'] = np.mean(cage_values)
        predictions['cage_max'] = np.max(cage_values)
        predictions['cage_center'] = np.mean(cage_values[900:1100])
        
        predictions['success'] = True
        predictions['error'] = None
        
    except Exception as e:
        print(f"Error predicting sequence: {e}")
        predictions['success'] = False
        predictions['error'] = str(e)
        # Fill with NaN
        for key in ['dnase_mean', 'dnase_max', 'dnase_center',
                    'rna_mean', 'rna_max', 'rna_center',
                    'cage_mean', 'cage_max', 'cage_center']:
            predictions[key] = np.nan
    
    return predictions

def process_batch(df, batch_size=50, max_sequences=None):
    """
    Process a batch of sequences and return predictions.
    """
    if max_sequences:
        df = df.head(max_sequences)
    
    results = []
    
    print(f"\nProcessing {len(df)} sequences...")
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Running predictions"):
        # Get sequence
        sequence = row['embedded_seq']
        
        if pd.isna(sequence) or len(sequence) < 10:
            print(f"Skipping invalid sequence at index {idx}")
            continue
        
        # Run predictions
        preds = predict_for_sequence(sequence)
        
        # Combine with original data
        result = {
            'seq_id': row['seq_id'],
            'chromosome': row['chromosome'],
            'start': row['start'],
            'end': row['end'],
            'strand': row['strand'],
            'sequence': sequence,
            'sequence_length': len(sequence),
            'pool': row['pool'],
            'mpra_log2_ratio': row['log2_ratio_mean'],
            'mpra_activity': row['activity_mean'],
            'mpra_rna_count': row['rna_count_sum'],
            'mpra_dna_count': row['dna_count_sum'],
            'n_variants': row['log2_ratio_count'],
            **preds
        }
        
        results.append(result)
        
        # Brief pause to avoid rate limiting
        time.sleep(0.1)
    
    return pd.DataFrame(results)

def main():
    """Main execution function."""
    print("="*60)
    print("AlphaGenome Prediction Pipeline for MPRA Data")
    print("="*60)
    
    # Load prepared data
    print("\nLoading prepared MPRA data...")
    
    # Start with sample for testing
    input_file = DATA_DIR / 'mpra_sample_100.csv'
    
    if not input_file.exists():
        print(f"Sample file not found: {input_file}")
        print("Run 01_prepare_mpra_data.py first!")
        sys.exit(1)
    
    df = pd.read_csv(input_file)
    print(f"✓ Loaded {len(df)} sequences from {input_file.name}")
    
    # Process sequences
    print("\n" + "="*60)
    print("Running AlphaGenome predictions...")
    print("="*60)
    print("Note: This may take several minutes...")
    
    results_df = process_batch(df, max_sequences=100)
    
    # Save results
    output_file = OUTPUT_DIR / 'alphagenome_predictions_sample100.csv'
    results_df.to_csv(output_file, index=False)
    
    print("\n" + "="*60)
    print("Predictions complete!")
    print("="*60)
    print(f"✓ Saved {len(results_df)} predictions to: {output_file}")
    
    # Quick summary
    print("\nPrediction Summary:")
    print(f"  Successful: {results_df['success'].sum()}")
    print(f"  Failed: {(~results_df['success']).sum()}")
    
    print("\nMPRA Activity Range:")
    print(f"  Min: {results_df['mpra_log2_ratio'].min():.3f}")
    print(f"  Max: {results_df['mpra_log2_ratio'].max():.3f}")
    print(f"  Mean: {results_df['mpra_log2_ratio'].mean():.3f}")
    
    print("\nAlphaGenome DNase Predictions:")
    print(f"  Min: {results_df['dnase_center'].min():.6f}")
    print(f"  Max: {results_df['dnase_center'].max():.6f}")
    print(f"  Mean: {results_df['dnase_center'].mean():.6f}")
    
    print("\nNext step: Run 03_benchmark_correlations.py")

if __name__ == '__main__':
    main()
