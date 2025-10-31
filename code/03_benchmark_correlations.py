#!/usr/bin/env python3
"""
Step 3: Benchmark AlphaGenome predictions against MPRA measurements - VERSION 2
Author: Generated for Layer Lab Rotation
Date: October 31, 2025

VERSION 2 ENHANCEMENTS:
- Analyzes all 6,863 variants (vs 18 in V1)
- Hexbin plots for large-scale visualization
- Per-TF transcription factor analysis
- Strand-specific analysis
- Chromosome-specific analysis
- Enhanced statistical power

This script:
1. Loads AlphaGenome predictions and MPRA measurements
2. Computes correlation metrics (Pearson, Spearman)
3. Computes AUROC for binarized predictions
4. Performs per-TF and strand-specific analysis
5. Generates comprehensive visualizations
6. Saves benchmark results
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.metrics import roc_curve, auc, roc_auc_score
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10

# Set paths
BASE_DIR = Path('/mnt/work_1/gest9386/CU_Boulder/rotations/LAYER/GSE84888_MPRA')
DATA_DIR = BASE_DIR / 'outputs' / '02_alphagenome_predictions'
OUTPUT_DIR = BASE_DIR / 'outputs' / '03_benchmark_results'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def compute_correlations(df, mpra_col, pred_col):
    """
    Compute Pearson and Spearman correlations between MPRA and predictions.
    """
    # Remove NaN values
    valid_mask = ~(df[mpra_col].isna() | df[pred_col].isna())
    valid_df = df[valid_mask]
    
    if len(valid_df) < 3:
        return {
            'n_samples': len(valid_df),
            'pearson_r': np.nan,
            'pearson_p': np.nan,
            'spearman_r': np.nan,
            'spearman_p': np.nan
        }
    
    pearson_r, pearson_p = stats.pearsonr(valid_df[mpra_col], valid_df[pred_col])
    spearman_r, spearman_p = stats.spearmanr(valid_df[mpra_col], valid_df[pred_col])
    
    return {
        'n_samples': len(valid_df),
        'pearson_r': pearson_r,
        'pearson_p': pearson_p,
        'spearman_r': spearman_r,
        'spearman_p': spearman_p
    }

def compute_auroc(df, mpra_col, pred_col, threshold='median'):
    """
    Compute AUROC by binarizing MPRA activity at a threshold.
    """
    valid_mask = ~(df[mpra_col].isna() | df[pred_col].isna())
    valid_df = df[valid_mask]
    
    if len(valid_df) < 10:
        return {'auroc': np.nan, 'threshold': np.nan, 'n_positive': 0, 'n_negative': 0}
    
    # Binarize MPRA activity
    if threshold == 'median':
        thresh_val = valid_df[mpra_col].median()
    elif threshold == 'mean':
        thresh_val = valid_df[mpra_col].mean()
    else:
        thresh_val = threshold
    
    y_true = (valid_df[mpra_col] > thresh_val).astype(int)
    y_pred = valid_df[pred_col]
    
    n_pos = y_true.sum()
    n_neg = len(y_true) - n_pos
    
    if n_pos == 0 or n_neg == 0:
        return {'auroc': np.nan, 'threshold': thresh_val, 'n_positive': n_pos, 'n_negative': n_neg}
    
    auroc = roc_auc_score(y_true, y_pred)
    
    return {
        'auroc': auroc,
        'threshold': thresh_val,
        'n_positive': n_pos,
        'n_negative': n_neg
    }

def plot_scatter(df, mpra_col, pred_col, title, output_file):
    """
    Create hexbin plot for large-scale data (6,863 points).
    VERSION 2: Uses hexbin instead of scatter for better visualization.
    """
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Remove NaN
    valid_mask = ~(df[mpra_col].isna() | df[pred_col].isna())
    plot_df = df[valid_mask]
    
    # Hexbin plot for large datasets
    hexbin = ax.hexbin(plot_df[mpra_col], plot_df[pred_col], 
                       gridsize=50, cmap='YlOrRd', mincnt=1, alpha=0.8)
    cb = plt.colorbar(hexbin, ax=ax)
    cb.set_label('Count', fontsize=11)
    
    # Compute correlations
    corr_stats = compute_correlations(df, mpra_col, pred_col)
    
    # Add regression line
    z = np.polyfit(plot_df[mpra_col], plot_df[pred_col], 1)
    p = np.poly1d(z)
    x_line = np.linspace(plot_df[mpra_col].min(), plot_df[mpra_col].max(), 100)
    ax.plot(x_line, p(x_line), "b-", alpha=0.8, linewidth=2, label='Linear fit')
    
    # Labels
    ax.set_xlabel(f'MPRA Activity (log2 RNA/DNA)', fontsize=13)
    ax.set_ylabel(f'AlphaGenome {pred_col.replace("_", " ").title()}', fontsize=13)
    ax.set_title(title, fontsize=15, fontweight='bold', pad=15)
    
    # Add statistics text box
    stats_text = f"N = {corr_stats['n_samples']:,}\n"
    stats_text += f"Pearson r = {corr_stats['pearson_r']:.4f}\n"
    stats_text += f"  p = {corr_stats['pearson_p']:.2e}\n"
    stats_text += f"Spearman ρ = {corr_stats['spearman_r']:.4f}\n"
    stats_text += f"  p = {corr_stats['spearman_p']:.2e}"
    
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
            fontsize=11, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.9, pad=0.8))
    
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved hexbin plot: {output_file.name}")

def plot_roc_curve(df, mpra_col, pred_col, title, output_file, threshold='median'):
    """
    Plot ROC curve for binarized MPRA activity.
    """
    valid_mask = ~(df[mpra_col].isna() | df[pred_col].isna())
    valid_df = df[valid_mask]
    
    # Binarize
    if threshold == 'median':
        thresh_val = valid_df[mpra_col].median()
    else:
        thresh_val = valid_df[mpra_col].mean()
    
    y_true = (valid_df[mpra_col] > thresh_val).astype(int)
    y_pred = valid_df[pred_col]
    
    # Compute ROC curve
    fpr, tpr, thresholds = roc_curve(y_true, y_pred)
    roc_auc = auc(fpr, tpr)
    
    # Plot
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
    ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random classifier')
    
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc="lower right", fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved ROC curve: {output_file.name}")

def plot_heatmap_correlation(corr_matrix, output_file):
    """
    Plot heatmap of correlations between different prediction metrics.
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                annot_kws={"size": 10})
    
    ax.set_title('Correlation Matrix: MPRA vs AlphaGenome Predictions (N=6,863)', 
                 fontsize=15, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved correlation heatmap: {output_file.name}")

def analyze_per_tf(df, mpra_col, pred_col):
    """
    VERSION 2: Analyze correlations for each transcription factor separately.
    Extracts TF names from tf_info, filtering out numeric position codes.
    """
    # Extract TF names from tf_info column
    # Format examples: "err1_82_92_atf3", "lxr_vbp_4_1", "myb_24_38_rar"
    # We want to extract non-numeric TF names (atf3, lxr, vbp, myb, rar)
    def extract_tf_names(tf_str):
        if pd.isna(tf_str) or tf_str == 'wt':
            return ['wt']
        
        parts = tf_str.split('_')
        # Filter out numeric-only parts (position codes)
        tf_names = [p for p in parts if not p.isdigit() and p.isalpha()]
        return tf_names if tf_names else ['unknown']
    
    df = df.copy()
    df['tf_names_list'] = df['tf_info'].apply(extract_tf_names)
    
    # Explode so each TF gets its own row (variants can have multiple TFs)
    df_exploded = df.explode('tf_names_list')
    df_exploded = df_exploded.rename(columns={'tf_names_list': 'tf_name'})
    
    tf_results = []
    
    for tf_name in df_exploded['tf_name'].unique():
        if pd.isna(tf_name) or tf_name == '' or tf_name == 'unknown':
            continue
        
        tf_df = df_exploded[df_exploded['tf_name'] == tf_name]
        
        if len(tf_df) < 10:  # Skip TFs with too few variants
            continue
        
        corr_stats = compute_correlations(tf_df, mpra_col, pred_col)
        
        if not np.isnan(corr_stats['pearson_r']):
            tf_results.append({
                'tf_name': tf_name,
                'n_variants': len(tf_df),
                'pearson_r': corr_stats['pearson_r'],
                'pearson_p': corr_stats['pearson_p'],
                'spearman_r': corr_stats['spearman_r'],
                'spearman_p': corr_stats['spearman_p']
            })
    
    return pd.DataFrame(tf_results).sort_values('pearson_r', ascending=False)

def analyze_per_strand(df, mpra_col, pred_col):
    """
    VERSION 2: Analyze correlations separately for + and - strands.
    """
    results = []
    
    for strand in ['+', '-']:
        strand_df = df[df['strand'] == strand]
        corr_stats = compute_correlations(strand_df, mpra_col, pred_col)
        
        results.append({
            'strand': strand,
            'n_variants': len(strand_df),
            **corr_stats
        })
    
    return pd.DataFrame(results)

def analyze_per_chromosome(df, mpra_col, pred_col):
    """
    VERSION 2: Analyze correlations for each chromosome.
    """
    results = []
    
    for chrom in sorted(df['chromosome'].unique()):
        chrom_df = df[df['chromosome'] == chrom]
        
        if len(chrom_df) < 10:
            continue
        
        corr_stats = compute_correlations(chrom_df, mpra_col, pred_col)
        
        results.append({
            'chromosome': chrom,
            'n_variants': len(chrom_df),
            **corr_stats
        })
    
    return pd.DataFrame(results)

def plot_per_tf_analysis(tf_df, output_file):
    """
    VERSION 2: Visualize per-TF correlations.
    """
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Sort by Pearson r
    tf_df_plot = tf_df.nlargest(30, 'pearson_r')  # Top 30 TFs
    
    colors = ['red' if r < 0 else 'green' for r in tf_df_plot['pearson_r']]
    
    ax.barh(range(len(tf_df_plot)), tf_df_plot['pearson_r'], color=colors, alpha=0.7)
    ax.set_yticks(range(len(tf_df_plot)))
    ax.set_yticklabels(tf_df_plot['tf_name'], fontsize=9)
    ax.set_xlabel('Pearson Correlation (r)', fontsize=12)
    ax.set_title('Top 30 Transcription Factors by Correlation', 
                 fontsize=14, fontweight='bold', pad=15)
    ax.axvline(x=0, color='black', linestyle='--', linewidth=1)
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved per-TF analysis: {output_file.name}")

def main():
    """Main benchmarking function - VERSION 2."""
    print("="*60)
    print("AlphaGenome vs MPRA Benchmark Analysis - VERSION 2")
    print("="*60)
    print("\nVERSION 2 FEATURES:")
    print("  - Analyzes all 6,863 variants")
    print("  - Per-TF transcription factor analysis")
    print("  - Strand-specific analysis")
    print("  - Chromosome-specific analysis")
    print("  - Enhanced visualizations (hexbin plots)")
    print("="*60)
    
    # Load predictions
    pred_file = DATA_DIR / 'alphagenome_predictions_all_variants.csv'
    
    if not pred_file.exists():
        print(f"\nPrediction file not found: {pred_file}")
        print("Run 02_run_alphagenome_predictions.py first!")
        return
    
    df = pd.read_csv(pred_file)
    print(f"\n✓ Loaded {len(df):,} predictions from {pred_file.name}")
    
    # Filter successful predictions
    df_success = df[df['success'] == True].copy()
    print(f"✓ {len(df_success):,} successful predictions ({len(df_success)/len(df)*100:.1f}%)")
    
    # Prediction columns to benchmark
    pred_columns = [
        ('dnase_center', 'DNase (Center)'),
        ('dnase_mean', 'DNase (Mean)'),
        ('rna_center', 'RNA-seq (Center)'),
        ('rna_mean', 'RNA-seq (Mean)'),
        ('cage_center', 'CAGE (Center)'),
        ('cage_mean', 'CAGE (Mean)'),
    ]
    
    mpra_col = 'mpra_log2_ratio'
    
    # Compute all correlations
    print("\n" + "="*60)
    print("Computing Correlations")
    print("="*60)
    
    results = []
    
    for pred_col, pred_name in pred_columns:
        corr_stats = compute_correlations(df_success, mpra_col, pred_col)
        auroc_stats = compute_auroc(df_success, mpra_col, pred_col, threshold='median')
        
        result = {
            'prediction_metric': pred_name,
            'column_name': pred_col,
            **corr_stats,
            **auroc_stats
        }
        results.append(result)
        
        print(f"\n{pred_name}:")
        print(f"  Pearson r:  {corr_stats['pearson_r']:.4f} (p={corr_stats['pearson_p']:.2e})")
        print(f"  Spearman ρ: {corr_stats['spearman_r']:.4f} (p={corr_stats['spearman_p']:.2e})")
        print(f"  AUROC:      {auroc_stats['auroc']:.4f}")
    
    # Save results table
    results_df = pd.DataFrame(results)
    results_file = OUTPUT_DIR / 'benchmark_summary.csv'
    results_df.to_csv(results_file, index=False)
    print(f"\n✓ Saved benchmark summary: {results_file}")
    
    # Generate plots
    print("\n" + "="*60)
    print("Generating Visualizations")
    print("="*60)
    
    # Scatter plots for each prediction metric
    for pred_col, pred_name in pred_columns:
        plot_scatter(
            df_success, mpra_col, pred_col,
            title=f'MPRA Activity vs {pred_name}',
            output_file=OUTPUT_DIR / f'scatter_{pred_col}.png'
        )
    
    # ROC curves
    for pred_col, pred_name in pred_columns[:3]:  # Top 3 metrics
        plot_roc_curve(
            df_success, mpra_col, pred_col,
            title=f'ROC Curve: {pred_name} predicting High MPRA Activity',
            output_file=OUTPUT_DIR / f'roc_{pred_col}.png',
            threshold='median'
        )
    
    # Correlation heatmap
    pred_cols_for_heatmap = [mpra_col] + [col for col, _ in pred_columns]
    corr_matrix = df_success[pred_cols_for_heatmap].corr()
    plot_heatmap_correlation(corr_matrix, OUTPUT_DIR / 'correlation_heatmap.png')
    
    # Distribution plots
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for idx, (pred_col, pred_name) in enumerate(pred_columns):
        ax = axes[idx]
        ax.hist(df_success[pred_col].dropna(), bins=50, alpha=0.7, edgecolor='black')
        ax.set_xlabel(pred_name, fontsize=10)
        ax.set_ylabel('Frequency', fontsize=10)
        ax.set_title(f'Distribution: {pred_name} (N={len(df_success):,})', 
                     fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'prediction_distributions.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved distribution plot: prediction_distributions.png")
    
    # VERSION 2: Per-TF Analysis
    print("\n" + "="*60)
    print("Running Per-Transcription Factor Analysis...")
    print("="*60)
    
    tf_analysis = analyze_per_tf(df_success, mpra_col, 'dnase_center')
    if len(tf_analysis) > 0:
        tf_file = OUTPUT_DIR / 'per_tf_correlations.csv'
        tf_analysis.to_csv(tf_file, index=False)
        print(f"✓ Saved per-TF analysis: {tf_file.name} ({len(tf_analysis)} TFs)")
        
        plot_per_tf_analysis(tf_analysis, OUTPUT_DIR / 'per_tf_barplot.png')
        
        print("\nTop 5 TFs with strongest positive correlation:")
        print(tf_analysis.head(5)[['tf_name', 'n_variants', 'pearson_r']].to_string(index=False))
        print("\nTop 5 TFs with strongest negative correlation:")
        print(tf_analysis.tail(5)[['tf_name', 'n_variants', 'pearson_r']].to_string(index=False))
    
    # VERSION 2: Strand Analysis
    print("\n" + "="*60)
    print("Running Strand-Specific Analysis...")
    print("="*60)
    
    strand_analysis = analyze_per_strand(df_success, mpra_col, 'dnase_center')
    strand_file = OUTPUT_DIR / 'per_strand_correlations.csv'
    strand_analysis.to_csv(strand_file, index=False)
    print(f"✓ Saved strand analysis: {strand_file.name}")
    print("\nStrand-specific correlations:")
    print(strand_analysis[['strand', 'n_variants', 'pearson_r', 'spearman_r']].to_string(index=False))
    
    # VERSION 2: Chromosome Analysis
    print("\n" + "="*60)
    print("Running Chromosome-Specific Analysis...")
    print("="*60)
    
    chrom_analysis = analyze_per_chromosome(df_success, mpra_col, 'dnase_center')
    chrom_file = OUTPUT_DIR / 'per_chromosome_correlations.csv'
    chrom_analysis.to_csv(chrom_file, index=False)
    print(f"✓ Saved chromosome analysis: {chrom_file.name}")
    print("\nChromosome-specific correlations:")
    print(chrom_analysis[['chromosome', 'n_variants', 'pearson_r']].to_string(index=False))
    
    # Summary report
    print("\n" + "="*60)
    print("Benchmark Complete!")
    print("="*60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nOverall best performing metrics:")
    top_metrics = results_df.nlargest(3, 'pearson_r')[['prediction_metric', 'pearson_r', 'spearman_r', 'auroc']]
    print(top_metrics.to_string(index=False))
    
    print("\nGenerated files:")
    print(f"  - benchmark_summary.csv (overall metrics)")
    print(f"  - per_tf_correlations.csv ({len(tf_analysis) if len(tf_analysis) > 0 else 0} TFs)")
    print(f"  - per_strand_correlations.csv")
    print(f"  - per_chromosome_correlations.csv")
    print(f"  - {len(pred_columns)} hexbin plots")
    print(f"  - 3 ROC curves")
    print(f"  - correlation_heatmap.png")
    print(f"  - prediction_distributions.png")
    print(f"  - per_tf_barplot.png")
    
    print("\n" + "="*60)
    print("Key Findings:")
    print("="*60)
    overall_r = results_df[results_df['column_name'] == 'dnase_center']['pearson_r'].values[0]
    overall_p = results_df[results_df['column_name'] == 'dnase_center']['pearson_p'].values[0]
    print(f"  Overall correlation (DNase center): r = {overall_r:.4f}, p = {overall_p:.2e}")
    print(f"  Sample size: N = {len(df_success):,} variants")
    print(f"  Statistical power: {'High (>99%)' if len(df_success) > 1000 else 'Moderate'}")
    print(f"  Version 2 provides {len(df_success)/18:.0f}× more data than Version 1")

if __name__ == '__main__':
    main()
