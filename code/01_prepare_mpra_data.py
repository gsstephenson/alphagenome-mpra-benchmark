#!/usr/bin/env python3
"""
Step 1: Prepare MPRA data for AlphaGenome benchmarking
Author: Generated for Layer Lab Rotation
Date: October 30, 2025

This script:
1. Loads synthetic enhancer sequences from Pool6 and Pool7
2. Loads corresponding MPRA reporter counts
3. Merges sequences with expression data
4. Extracts the actual DNA sequences from the names
5. Computes MPRA activity (RNA/DNA ratio)
6. Saves prepared data for AlphaGenome inference
"""

import os
import re
import pandas as pd
import numpy as np
from pathlib import Path

# Set paths
BASE_DIR = Path('/mnt/work_1/gest9386/CU_Boulder/rotations/LAYER/GSE84888_MPRA')
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'outputs' / '01_prepared_data'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def parse_sequence_name(name):
    """
    Extract genomic coordinates and sequence from the sequence name.
    Format: PPREwt_{id}_chr{chr}_{start}_{end}_{strand}_{sequence}_{modifications}
    """
    parts = name.split('_')
    
    # Extract chromosome, start, end, strand, and embedded sequence
    chr_idx = next(i for i, p in enumerate(parts) if p.startswith('chr'))
    
    result = {
        'sequence_id': '_'.join(parts[:chr_idx]),
        'chromosome': parts[chr_idx],
        'start': int(parts[chr_idx + 1]),
        'end': int(parts[chr_idx + 2]),
        'strand': parts[chr_idx + 3],
        'embedded_seq': parts[chr_idx + 4] if chr_idx + 4 < len(parts) else None,
        'modification': '_'.join(parts[chr_idx + 5:]) if chr_idx + 5 < len(parts) else 'wt'
    }
    
    return result

def load_and_merge_pool(pool_name):
    """
    Load barcode sequences and MPRA counts for a given pool, then merge.
    """
    print(f"\n{'='*60}")
    print(f"Processing {pool_name}")
    print(f"{'='*60}")
    
    # Determine file paths
    if pool_name == 'Pool6':
        barcode_file = DATA_DIR / 'Synthetic_enhancer_seq' / 'GSM2253166_Pool6.barcodes.txt'
        mpra_file = DATA_DIR / 'MPRA_reporter_counts' / 'GSE84888_Pool6_MPRA.txt'
    else:
        barcode_file = DATA_DIR / 'Synthetic_enhancer_seq' / 'GSM2253167_Pool7.barcodes.txt'
        mpra_file = DATA_DIR / 'MPRA_reporter_counts' / 'GSE84888_Pool7_MPRA.txt'
    
    # Load barcode data
    print(f"Loading barcodes from {barcode_file.name}...")
    barcodes = pd.read_csv(barcode_file, sep='\t')
    print(f"  - Loaded {len(barcodes):,} barcode entries")
    print(f"  - Columns: {list(barcodes.columns)}")
    
    # Load MPRA counts
    print(f"\nLoading MPRA counts from {mpra_file.name}...")
    mpra = pd.read_csv(mpra_file, sep='\t')
    print(f"  - Loaded {len(mpra):,} MPRA entries")
    print(f"  - Columns: {list(mpra.columns)}")
    
    # Parse sequence information
    print("\nParsing sequence names...")
    seq_info = mpra['name'].apply(parse_sequence_name)
    seq_df = pd.DataFrame(seq_info.tolist())
    mpra = pd.concat([mpra, seq_df], axis=1)
    
    # Compute MPRA activity (log2 RNA/DNA ratio)
    print("\nComputing MPRA activity metrics...")
    mpra['rna_count'] = mpra['counts.rna']
    mpra['dna_count'] = mpra['counts.plasmid']
    
    # Add pseudocount to avoid log(0)
    pseudocount = 1
    mpra['log2_ratio'] = np.log2((mpra['rna_count'] + pseudocount) / (mpra['dna_count'] + pseudocount))
    mpra['activity'] = mpra['rna_count'] / (mpra['dna_count'] + pseudocount)
    
    # Get unique sequences (many variants per sequence)
    print("\nAggregating by base sequence...")
    
    # Group by the base genomic location to get unique sequences
    grouped = mpra.groupby(['chromosome', 'start', 'end', 'strand', 'embedded_seq']).agg({
        'log2_ratio': ['mean', 'std', 'count'],
        'activity': ['mean', 'std'],
        'rna_count': 'sum',
        'dna_count': 'sum'
    }).reset_index()
    
    # Flatten column names
    grouped.columns = ['_'.join(col).strip('_') for col in grouped.columns.values]
    
    print(f"  - Reduced to {len(grouped):,} unique sequences")
    
    # Add pool identifier
    grouped['pool'] = pool_name
    
    # Create a sequence ID for joining
    grouped['seq_id'] = (grouped['chromosome'] + ':' + 
                         grouped['start'].astype(str) + '-' + 
                         grouped['end'].astype(str) + 
                         grouped['strand'])
    
    return grouped, mpra

