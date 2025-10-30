#!/usr/bin/env python3
"""
Inspect specific sequences from MPRA benchmark results
Author: Generated for Layer Lab Rotation
Date: October 30, 2025

This script helps investigate individual sequence predictions to understand
the negative correlation pattern.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE_DIR = Path('/mnt/work_1/gest9386/CU_Boulder/rotations/LAYER/GSE84888_MPRA')
PRED_FILE = BASE_DIR / 'outputs' / '02_alphagenome_predictions' / 'alphagenome_predictions_sample100.csv'
OUTPUT_DIR = BASE_DIR / 'outputs' / '03_benchmark_results'

def load_and_rank():
    """Load predictions and rank by MPRA activity."""
    df = pd.read_csv(PRED_FILE)
    df = df[df['success'] == True].copy()
    
    # Sort by MPRA activity
    df = df.sort_values('mpra_log2_ratio', ascending=False)
    
    return df

def print_top_bottom(df, n=5):
    """Print top and bottom sequences by MPRA activity."""
    print("="*80)
    print(f"TOP {n} SEQUENCES (Highest MPRA Activity)")
    print("="*80)
    
    cols = ['seq_id', 'sequence_length', 'mpra_log2_ratio', 
            'dnase_center', 'rna_center', 'cage_center']
    
    print(df.head(n)[cols].to_string(index=False))
    
    print("\n" + "="*80)
    print(f"BOTTOM {n} SEQUENCES (Lowest MPRA Activity)")
    print("="*80)
    
    print(df.tail(n)[cols].to_string(index=False))

def plot_rank_correlation(df, output_file):
    """Plot MPRA activity vs AlphaGenome predictions by rank."""
    df = df.copy()
    df['rank'] = range(1, len(df) + 1)
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # DNase
    ax1 = axes[0]
    ax1_twin = ax1.twinx()
    ax1.plot(df['rank'], df['mpra_log2_ratio'], 'o-', color='blue', 
             label='MPRA Activity', linewidth=2)
    ax1_twin.plot(df['rank'], df['dnase_center'], 's-', color='red', 
                  label='AlphaGenome DNase', linewidth=2, alpha=0.7)
    ax1.set_xlabel('Rank (by MPRA activity)', fontsize=11)
    ax1.set_ylabel('MPRA log2(RNA/DNA)', color='blue', fontsize=11)
    ax1_twin.set_ylabel('AlphaGenome DNase', color='red', fontsize=11)
    ax1.set_title('DNase Predictions vs MPRA Activity (Ranked)', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # RNA-seq
    ax2 = axes[1]
    ax2_twin = ax2.twinx()
    ax2.plot(df['rank'], df['mpra_log2_ratio'], 'o-', color='blue', 
             label='MPRA Activity', linewidth=2)
    ax2_twin.plot(df['rank'], df['rna_center'], 's-', color='green', 
                  label='AlphaGenome RNA-seq', linewidth=2, alpha=0.7)
    ax2.set_xlabel('Rank (by MPRA activity)', fontsize=11)
    ax2.set_ylabel('MPRA log2(RNA/DNA)', color='blue', fontsize=11)
    ax2_twin.set_ylabel('AlphaGenome RNA-seq', color='green', fontsize=11)
    ax2.set_title('RNA-seq Predictions vs MPRA Activity (Ranked)', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper left')
    ax2_twin.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # CAGE
    ax3 = axes[2]
    ax3_twin = ax3.twinx()
    ax3.plot(df['rank'], df['mpra_log2_ratio'], 'o-', color='blue', 
             label='MPRA Activity', linewidth=2)
    ax3_twin.plot(df['rank'], df['cage_center'], 's-', color='purple', 
                  label='AlphaGenome CAGE', linewidth=2, alpha=0.7)
    ax3.set_xlabel('Rank (by MPRA activity)', fontsize=11)
    ax3.set_ylabel('MPRA log2(RNA/DNA)', color='blue', fontsize=11)
    ax3_twin.set_ylabel('AlphaGenome CAGE', color='purple', fontsize=11)
    ax3.set_title('CAGE Predictions vs MPRA Activity (Ranked)', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper left')
    ax3_twin.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Saved rank plot: {output_file.name}")

def print_sequence_details(df):
    """Print detailed information for extreme cases."""
    print("\n" + "="*80)
    print("DETAILED SEQUENCE INSPECTION")
    print("="*80)
    
    # Highest MPRA activity
    top = df.iloc[0]
    print("\n🔺 HIGHEST MPRA ACTIVITY:")
    print(f"  Sequence ID: {top['seq_id']}")
    print(f"  Location: {top['chromosome']}:{top['start']}-{top['end']}")
    print(f"  Sequence: {top['sequence'][:50]}..." if len(top['sequence']) > 50 else f"  Sequence: {top['sequence']}")
    print(f"  Length: {top['sequence_length']} bp")
    print(f"  MPRA log2 ratio: {top['mpra_log2_ratio']:.4f}")
    print(f"  AlphaGenome DNase: {top['dnase_center']:.6f}")
    print(f"  AlphaGenome RNA-seq: {top['rna_center']:.6f}")
    print(f"  AlphaGenome CAGE: {top['cage_center']:.6f}")
    
    # Lowest MPRA activity
    bottom = df.iloc[-1]
    print("\n🔻 LOWEST MPRA ACTIVITY:")
    print(f"  Sequence ID: {bottom['seq_id']}")
    print(f"  Location: {bottom['chromosome']}:{bottom['start']}-{bottom['end']}")
    print(f"  Sequence: {bottom['sequence'][:50]}..." if len(bottom['sequence']) > 50 else f"  Sequence: {bottom['sequence']}")
    print(f"  Length: {bottom['sequence_length']} bp")
    print(f"  MPRA log2 ratio: {bottom['mpra_log2_ratio']:.4f}")
    print(f"  AlphaGenome DNase: {bottom['dnase_center']:.6f}")
    print(f"  AlphaGenome RNA-seq: {bottom['rna_center']:.6f}")
    print(f"  AlphaGenome CAGE: {bottom['cage_center']:.6f}")

def main():
    print("="*80)
    print("MPRA Sequence Inspector")
    print("="*80)
    
    # Load data
    df = load_and_rank()
    print(f"\n✓ Loaded {len(df)} sequences with successful predictions")
    
    # Print top/bottom
    print_top_bottom(df, n=5)
    
    # Plot ranks
    plot_rank_correlation(df, OUTPUT_DIR / 'rank_correlation_plot.png')
    
    # Detailed inspection
    print_sequence_details(df)
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    print("\nMPRA Activity:")
    print(df['mpra_log2_ratio'].describe())
    
    print("\nAlphaGenome DNase (Center):")
    print(df['dnase_center'].describe())
    
    print("\nAlphaGenome RNA-seq (Center):")
    print(df['rna_center'].describe())
    
    print("\nAlphaGenome CAGE (Center):")
    print(df['cage_center'].describe())
    
    # Correlation with inverted predictions
    print("\n" + "="*80)
    print("INVERTED CORRELATION TEST")
    print("="*80)
    
    from scipy.stats import pearsonr, spearmanr
    
    # Test with inverted predictions
    df['dnase_inverted'] = -df['dnase_center']
    df['rna_inverted'] = -df['rna_center']
    df['cage_inverted'] = -df['cage_center']
    
    print("\nIf we INVERT predictions (multiply by -1):")
    
    for metric, col in [('DNase', 'dnase_inverted'), 
                        ('RNA-seq', 'rna_inverted'), 
                        ('CAGE', 'cage_inverted')]:
        r, p = pearsonr(df['mpra_log2_ratio'], df[col])
        rho, rho_p = spearmanr(df['mpra_log2_ratio'], df[col])
        print(f"\n{metric}:")
        print(f"  Pearson r:  {r:.4f} (p={p:.4f})")
        print(f"  Spearman ρ: {rho:.4f} (p={rho_p:.4f})")
    
    print("\n" + "="*80)
    print("✓ Inspection complete!")
    print("="*80)

if __name__ == '__main__':
    main()
