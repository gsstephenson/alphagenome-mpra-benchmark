#!/usr/bin/env python3
"""
Step 5: Wild-Type Validation Analysis
Author: Generated for Layer Lab Rotation
Date: October 31, 2025

PURPOSE:
This script validates AlphaGenome's performance on natural (wild-type) sequences
by comparing predictions on reconstructed WT sequences vs synthetic mutant variants.

HYPOTHESIS:
AlphaGenome should perform better on natural sequences (r > 0.3) compared to
synthetic mutants (r = 0.05), validating that the weak correlation is due to
the artificial nature of MPRA variants, not model failure.

METHODOLOGY:
1. Extract true reference sequences from mm9 genome at variant locations
2. Reconstruct wild-type 2048bp sequences (replacing variant_seq with reference)
3. Run AlphaGenome predictions on reconstructed WT sequences (~6,863 predictions)
4. Compare WT predictions vs mutant predictions
5. Correlate both with MPRA activity
6. Quantify mutation effect sizes (mutant - WT predictions)

EXPECTED OUTCOMES:
- WT sequences show stronger correlation with MPRA (r > 0.3)
- WT predictions are more consistent (lower variance)
- Mutation effects are quantifiable and directional
- Validates model works on natural genomic sequences
"""

import os
import sys
import time
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from pyfaidx import Fasta
from scipy import stats
from tqdm import tqdm
from datetime import datetime

# AlphaGenome imports
from dotenv import load_dotenv
from alphagenome.models import dna_client

# Suppress warnings
warnings.filterwarnings('ignore')

# Set paths
BASE_DIR = Path('/mnt/work_1/gest9386/CU_Boulder/rotations/LAYER/GSE84888_MPRA')
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'outputs' / '05_wildtype_validation'
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

# Load API key
env_path = Path('/mnt/work_1/gest9386/CU_Boulder/rotations/LAYER/Alpha_genome_quickstart_notebook/.env')
load_dotenv(env_path)
api_key = os.getenv('ALPHA_GENOME_API_KEY') or os.getenv('ALPHA_GENOME_KEY')

if not api_key:
    raise RuntimeError('Missing ALPHA_GENOME_API_KEY in environment.')

# Checkpointing
CHECKPOINT_DIR = OUTPUT_DIR / 'checkpoints'
CHECKPOINT_DIR.mkdir(exist_ok=True)
CHECKPOINT_INTERVAL = 100

print("="*80)
print("WILD-TYPE VALIDATION ANALYSIS")
print("="*80)
print(f"\nOutput directory: {OUTPUT_DIR}")
print(f"Checkpoint directory: {CHECKPOINT_DIR}")


def reverse_complement(seq):
    """Return reverse complement of DNA sequence."""
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'N': 'N'}
    return ''.join(complement.get(base.upper(), 'N') for base in reversed(seq))


def extract_reference_sequence(genome, chromosome, start, end, strand):
    """
    Extract the true reference sequence from mm9 genome.
    
    Args:
        genome: pyfaidx Fasta object
        chromosome: Chromosome name (e.g., 'chr3')
        start: 0-based start position
        end: 0-based end position (exclusive)
        strand: '+' or '-'
    
    Returns:
        Reference sequence string (16bp for this dataset)
    """
    try:
        # Convert UCSC chromosome name to RefSeq ID
        refseq_chr = CHR_MAP.get(chromosome, chromosome)
        ref_seq = genome[refseq_chr][start:end].seq.upper()
        if strand == '-':
            ref_seq = reverse_complement(ref_seq)
        return ref_seq
    except Exception as e:
        print(f"Error extracting reference for {chromosome}:{start}-{end}:{strand}: {e}")
        return None


