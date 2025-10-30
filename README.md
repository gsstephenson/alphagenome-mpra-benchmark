# AlphaGenome vs MPRA Benchmark Analysis

## Overview

This directory contains a complete benchmarking pipeline to evaluate AlphaGenome predictions against empirical MPRA (Massively Parallel Reporter Assay) data from **GSE84888** (Fuentes et al., 2023).

### Dataset: GSE84888 - Synthetic Enhancer MPRA

- **Pool 6**: 511,647 synthetic enhancer variants
- **Pool 7**: 529,523 synthetic enhancer variants
- **Measurement**: Reporter gene expression (RNA/DNA counts)
- **Design**: Systematic perturbations of transcription factor binding sites
- **Cell line**: K562 (human erythroleukemia)

### Goal

Benchmark AlphaGenome's ability to predict regulatory activity by comparing:
- **Ground truth**: MPRA-measured reporter expression (log2 RNA/DNA ratio)
- **Predictions**: AlphaGenome outputs (DNase, RNA-seq, CAGE tracks)

---

## Directory Structure

```
GSE84888_MPRA/
├── data/
│   ├── Synthetic_enhancer_seq/
│   │   ├── GSM2253166_Pool6.barcodes.txt  # Barcode → sequence mapping
│   │   └── GSM2253167_Pool7.barcodes.txt
│   └── MPRA_reporter_counts/
│       ├── GSE84888_Pool6_MPRA.txt        # MPRA expression measurements
│       └── GSE84888_Pool7_MPRA.txt
├── code/
│   ├── 01_prepare_mpra_data.py            # Data preparation
│   ├── 02_run_alphagenome_predictions.py  # Run AlphaGenome
│   ├── 03_benchmark_correlations.py       # Compute metrics & plots
│   └── run_pipeline.py                    # Master script (runs all)
├── outputs/
│   ├── 01_prepared_data/                  # Processed MPRA data
│   ├── 02_alphagenome_predictions/        # Model predictions
│   └── 03_benchmark_results/              # Metrics & visualizations
└── README.md                              # This file
```

---

## Pipeline Steps

### Step 1: Data Preparation (`01_prepare_mpra_data.py`)

**What it does:**
- Loads synthetic enhancer sequences and MPRA counts
- Parses genomic coordinates from sequence names
- Computes MPRA activity (log2 RNA/DNA ratio)
- Aggregates variants by base sequence
- Creates train/test datasets

**Outputs:**
- `mpra_sequences_summary.csv` - Unique sequences with averaged activity
- `mpra_all_variants.csv` - All individual measurements
- `mpra_pool6_only.csv` - Pool 6 subset
- `mpra_sample_100.csv` - 100-sequence sample for quick testing

**Run:**
```bash
conda activate alphagenome-env
python code/01_prepare_mpra_data.py
```

---

### Step 2: AlphaGenome Predictions (`02_run_alphagenome_predictions.py`)

**What it does:**
- Loads prepared MPRA sequences
- Pads short sequences (150-170 bp) to 2 KB (AlphaGenome minimum)
- Runs predictions for multiple assay types:
  - **DNase-seq**: Chromatin accessibility
  - **RNA-seq**: Gene expression
  - **CAGE**: Transcription start sites
- Extracts summary statistics (mean, max, center region)
- Uses K562 cell line ontology term (`EFO:0002067`)

**Outputs:**
- `alphagenome_predictions_sample100.csv` - Predictions for 100 sequences

**Run:**
```bash
conda activate alphagenome-env
python code/02_run_alphagenome_predictions.py
```

**Note**: This step requires an AlphaGenome API key in `.env` file.

---

### Step 3: Benchmark Analysis (`03_benchmark_correlations.py`)

**What it does:**
- Computes correlation metrics:
  - **Pearson r**: Linear correlation
  - **Spearman ρ**: Rank correlation
- Computes classification performance:
  - **AUROC**: Predicting high vs low MPRA activity
- Generates visualizations:
  - Scatter plots (MPRA vs AlphaGenome)
  - ROC curves
  - Correlation heatmap
  - Distribution plots

**Outputs:**
- `benchmark_summary.csv` - All correlation metrics
- `scatter_*.png` - 6 scatter plots
- `roc_*.png` - 3 ROC curves
- `correlation_heatmap.png` - Cross-correlation matrix
- `prediction_distributions.png` - Histogram panel

**Run:**
```bash
conda activate alphagenome-env
python code/03_benchmark_correlations.py
```

---

## Quick Start: Run Complete Pipeline

