#!/usr/bin/env python3
"""
Step 1: Prepare MPRA data for AlphaGenome benchmarking - VERSION 2
Author: Generated for Layer Lab Rotation
Date: October 30, 2025

VERSION 2 ENHANCEMENTS:
- Uses mm9 reference genome to extract full 2KB genomic context
- Processes all 6,963 individual variants (not aggregated)
- Handles strand orientation correctly (reverse complement for minus strand)
- Creates biologically realistic sequences with natural flanking regions

This script:
1. Loads synthetic enhancer sequences from Pool6 and Pool7
2. Loads corresponding MPRA reporter counts
3. Extracts variant sequences from names
4. Retrieves 2KB genomic context from mm9 reference
5. Inserts variant sequence into genomic context
6. Handles strand orientation (reverse complement)
7. Computes MPRA activity (RNA/DNA ratio)
8. Saves prepared data for AlphaGenome inference
"""

import os
import re
import pandas as pd
import numpy as np
from pathlib import Path
from pyfaidx import Fasta
from collections import defaultdict

# Set paths
BASE_DIR = Path('/mnt/work_1/gest9386/CU_Boulder/rotations/LAYER/GSE84888_MPRA')
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'outputs' / '01_prepared_data'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Genome reference
GENOME_FILE = DATA_DIR / 'mm9_ref' / 'mm9_genome.fna'

# Chromosome name mapping (UCSC to NCBI RefSeq)
CHR_MAP = {
    'chr1': 'NC_000067.5',
    'chr2': 'NC_000068.6',
    'chr3': 'NC_000069.5',
    'chr4': 'NC_000070.5',
    'chr5': 'NC_000071.5',
    'chr6': 'NC_000072.5',
    'chr7': 'NC_000073.5',
    'chr8': 'NC_000074.5',
    'chr9': 'NC_000075.5',
    'chr10': 'NC_000076.5',
    'chr11': 'NC_000077.5',
    'chr12': 'NC_000078.5',
    'chr13': 'NC_000079.5',
    'chr14': 'NC_000080.5',
    'chr15': 'NC_000081.5',
    'chr16': 'NC_000082.5',
    'chr17': 'NC_000083.5',
    'chr18': 'NC_000084.5',
    'chr19': 'NC_000085.5',
    'chrX': 'NC_000086.6',
    'chrY': 'NC_000087.6'
}

def reverse_complement(seq):
    """Return reverse complement of DNA sequence."""
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'N': 'N'}
    return ''.join(complement.get(base, 'N') for base in reversed(seq.upper()))

def parse_sequence_name(name):
    """
    Extract genomic coordinates and sequence from the sequence name.
    Format: PPREwt_{id}_chr{chr}_{start}_{end}_{strand}_{sequence}_{modifications}
    """
    parts = name.split('_')
    
    # Extract chromosome, start, end, strand, and embedded sequence
    chr_idx = next(i for i, p in enumerate(parts) if p.startswith('chr'))
    
    result = {
        'variant_name': name,
        'sequence_id': '_'.join(parts[:chr_idx]),
        'chromosome': parts[chr_idx],
        'start': int(parts[chr_idx + 1]),
        'end': int(parts[chr_idx + 2]),
        'strand': parts[chr_idx + 3],
        'variant_seq': parts[chr_idx + 4] if chr_idx + 4 < len(parts) else None,
        'tf_info': '_'.join(parts[chr_idx + 5:]) if chr_idx + 5 < len(parts) else 'wt'
    }
    
    return result

