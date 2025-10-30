#!/usr/bin/env python3
"""
Step 3: Benchmark AlphaGenome predictions against MPRA measurements
Author: Generated for Layer Lab Rotation
Date: October 30, 2025

This script:
1. Loads AlphaGenome predictions and MPRA measurements
2. Computes correlation metrics (Pearson, Spearman)
3. Computes AUROC for binarized predictions
4. Generates comprehensive visualizations
5. Saves benchmark results
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.metrics import roc_curve, auc, roc_auc_score

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
    Create scatter plot with correlation statistics.
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Remove NaN
    valid_mask = ~(df[mpra_col].isna() | df[pred_col].isna())
    plot_df = df[valid_mask]
    
    # Scatter plot
    ax.scatter(plot_df[mpra_col], plot_df[pred_col], alpha=0.5, s=30)
    
    # Compute correlations
    corr_stats = compute_correlations(df, mpra_col, pred_col)
    
    # Add regression line
    z = np.polyfit(plot_df[mpra_col], plot_df[pred_col], 1)
    p = np.poly1d(z)
    x_line = np.linspace(plot_df[mpra_col].min(), plot_df[mpra_col].max(), 100)
    ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label='Linear fit')
    
    # Labels
    ax.set_xlabel(f'MPRA Activity ({mpra_col})', fontsize=12)
    ax.set_ylabel(f'AlphaGenome Prediction ({pred_col})', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add statistics text box
    stats_text = f"N = {corr_stats['n_samples']}\n"
    stats_text += f"Pearson r = {corr_stats['pearson_r']:.3f} (p = {corr_stats['pearson_p']:.2e})\n"
    stats_text += f"Spearman ρ = {corr_stats['spearman_r']:.3f} (p = {corr_stats['spearman_p']:.2e})"
    
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved scatter plot: {output_file.name}")

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
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={"shrink": 0.8})
    
    ax.set_title('Correlation Matrix: MPRA vs AlphaGenome Predictions', 
                 fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved correlation heatmap: {output_file.name}")

def main():
    """Main benchmarking function."""
    print("="*60)
    print("AlphaGenome vs MPRA Benchmark Analysis")
    print("="*60)
    
    # Load predictions
    pred_file = DATA_DIR / 'alphagenome_predictions_sample100.csv'
    
    if not pred_file.exists():
        print(f"Prediction file not found: {pred_file}")
        print("Run 02_run_alphagenome_predictions.py first!")
        return
    
    df = pd.read_csv(pred_file)
    print(f"\n✓ Loaded {len(df)} predictions from {pred_file.name}")
    
    # Filter successful predictions
    df_success = df[df['success'] == True].copy()
    print(f"✓ {len(df_success)} successful predictions ({len(df_success)/len(df)*100:.1f}%)")
    
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
        ax.hist(df_success[pred_col].dropna(), bins=30, alpha=0.7, edgecolor='black')
        ax.set_xlabel(pred_name, fontsize=10)
        ax.set_ylabel('Frequency', fontsize=10)
        ax.set_title(f'Distribution: {pred_name}', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'prediction_distributions.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved distribution plot: prediction_distributions.png")
    
    # Summary report
    print("\n" + "="*60)
    print("Benchmark Complete!")
    print("="*60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nBest performing metrics:")
    top_metrics = results_df.nlargest(3, 'pearson_r')[['prediction_metric', 'pearson_r', 'spearman_r', 'auroc']]
    print(top_metrics.to_string(index=False))
    
    print("\nGenerated files:")
    print(f"  - benchmark_summary.csv")
    print(f"  - {len(pred_columns)} scatter plots")
    print(f"  - 3 ROC curves")
    print(f"  - correlation_heatmap.png")
    print(f"  - prediction_distributions.png")

if __name__ == '__main__':
    main()