def main():
    """Main execution function."""
    print("="*60)
    print("MPRA Data Preparation for AlphaGenome Benchmarking")
    print("="*60)
    
    # Process both pools
    pool6_summary, pool6_full = load_and_merge_pool('Pool6')
    pool7_summary, pool7_full = load_and_merge_pool('Pool7')
    
    # Combine pools
    print("\n" + "="*60)
    print("Combining pools...")
    print("="*60)
    combined_summary = pd.concat([pool6_summary, pool7_summary], ignore_index=True)
    combined_full = pd.concat([pool6_full, pool7_full], ignore_index=True)
    
    print(f"\nTotal unique sequences: {len(combined_summary):,}")
    print(f"Total individual measurements: {len(combined_full):,}")
    
    # Summary statistics
    print("\n" + "="*60)
    print("Summary Statistics:")
    print("="*60)
    print(f"\nLog2(RNA/DNA) ratio statistics:")
    print(combined_summary['log2_ratio_mean'].describe())
    
    print(f"\nVariants per sequence:")
    print(combined_summary['log2_ratio_count'].describe())
    
    # Save outputs
    print("\n" + "="*60)
    print("Saving prepared data...")
    print("="*60)
    
    # Save summary (one row per unique sequence)
    summary_file = OUTPUT_DIR / 'mpra_sequences_summary.csv'
    combined_summary.to_csv(summary_file, index=False)
    print(f"✓ Saved sequence summary: {summary_file}")
    print(f"  {len(combined_summary):,} unique sequences")
    
    # Save full data (all variants)
    full_file = OUTPUT_DIR / 'mpra_all_variants.csv'
    combined_full.to_csv(full_file, index=False)
    print(f"✓ Saved full variant data: {full_file}")
    print(f"  {len(combined_full):,} total measurements")
    
    # Save Pool6 only (for initial testing with smaller dataset)
    pool6_file = OUTPUT_DIR / 'mpra_pool6_only.csv'
    pool6_summary.to_csv(pool6_file, index=False)
    print(f"✓ Saved Pool6 data: {pool6_file}")
    print(f"  {len(pool6_summary):,} sequences")
    
    # Create a sample subset for quick testing
    sample_size = 100
    sample = combined_summary.sample(n=min(sample_size, len(combined_summary)), random_state=42)
    sample_file = OUTPUT_DIR / f'mpra_sample_{sample_size}.csv'
    sample.to_csv(sample_file, index=False)
    print(f"✓ Saved sample data: {sample_file}")
    print(f"  {len(sample):,} sequences (for quick testing)")
    
    print("\n" + "="*60)
    print("Data preparation complete!")
    print("="*60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nNext step: Run 02_run_alphagenome_predictions.py")

if __name__ == '__main__':
    main()