def extract_2kb_sequence(genome, chromosome, start, end, strand, variant_seq):
    """
    Extract 2048bp genomic sequence centered on variant with real flanking regions.
    AlphaGenome requires 2048bp (2KB), not 2000bp.
    
    Args:
        genome: pyfaidx Fasta object
        chromosome: UCSC format (chr1, chr2, etc.)
        start, end: 0-based coordinates of variant region
        strand: '+' or '-'
        variant_seq: The variant sequence to insert
    
    Returns:
        2048bp sequence with variant inserted in center
    """
    # Convert UCSC to NCBI chromosome name
    if chromosome not in CHR_MAP:
        print(f"Warning: Unknown chromosome {chromosome}, skipping")
        return None
    
    ncbi_chr = CHR_MAP[chromosome]
    
    try:
        # Calculate center and extract 2048bp window
        variant_len = len(variant_seq)
        center = (start + end) // 2
        
        # Define 2048bp window centered on variant (1024bp on each side)
        window_start = center - 1024
        window_end = center + 1024
        
        # Ensure we don't go negative
        if window_start < 0:
            window_start = 0
            window_end = 2048
        
        # Extract full 2048bp from genome (using 0-based coordinates)
        full_seq = str(genome[ncbi_chr][window_start:window_end])
        
        # Calculate where to insert the variant in the 2048bp window
        variant_offset_in_window = center - window_start
        variant_start_in_window = variant_offset_in_window - variant_len // 2
        variant_end_in_window = variant_start_in_window + variant_len
        
        # Replace the center region with variant sequence
        seq_with_variant = (
            full_seq[:variant_start_in_window] + 
            variant_seq + 
            full_seq[variant_end_in_window:]
        )
        
        # Pad or truncate to exactly 2048bp
        if len(seq_with_variant) < 2048:
            seq_with_variant = seq_with_variant + 'N' * (2048 - len(seq_with_variant))
        elif len(seq_with_variant) > 2048:
            seq_with_variant = seq_with_variant[:2048]
        
        # Handle strand orientation
        if strand == '-':
            seq_with_variant = reverse_complement(seq_with_variant)
        
        return seq_with_variant.upper()
        
    except Exception as e:
        print(f"Error extracting sequence for {chromosome}:{start}-{end}: {e}")
        return None