def reconstruct_wildtype_sequence(genome, row):
    """
    Reconstruct wild-type 2048bp sequence by replacing variant_seq with reference.
    
    Args:
        genome: pyfaidx Fasta object
        row: DataFrame row with variant information
    
    Returns:
        Reconstructed WT sequence (2048bp)
    """
    # Extract reference sequence at variant position
    ref_seq = extract_reference_sequence(
        genome, 
        row['chromosome'], 
        row['start'], 
        row['end'], 
        row['strand']
    )
    
    if ref_seq is None:
        return None
    
    # The sequence_2kb contains the variant_seq embedded in the center
    # We need to replace the variant with the reference
    sequence_2kb = row['sequence_2kb']
    variant_seq = row['variant_seq']
    
    # CRITICAL FIX: For minus strand, the sequence_2kb is reverse complemented,
    # so we need to search for the reverse complement of variant_seq
    if row['strand'] == '-':
        variant_seq_to_find = reverse_complement(variant_seq)
    else:
        variant_seq_to_find = variant_seq
    
    # Find and replace variant_seq with ref_seq
    if variant_seq_to_find in sequence_2kb:
        wt_sequence = sequence_2kb.replace(variant_seq_to_find, ref_seq, 1)
        return wt_sequence
    else:
        # Debug: try both orientations to confirm issue
        if variant_seq in sequence_2kb:
            print(f"Warning: Found forward strand variant_seq in minus strand sequence for {row['variant_id']}")
            wt_sequence = sequence_2kb.replace(variant_seq, ref_seq, 1)
            return wt_sequence
        else:
            print(f"Warning: variant_seq not found in sequence_2kb for {row['variant_id']}")
            return None


def predict_sequence(dna_model, sequence, variant_id):
    """
    Run AlphaGenome prediction on a single sequence.
    Uses the same method as 02_run_alphagenome_predictions.py for consistency.
    
    Returns:
        Dictionary with prediction metrics
    """
    ontology_term = 'EFO:0002067'  # K562
    
    predictions = {'variant_id': variant_id}
    
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
        
        # Extract prediction values
        dnase_values = output_dnase.dnase.values
        predictions['wt_dnase_mean'] = float(np.mean(dnase_values))
        predictions['wt_dnase_max'] = float(np.max(dnase_values))
        predictions['wt_dnase_center'] = float(np.mean(dnase_values[900:1100]))  # Central 200bp
        
        # Predict RNA-seq (gene expression proxy)
        output_rna = dna_model.predict_sequence(
            sequence=sequence,
            requested_outputs=[dna_client.OutputType.RNA_SEQ],
            ontology_terms=[ontology_term]
        )
        
        rna_values = output_rna.rna_seq.values
        predictions['wt_rna_mean'] = float(np.mean(rna_values))
        predictions['wt_rna_max'] = float(np.max(rna_values))
        predictions['wt_rna_center'] = float(np.mean(rna_values[900:1100]))
        
        # Predict CAGE (transcription start sites)
        output_cage = dna_model.predict_sequence(
            sequence=sequence,
            requested_outputs=[dna_client.OutputType.CAGE],
            ontology_terms=[ontology_term]
        )
        
        cage_values = output_cage.cage.values
        predictions['wt_cage_mean'] = float(np.mean(cage_values))
        predictions['wt_cage_max'] = float(np.max(cage_values))
        predictions['wt_cage_center'] = float(np.mean(cage_values[900:1100]))
        
        predictions['success'] = True
        
    except Exception as e:
        print(f"Prediction failed for {variant_id}: {e}")
        predictions['success'] = False
        for key in ['wt_dnase_center', 'wt_rna_center', 'wt_cage_center',
                    'wt_dnase_mean', 'wt_rna_mean', 'wt_cage_mean',
                    'wt_dnase_max', 'wt_rna_max', 'wt_cage_max']:
            predictions[key] = np.nan
    
    return predictions


def save_checkpoint(results_df, checkpoint_num):
    """Save checkpoint to disk."""
    checkpoint_file = CHECKPOINT_DIR / f'wt_checkpoint_{checkpoint_num:04d}.csv'
    results_df.to_csv(checkpoint_file, index=False)
    return checkpoint_file


def load_latest_checkpoint():
    """Load the latest checkpoint if it exists."""
    checkpoint_files = sorted(CHECKPOINT_DIR.glob('wt_checkpoint_*.csv'))
    if checkpoint_files:
        latest = checkpoint_files[-1]
        print(f"Found checkpoint: {latest.name}")
        df = pd.read_csv(latest)
        checkpoint_num = int(latest.stem.split('_')[-1])
        return df, checkpoint_num
    return None, 0