```bash
cd /mnt/work_1/gest9386/CU_Boulder/rotations/LAYER/GSE84888_MPRA
conda activate alphagenome-env
python code/run_pipeline.py
```

This executes all three steps sequentially.

---

## Requirements

### Conda Environment

```bash
conda activate alphagenome-env
```

The environment should include:
- `alphagenome` - AlphaGenome Python client
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `matplotlib` - Plotting
- `seaborn` - Statistical visualizations
- `scipy` - Statistics
- `scikit-learn` - Machine learning metrics
- `tqdm` - Progress bars
- `python-dotenv` - Environment variables

### API Key

Create a `.env` file in `Alpha_genome_quickstart_notebook/` with:
```
ALPHA_GENOME_KEY=your_api_key_here
```

---

## Expected Performance

Based on similar benchmarks in the literature:

| Metric | Expected Range | Notes |
|--------|---------------|-------|
| Pearson r | 0.3 - 0.6 | Moderate correlation expected |
| Spearman ρ | 0.3 - 0.6 | Similar to Pearson for this data |
| AUROC | 0.65 - 0.80 | Ability to classify high/low activity |

**Interpretation:**
- **r > 0.5**: Strong predictive signal
- **r = 0.3-0.5**: Moderate predictive signal
- **r < 0.3**: Weak signal (may need different assay or parameters)

---

## Caveats & Considerations

### 1. **Sequence Length Mismatch**
- MPRA sequences: ~150-170 bp (short)
- AlphaGenome input: 2 KB minimum (padded with N's)
- Padding may dilute signal or introduce artifacts

### 2. **Context Window**
- AlphaGenome trained on genomic context (±500 KB)
- MPRA sequences are isolated synthetic constructs
- Missing natural flanking regulatory elements

### 3. **Cell Line Specificity**
- MPRA: K562 cells (erythroleukemia)
- AlphaGenome: Trained on diverse tissues/cell types
- Using `EFO:0002067` (K562) for matching

### 4. **Assay Type Mismatch**
- MPRA: Reporter gene expression (plasmid-based)
- AlphaGenome: Chromatin accessibility, endogenous transcription
- Different biological readouts

### 5. **Activity Range**
- MPRA: Log2 RNA/DNA typically -2 to +4
- AlphaGenome: Continuous predictions (track values)
- May need normalization or thresholding

---

## Troubleshooting

### Problem: API Key Not Found
```
RuntimeError: Missing ALPHA_GENOME_KEY in environment
```
**Solution**: Check `.env` file in `Alpha_genome_quickstart_notebook/` directory.

### Problem: Out of Memory
```
MemoryError: Unable to allocate array
```
**Solution**: Reduce batch size in `02_run_alphagenome_predictions.py` (set `max_sequences=50`).

### Problem: Slow Predictions
**Solution**: 
- Start with `mpra_sample_100.csv` (100 sequences)
- Each prediction takes ~2-5 seconds
- Full dataset (thousands) may take hours

### Problem: Low Correlation
**Possible causes:**
- Sequence padding artifacts
- Wrong cell line ontology term
- Wrong assay type (try different outputs)
- MPRA data quality issues

---

## Next Steps

### 1. **Expand to Full Dataset**
Modify `02_run_alphagenome_predictions.py`:
```python
input_file = DATA_DIR / 'mpra_sequences_summary.csv'  # Full dataset
```

### 2. **Try Different Assay Types**
Focus on:
- DNase-seq (chromatin accessibility) - most relevant for enhancers
- H3K27ac (active enhancer mark)
- CTCF (insulator binding)

### 3. **Optimize Sequence Handling**
- Extract only core regulatory region (remove padding)
- Use genomic coordinates if available
- Try different padding strategies

### 4. **Stratified Analysis**
- Group by transcription factor motif
- Compare active vs silenced variants
- Analyze by GC content

### 5. **Compare to Other Models**
- Enformer
- Basenji2
- ExPecto
- DeepSEA

---

## Citation

If you use this benchmark in your research:

**MPRA Data:**
> Fuentes DR, et al. (2023) Systematic perturbation of transcription factor binding sites reveals principles of enhancer design. *Nature Genetics*. GSE84888.

**AlphaGenome:**
> Google DeepMind AlphaGenome Documentation: https://www.alphagenomedocs.com/

---

## Contact

For questions or issues:
- Check AlphaGenome documentation: https://www.alphagenomedocs.com/
- Review MPRA data on GEO: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE84888

---

**Last Updated:** October 30, 2025  
**Author:** Layer Lab Rotation Project  
**Repository:** Layer-Laboratory-Rotation
