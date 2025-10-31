# 🚀 Quick Reference - Version 2

## One-Command Execution

```bash
cd /mnt/work_1/gest9386/CU_Boulder/rotations/LAYER/GSE84888_MPRA
conda activate alphagenome-env
python code/run_pipeline.py
```

---

## Key Results at a Glance

| Metric | Value | Note |
|--------|-------|------|
| **Sample Size** | 6,863 variants | 381× larger than V1 |
| **Success Rate** | 100% | All predictions succeeded |
| **Best Correlation** | r = 0.053 | DNase center region |
| **Significance** | p < 10⁻⁵ | Highly significant |
| **Statistical Power** | >99% | Strong confidence |
| **Runtime** | ~35 min total | Data prep + predictions + analysis |

---

## 📊 Top 3 Metrics

| Rank | Metric | Pearson r | Spearman ρ | AUROC |
|------|--------|-----------|------------|-------|
| 1 | DNase (Center) | 0.053 | 0.095 | 0.538 |
| 2 | CAGE (Center) | 0.040 | 0.119 | 0.543 |
| 3 | DNase (Mean) | 0.042 | 0.091 | 0.539 |

---

## 📁 File Structure (Professional Upload)

```
GSE84888_MPRA/
├── README.md                    # Complete V2 documentation
├── RESULTS_SUMMARY.md           # Detailed analysis
├── QUICK_REFERENCE.md           # This file
├── .gitignore                   # Excludes large files
│
├── code/                        # Analysis pipeline (5 scripts)
│   ├── 01_prepare_mpra_data.py
│   ├── 02_run_alphagenome_predictions.py
│   ├── 03_benchmark_correlations.py
│   └── run_pipeline.py
│
├── data/                        # Input data (NOT in repo)
│   ├── mm9_ref/                 # Genome reference (excluded)
│   ├── Synthetic_enhancer_seq/  # Raw sequences (excluded)
│   └── MPRA_reporter_counts/    # MPRA data (excluded)
│
└── outputs/                     # Results (partial)
    ├── 01_prepared_data/
    │   ├── mpra_test_sample_100.csv  (included)
    │   └── dataset_metadata.json     (included)
    │
    ├── 02_alphagenome_predictions/
    │   └── [Large files excluded from repo]
    │
    └── 03_benchmark_results/
        ├── benchmark_summary.csv         ✅ (included)
        ├── per_tf_correlations.csv       ✅ (included)
        ├── per_strand_correlations.csv   ✅ (included)
        ├── per_chromosome_correlations.csv ✅ (included)
        └── *.png (11 visualizations)     ✅ (included)
```

**Note:** Large data files (>50MB) excluded via .gitignore. See README.md for download instructions.

---

## 🔧 Quick Commands

### Run Individual Steps

```bash
# Step 1: Prepare data (requires mm9 genome)
conda activate alphagenome-env
python code/01_prepare_mpra_data.py

# Step 2: Run predictions (requires API key in .env)
python code/02_run_alphagenome_predictions.py

# Step 3: Benchmark analysis
python code/03_benchmark_correlations.py
```

### View Results

```bash
# Summary statistics
cat outputs/03_benchmark_results/benchmark_summary.csv | column -t -s,

# Per-TF analysis
cat outputs/03_benchmark_results/per_tf_correlations.csv | head -20

# View plots (Linux)
xdg-open outputs/03_benchmark_results/*.png
```

---

## 📊 Data Summary

### MPRA Activity Distribution
- **Mean:** -1.075 log2(RNA/DNA)
- **Range:** -10.2 to +5.0
- **N:** 6,863 variants

### AlphaGenome Predictions (DNase Center)
- **Mean:** 0.099
- **Range:** 0.009 to 1.416
- **All predictions:** 2048bp sequences with center focus

---

## 🔑 Key Findings

### ✅ What Works
- Statistical significance achieved (p < 10⁻⁵)
- Center region > full sequence
- DNase-seq most reliable
- 100% prediction success

### ⚠️ Limitations
- Weak correlation (r ≈ 0.05)
- Limited practical utility for MPRA
- Context mismatch (synthetic vs natural)
- Cross-species prediction uncertainty

---

## 🎓 Main Takeaway

**AlphaGenome detects regulatory signal but shows weak predictive power for synthetic MPRA sequences.** This is expected given the biological context differences (episomal vs endogenous, mutant vs wild-type). The model performs better on natural genomic sequences in native chromatin context.

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| Missing mm9 genome | Download from UCSC and index with pyfaidx |
| API key error | Create .env file with ALPHA_GENOME_KEY |
| Large files in git | Excluded via .gitignore |
| Out of memory | Use test sample (mpra_test_sample_100.csv) |

---

## 🌐 Resources

- **Dataset:** [GEO GSE84888](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE84888)
- **AlphaGenome:** [Documentation](https://www.alphagenomedocs.com/)
- **Repository:** Check README.md for complete details

---

**Version:** 2.0  
**Last Updated:** October 31, 2025  
**Status:** ✅ Production Ready