def load_and_process_pool(pool_name, genome):
    """
    Load and process MPRA data for a pool with full genome context.
    VERSION 2: Processes all individual variants (no aggregation).
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
    
    # Load MPRA counts
    print(f"Loading MPRA counts from {mpra_file.name}...")
    mpra = pd.read_csv(mpra_file, sep='\t')
    print(f"  - Loaded {len(mpra):,} MPRA entries")
    
    # Parse sequence information from variant names
    print("\nParsing variant names...")
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
    
    # Extract 2KB genomic sequences for each variant
    print("\nExtracting 2KB genomic sequences from mm9 genome...")
    print("This may take a few minutes...")
    
    sequences_2kb = []
    failed_count = 0
    
    for idx, row in mpra.iterrows():
        if idx % 500 == 0:
            print(f"  Progress: {idx:,} / {len(mpra):,} variants processed...")
        
        seq_2kb = extract_2kb_sequence(
            genome,
            row['chromosome'],
            row['start'],
            row['end'],
            row['strand'],
            row['variant_seq']
        )
        
        if seq_2kb is None:
            failed_count += 1
        
        sequences_2kb.append(seq_2kb)
    
    mpra['sequence_2kb'] = sequences_2kb
    
    # Remove failed extractions
    if failed_count > 0:
        print(f"\n  Warning: {failed_count} sequences failed extraction")
        mpra = mpra[mpra['sequence_2kb'].notna()].reset_index(drop=True)
    
    print(f"\n  Successfully extracted {len(mpra):,} 2KB sequences")
    
    # Add pool identifier
    mpra['pool'] = pool_name
    
    # Create a unique identifier for each variant
    mpra['variant_id'] = (
        mpra['chromosome'] + ':' + 
        mpra['start'].astype(str) + '-' + 
        mpra['end'].astype(str) + ':' +
        mpra['strand'] + ':' +
        mpra['variant_seq']
    )
    
    return mpra

def main():
    """Main execution function - VERSION 2."""
    print("="*60)
    print("MPRA Data Preparation for AlphaGenome Benchmarking - V2")
    print("="*60)
    print("\nVERSION 2 FEATURES:")
    print("  - Uses mm9 reference genome for 2048bp context")
    print("  - Processes all 6,963 individual variants")
    print("  - Handles strand orientation (reverse complement)")
    print("  - Creates biologically realistic sequences")
    print("  - AlphaGenome-compatible 2048bp length")
    print("="*60)
    
    # Load genome
    print(f"\nLoading mm9 reference genome from {GENOME_FILE}...")
    genome = Fasta(str(GENOME_FILE))
    print(f"✓ Loaded genome with {len(genome.keys())} sequences")
    
    # Process both pools
    pool6_data = load_and_process_pool('Pool6', genome)
    pool7_data = load_and_process_pool('Pool7', genome)
    
    # Combine pools
    print("\n" + "="*60)
    print("Combining pools...")
    print("="*60)
    combined_data = pd.concat([pool6_data, pool7_data], ignore_index=True)
    
    print(f"\nTotal variants processed: {len(combined_data):,}")
    
    # Summary statistics
    print("\n" + "="*60)
    print("Summary Statistics:")
    print("="*60)
    print(f"\nLog2(RNA/DNA) ratio statistics:")
    print(combined_data['log2_ratio'].describe())
    
    print(f"\nActivity statistics:")
    print(combined_data['activity'].describe())
    
    print(f"\nSequence length distribution:")
    seq_lengths = combined_data['sequence_2kb'].apply(len)
    print(seq_lengths.describe())
    print(f"  All sequences should be 2048bp for AlphaGenome compatibility")
    
    print(f"\nStrand distribution:")
    print(combined_data['strand'].value_counts())
    
    print(f"\nChromosome distribution:")
    print(combined_data['chromosome'].value_counts().sort_index())
    
    # Save outputs
    print("\n" + "="*60)
    print("Saving prepared data...")
    print("="*60)
    
    # Select columns to save
    output_cols = [
        'variant_id', 'variant_name', 'sequence_2kb', 'variant_seq',
        'chromosome', 'start', 'end', 'strand', 'tf_info',
        'log2_ratio', 'activity', 'rna_count', 'dna_count', 'pool'
    ]
    
    # Save full dataset (all 6,963 variants with 2KB sequences)
    full_file = OUTPUT_DIR / 'mpra_variants_with_2kb_sequences.csv'
    combined_data[output_cols].to_csv(full_file, index=False)
    print(f"✓ Saved full variant dataset: {full_file}")
    print(f"  {len(combined_data):,} variants with 2KB genomic sequences")
    
    # Create a smaller test subset (100 variants)
    sample_size = 100
    sample = combined_data.sample(n=min(sample_size, len(combined_data)), random_state=42)
    sample_file = OUTPUT_DIR / f'mpra_test_sample_{sample_size}.csv'
    sample[output_cols].to_csv(sample_file, index=False)
    print(f"✓ Saved test sample: {sample_file}")
    print(f"  {len(sample):,} variants (for quick testing)")
    
    # Save metadata summary
    metadata = {
        'version': 2,
        'genome_reference': 'mm9',
        'total_variants': len(combined_data),
        'pool6_variants': len(pool6_data),
        'pool7_variants': len(pool7_data),
        'sequence_length': 2048,
        'strand_aware': True,
        'log2_ratio_mean': float(combined_data['log2_ratio'].mean()),
        'log2_ratio_std': float(combined_data['log2_ratio'].std())
    }
    
    import json
    metadata_file = OUTPUT_DIR / 'dataset_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Saved metadata: {metadata_file}")
    
    print("\n" + "="*60)
    print("Data preparation complete!")
    print("="*60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"\nKey improvements in Version 2:")
    print(f"  ✓ Real genomic context (2048bp from mm9)")
    print(f"  ✓ All {len(combined_data):,} variants (not aggregated)")
    print(f"  ✓ Strand-aware sequence extraction")
    print(f"  ✓ Biologically realistic flanking regions")
    print(f"  ✓ AlphaGenome-compatible sequence length (2048bp)")
    print("\nNext step: Run 02_run_alphagenome_predictions.py")

if __name__ == '__main__':
    main()