def main():
    """Main execution function."""
    
    # Step 1: Load mutant predictions
    print("\n" + "="*80)
    print("STEP 1: Load Mutant Variant Data")
    print("="*80)
    
    mutant_file = BASE_DIR / 'outputs' / '02_alphagenome_predictions' / 'alphagenome_predictions_all_variants.csv'
    if not mutant_file.exists():
        print(f"ERROR: Mutant predictions file not found: {mutant_file}")
        return
    
    df = pd.read_csv(mutant_file)
    print(f"✓ Loaded {len(df):,} mutant variant predictions")
    print(f"  - Success rate: {df['success'].mean()*100:.1f}%")
    
    # Step 2: Load genome reference
    print("\n" + "="*80)
    print("STEP 2: Load MM9 Genome Reference")
    print("="*80)
    
    if not GENOME_FILE.exists():
        print(f"ERROR: Genome file not found: {GENOME_FILE}")
        return
    
    print(f"Loading genome from: {GENOME_FILE}")
    genome_ref = Fasta(str(GENOME_FILE))
    print(f"✓ Genome loaded with {len(genome_ref.keys())} chromosomes")
    
    # Step 3: Reconstruct wild-type sequences
    print("\n" + "="*80)
    print("STEP 3: Reconstruct Wild-Type Sequences")
    print("="*80)
    
    print("Extracting true reference sequences from mm9...")
    wt_sequences = []
    failed = 0
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Reconstructing WT sequences"):
        wt_seq = reconstruct_wildtype_sequence(genome_ref, row)
        if wt_seq is not None:
            wt_sequences.append({
                'variant_id': row['variant_id'],
                'wt_sequence_2kb': wt_seq,
                'chromosome': row['chromosome'],
                'start': row['start'],
                'end': row['end'],
                'strand': row['strand']
            })
        else:
            failed += 1
    
    wt_df = pd.DataFrame(wt_sequences)
    print(f"\n✓ Reconstructed {len(wt_df):,} wild-type sequences")
    if failed > 0:
        print(f"⚠ Failed to reconstruct {failed} sequences")
    
    # Save reconstructed sequences
    wt_seq_file = OUTPUT_DIR / 'wildtype_sequences_reconstructed.csv'
    wt_df.to_csv(wt_seq_file, index=False)
    print(f"✓ Saved to: {wt_seq_file}")
    
    # Step 4: Check for existing checkpoint
    print("\n" + "="*80)
    print("STEP 4: Run AlphaGenome Predictions on Wild-Type Sequences")
    print("="*80)
    
    existing_results, last_checkpoint = load_latest_checkpoint()
    
    if existing_results is not None:
        print(f"Resuming from checkpoint {last_checkpoint} ({len(existing_results):,} sequences completed)")
        resume_from = len(existing_results)
    else:
        print("Starting fresh predictions")
        resume_from = 0
        existing_results = pd.DataFrame()
    
    # Initialize AlphaGenome model
    print("\nInitializing AlphaGenome model...")
    dna_model = dna_client.create(api_key)
    print("✓ Model initialized")
    
    # Run predictions
    print(f"\nRunning predictions for {len(wt_df) - resume_from:,} wild-type sequences...")
    print(f"Estimated time: ~{(len(wt_df) - resume_from) * 0.29 / 60:.1f} minutes")
    
    all_predictions = []
    if len(existing_results) > 0:
        all_predictions.extend(existing_results.to_dict('records'))
    
    start_time = time.time()
    
    for idx in tqdm(range(resume_from, len(wt_df)), desc="Predicting WT sequences"):
        row = wt_df.iloc[idx]
        
        predictions = predict_sequence(
            dna_model,
            row['wt_sequence_2kb'],
            row['variant_id']
        )
        
        all_predictions.append(predictions)
        
        # Checkpoint every N sequences
        if (idx + 1) % CHECKPOINT_INTERVAL == 0:
            checkpoint_df = pd.DataFrame(all_predictions)
            checkpoint_num = (idx + 1) // CHECKPOINT_INTERVAL
            save_checkpoint(checkpoint_df, checkpoint_num)
            
            elapsed = time.time() - start_time
            rate = (idx + 1 - resume_from) / elapsed
            remaining = (len(wt_df) - idx - 1) / rate
            print(f"\n  Checkpoint {checkpoint_num}: {idx+1}/{len(wt_df)} sequences")
            print(f"  Rate: {rate:.2f} seq/sec | ETA: {remaining/60:.1f} min")
    
    # Final results
    wt_predictions_df = pd.DataFrame(all_predictions)
    
    elapsed_total = time.time() - start_time
    print(f"\n✓ Completed {len(wt_predictions_df):,} predictions in {elapsed_total/60:.1f} minutes")
    print(f"  Success rate: {wt_predictions_df['success'].mean()*100:.1f}%")
    
    # Save final predictions
    wt_pred_file = OUTPUT_DIR / 'wildtype_predictions.csv'
    wt_predictions_df.to_csv(wt_pred_file, index=False)
    print(f"✓ Saved to: {wt_pred_file}")
    
    # Step 5: Merge and compare
    print("\n" + "="*80)
    print("STEP 5: Compare Wild-Type vs Mutant Predictions")
    print("="*80)
    
    # Merge WT predictions with mutant data
    comparison_df = df.merge(wt_predictions_df, on='variant_id', how='inner')
    
    print(f"✓ Merged {len(comparison_df):,} variants with both WT and mutant predictions")
    
    # Calculate mutation effects (mutant - WT)
    comparison_df['delta_dnase_center'] = comparison_df['dnase_center'] - comparison_df['wt_dnase_center']
    comparison_df['delta_rna_center'] = comparison_df['rna_center'] - comparison_df['wt_rna_center']
    comparison_df['delta_cage_center'] = comparison_df['cage_center'] - comparison_df['wt_cage_center']
    
    # Save comparison
    comparison_file = OUTPUT_DIR / 'wildtype_vs_mutant_comparison.csv'
    comparison_df.to_csv(comparison_file, index=False)
    print(f"✓ Saved comparison to: {comparison_file}")
    
    # Step 6: Statistical analysis
    print("\n" + "="*80)
    print("STEP 6: Statistical Analysis - WT vs Mutant Correlations")
    print("="*80)
    
    results = []
    
    for pred_type in ['dnase_center', 'rna_center', 'cage_center']:
        mutant_col = pred_type
        wt_col = f'wt_{pred_type}'
        
        # Mutant correlation
        valid_mask = ~(comparison_df['mpra_log2_ratio'].isna() | comparison_df[mutant_col].isna())
        valid_data = comparison_df[valid_mask]
        
        if len(valid_data) > 3:
            r_mutant, p_mutant = stats.pearsonr(valid_data['mpra_log2_ratio'], valid_data[mutant_col])
            rho_mutant, p_spear_mutant = stats.spearmanr(valid_data['mpra_log2_ratio'], valid_data[mutant_col])
        else:
            r_mutant = p_mutant = rho_mutant = p_spear_mutant = np.nan
        
        # WT correlation
        valid_mask_wt = ~(comparison_df['mpra_log2_ratio'].isna() | comparison_df[wt_col].isna())
        valid_data_wt = comparison_df[valid_mask_wt]
        
        if len(valid_data_wt) > 3:
            r_wt, p_wt = stats.pearsonr(valid_data_wt['mpra_log2_ratio'], valid_data_wt[wt_col])
            rho_wt, p_spear_wt = stats.spearmanr(valid_data_wt['mpra_log2_ratio'], valid_data_wt[wt_col])
        else:
            r_wt = p_wt = rho_wt = p_spear_wt = np.nan
        
        results.append({
            'metric': pred_type,
            'n_samples': len(valid_data),
            'mutant_pearson_r': r_mutant,
            'mutant_pearson_p': p_mutant,
            'mutant_spearman_r': rho_mutant,
            'wt_pearson_r': r_wt,
            'wt_pearson_p': p_wt,
            'wt_spearman_r': rho_wt,
            'delta_pearson_r': r_wt - r_mutant,
            'improvement': 'Yes' if r_wt > r_mutant else 'No'
        })
    
    results_df = pd.DataFrame(results)
    
    # Print results
    print("\nCORRELATION COMPARISON:")
    print("-" * 80)
    for _, row in results_df.iterrows():
        print(f"\n{row['metric'].upper().replace('_', ' ')}:")
        print(f"  Mutant:  r = {row['mutant_pearson_r']:+.4f}  (p = {row['mutant_pearson_p']:.2e})")
        print(f"  WT:      r = {row['wt_pearson_r']:+.4f}  (p = {row['wt_pearson_p']:.2e})")
        print(f"  Δ:       r = {row['delta_pearson_r']:+.4f}  ({row['improvement']} improvement)")
    
    # Save results
    results_file = OUTPUT_DIR / 'correlation_comparison_summary.csv'
    results_df.to_csv(results_file, index=False)
    print(f"\n✓ Saved summary to: {results_file}")
    
    # Step 7: Visualizations
    print("\n" + "="*80)
    print("STEP 7: Generate Visualizations")
    print("="*80)
    
    # Create comparison plots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Wild-Type vs Mutant Prediction Comparison', fontsize=16, fontweight='bold')
    
    metrics = ['dnase_center', 'rna_center', 'cage_center']
    metric_names = ['DNase-seq', 'RNA-seq', 'CAGE']
    
    for idx, (metric, name) in enumerate(zip(metrics, metric_names)):
        # Top row: WT vs MPRA
        ax1 = axes[0, idx]
        valid = comparison_df[~comparison_df[f'wt_{metric}'].isna()]
        ax1.hexbin(valid['mpra_log2_ratio'], valid[f'wt_{metric}'], gridsize=30, cmap='Blues', mincnt=1)
        r_wt = results_df[results_df['metric'] == metric]['wt_pearson_r'].values[0]
        p_wt = results_df[results_df['metric'] == metric]['wt_pearson_p'].values[0]
        ax1.set_xlabel('MPRA log2(RNA/DNA)', fontsize=11)
        ax1.set_ylabel(f'WT {name} Prediction', fontsize=11)
        ax1.set_title(f'WT {name}\nr = {r_wt:.4f}, p = {p_wt:.2e}', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Bottom row: Mutant vs MPRA
        ax2 = axes[1, idx]
        valid = comparison_df[~comparison_df[metric].isna()]
        ax2.hexbin(valid['mpra_log2_ratio'], valid[metric], gridsize=30, cmap='Reds', mincnt=1)
        r_mut = results_df[results_df['metric'] == metric]['mutant_pearson_r'].values[0]
        p_mut = results_df[results_df['metric'] == metric]['mutant_pearson_p'].values[0]
        ax2.set_xlabel('MPRA log2(RNA/DNA)', fontsize=11)
        ax2.set_ylabel(f'Mutant {name} Prediction', fontsize=11)
        ax2.set_title(f'Mutant {name}\nr = {r_mut:.4f}, p = {p_mut:.2e}', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_file = OUTPUT_DIR / 'wildtype_vs_mutant_correlations.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved plot: {plot_file}")
    plt.close()
    
    # Mutation effect distribution plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('Mutation Effect Distributions (Mutant - WT)', fontsize=16, fontweight='bold')
    
    for idx, (metric, name) in enumerate(zip(metrics, metric_names)):
        ax = axes[idx]
        delta_col = f'delta_{metric}'
        valid = comparison_df[~comparison_df[delta_col].isna()]
        
        ax.hist(valid[delta_col], bins=50, color='purple', alpha=0.7, edgecolor='black')
        mean_delta = valid[delta_col].mean()
        median_delta = valid[delta_col].median()
        
        ax.axvline(0, color='red', linestyle='--', linewidth=2, label='No effect')
        ax.axvline(mean_delta, color='blue', linestyle='-', linewidth=2, label=f'Mean = {mean_delta:.4f}')
        ax.axvline(median_delta, color='green', linestyle='-', linewidth=2, label=f'Median = {median_delta:.4f}')
        
        ax.set_xlabel(f'Δ {name} (Mutant - WT)', fontsize=11)
        ax.set_ylabel('Count', fontsize=11)
        ax.set_title(f'{name} Mutation Effects', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    delta_plot_file = OUTPUT_DIR / 'mutation_effect_distributions.png'
    plt.savefig(delta_plot_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved plot: {delta_plot_file}")
    plt.close()
    
    # Final summary
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)
    print(f"\nAll outputs saved to: {OUTPUT_DIR}")
    print("\nGenerated files:")
    print("  - wildtype_sequences_reconstructed.csv")
    print("  - wildtype_predictions.csv")
    print("  - wildtype_vs_mutant_comparison.csv")
    print("  - correlation_comparison_summary.csv")
    print("  - wildtype_vs_mutant_correlations.png")
    print("  - mutation_effect_distributions.png")
    print(f"  - checkpoints/ ({len(list(CHECKPOINT_DIR.glob('*.csv')))} files)")
    
    print("\n" + "="*80)
    print("KEY FINDINGS:")
    print("="*80)
    best_metric = results_df.loc[results_df['wt_pearson_r'].idxmax()]
    print(f"\nBest WT correlation: {best_metric['metric']}")
    print(f"  WT:     r = {best_metric['wt_pearson_r']:+.4f}")
    print(f"  Mutant: r = {best_metric['mutant_pearson_r']:+.4f}")
    print(f"  Δ:      r = {best_metric['delta_pearson_r']:+.4f}")
    
    if best_metric['wt_pearson_r'] > 0.3:
        print("\n✅ VALIDATION SUCCESSFUL: WT sequences show strong correlation (r > 0.3)")
    elif best_metric['wt_pearson_r'] > best_metric['mutant_pearson_r']:
        print("\n✅ IMPROVEMENT CONFIRMED: WT sequences show better correlation than mutants")
    else:
        print("\n⚠️  UNEXPECTED: WT sequences do not show improved correlation")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    main()
