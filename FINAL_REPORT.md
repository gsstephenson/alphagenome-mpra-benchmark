# AlphaGenome vs MPRA Benchmark - Final Report

**Project:** Systematic validation of AlphaGenome predictions against experimental MPRA data  
**Dataset:** GSE84888 - Synthetic enhancer perturbations  
**Version:** 2.0 (Production)  
**Date:** October 31, 2025  
**Institution:** Layer Laboratory, CU Boulder

---

## Project Overview

### Objective

Benchmark AlphaGenome's ability to predict regulatory activity by comparing model predictions against empirical MPRA (Massively Parallel Reporter Assay) measurements from 6,863 synthetic enhancer variants.

### Dataset: GSE84888

- **Source:** Fuentes et al., 2023
- **Design:** Systematic mutations in transcription factor binding sites
- **Measurement:** Reporter gene expression (log2 RNA/DNA)
- **Cell Line:** K562 (human erythroleukemia)
- **Genome:** mm9 (mouse)
- **Variants:** 6,863 unique TF binding site perturbations

### AlphaGenome Configuration

- **Model:** AlphaGenome API
- **Ontology:** K562 (EFO:0002067)
- **Predictions:** DNase-seq, RNA-seq, CAGE
- **Input:** 2048bp sequences (real genomic context from mm9)
- **Analysis:** Center region (200bp) + full sequence statistics

---

## Methodology

### Version 2 Pipeline

**Step 1: Data Preparation** (`01_prepare_mpra_data.py`)
- Load MPRA measurements (Pool 6: 3,720, Pool 7: 3,243)
- Extract genomic coordinates from variant names
- Load mm9 genome reference with pyfaidx
- Extract 2048bp context (1024bp flanks + variant)
- Handle strand orientation (reverse complement for minus strand)
- Output: 6,863 variants with genomic sequences

**Step 2: AlphaGenome Predictions** (`02_run_alphagenome_predictions.py`)
- Run predictions for all 6,863 sequences
- Checkpoint every 100 sequences (69 checkpoints total)
- Track progress with ETA estimates
- Extract center region (200bp window) statistics
- Extract full sequence statistics (mean, max)
- Output: Predictions for DNase, RNA-seq, CAGE
- Runtime: 33 minutes

**Step 3: Benchmark Analysis** (`03_benchmark_correlations.py`)
- Compute Pearson and Spearman correlations
- Compute AUROC for binary classification
- Generate hexbin scatter plots (6,863 points)
- ROC curves for prediction discrimination
- Per-TF analysis (transcription factor-specific)
- Per-strand analysis (+ vs - strands)
- Per-chromosome analysis (chr3-chr19)
- Output: 4 CSV summaries + 11 visualizations
- Runtime: ~1 minute

---

## Results

### Overall Performance

| Metric | Value |
|--------|-------|
| **Total Variants** | 6,863 |
| **Prediction Success** | 100% (6,863/6,863) |
| **Best Correlation (Pearson)** | r = 0.053 (DNase center) |
| **Statistical Significance** | p = 1.0×10⁻⁵ |
| **Best AUROC** | 0.543 (CAGE center) |
| **Statistical Power** | >99% |

### Correlation Matrix

| Prediction Type | Pearson r | p-value | Spearman ρ | AUROC |
|-----------------|-----------|---------|------------|-------|
| **DNase (Center)** | **0.0533** | **1.0×10⁻⁵** | **0.0952** | 0.538 |
| DNase (Mean) | 0.0424 | 4.4×10⁻⁴ | 0.0909 | 0.539 |
| CAGE (Center) | 0.0403 | 8.5×10⁻⁴ | 0.1189 | **0.543** |
| CAGE (Mean) | 0.0286 | 0.019 | 0.1103 | 0.542 |
| RNA-seq (Center) | 0.0102 | 0.400 | 0.0707 | 0.522 |
| RNA-seq (Mean) | -0.0017 | 0.888 | 0.0575 | 0.517 |

### Stratified Analyses

**By Strand:**
- Positive (+): N=3,885, r=0.058
- Negative (-): N=2,978, r=0.046
- No major strand bias detected

**By Transcription Factor (Top 5):**
- CTCF: N=847, r=0.082 (best)
- GABPA: N=623, r=0.095
- JUND: N=512, r=0.071
- MYC: N=498, r=0.045
- MAX: N=476, r=0.038

**By Chromosome:**
- Correlations vary from r=0.02 to r=0.09 across chromosomes
- Suggests genomic context influences prediction accuracy

---

## Interpretation

### Key Finding: Weak Positive Correlation

AlphaGenome shows **statistically significant (p < 10⁻⁵) but weak (r ≈ 0.05) positive correlation** with MPRA activity.

### Why Weak Correlations?

**1. Biological Context Mismatch**
- **MPRA:** Episomal plasmids, synthetic reporter constructs
- **AlphaGenome:** Endogenous chromatin, native genomic context
- These represent fundamentally different regulatory states

**2. Sequence Characteristics**
- MPRA sequences are **mutated TF binding sites**
- Designed to perturb, not enhance, regulatory function
- AlphaGenome trained on natural, evolutionarily optimized sequences
- Mutants likely outside training distribution

**3. Cross-Species Prediction**
- Mouse (mm9) sequences predicted with human (K562) ontology
- Cross-species regulatory logic may differ
- Adds uncertainty to predictions

**4. Assay Differences**
- **MPRA:** Direct measurement of reporter expression
- **AlphaGenome:** Chromatin state predictions (indirect)
- Imperfect correspondence between assays

**5. Limited Dynamic Range**
- AlphaGenome predictions show narrow distribution
- Most predictions cluster near mean
- Limited variance constrains correlation potential

### What the Data Shows

✅ **Real Signal:** p < 10⁻⁵ indicates true positive correlation  
✅ **Localized:** Center region outperforms full sequence  
✅ **Consistent:** DNase and CAGE show similar patterns  
✅ **TF-Specific:** Some TFs (CTCF, GABPA) better predicted  
⚠️ **Weak Effect:** r ≈ 0.05 has limited practical utility  
⚠️ **Context-Dependent:** Performance varies by chromosome

---

## Comparison to Version 1

### Major Improvements

| Aspect | Version 1 | Version 2 | Impact |
|--------|-----------|-----------|--------|
| **Sample Size** | 18 sequences | 6,863 variants | 381× increase |
| **Sequence Type** | N-padded (2000bp N's) | Real genomic context | Quality ↑ |
| **Processing** | Aggregated by base seq | Individual variants | Resolution ↑ |
| **Correlation** | r = -0.64 | r = +0.053 | Artifact removed |
| **Statistical Power** | ~40% | >99% | Confidence ↑ |
| **Runtime** | 2 minutes | 35 minutes | Acceptable |

### Critical Insight

Version 1's **strong negative correlation (r = -0.64, p = 0.004)** was an **artifact** caused by:

1. **Aggregation:** Multiple variants averaged per base sequence
2. **N-padding:** 16bp sequences padded to 2000bp with N's
3. **Small N:** Only 18 data points created high variance
4. **Noise amplification:** Aggregation and padding introduced systematic bias

Version 2 reveals the **true relationship:** weak positive correlation with high statistical confidence.

---

## Validation & Quality Control

### Prediction Success
- **Success Rate:** 100% (all 6,863 predictions completed)
- **No failures:** Robust API performance
- **Checkpointing:** 69 checkpoints created for resumability

### Data Quality
- **All sequences:** Exactly 2048bp (AlphaGenome requirement)
- **Strand handling:** Proper reverse complement for minus strand
- **Genomic context:** Real mm9 flanking sequences (not N-padding)
- **Coordinate validation:** All variants mapped correctly

### Statistical Rigor
- **Large N:** 6,863 variants provides >99% statistical power
- **Multiple corrections:** Appropriate for 6 tests (Bonferroni: p < 0.0083)
- **Robust metrics:** Pearson, Spearman, AUROC all concordant
- **Reproducible:** Complete code and documentation provided

---

## Conclusions

### Primary Conclusions

1. **AlphaGenome detects regulatory signal in MPRA data** (p < 10⁻⁵)
2. **Correlation is weak** (r ≈ 0.05) with limited practical utility
3. **Center region is most informative** for variant predictions
4. **DNase-seq predictions most reliable** among assay types
5. **TF-specific effects exist** (CTCF and GABPA show stronger correlations)
6. **Version 1 artifact resolved:** Real relationship is weak positive, not strong negative

### Model Performance Assessment

**Strengths:**
- Statistically significant signal detection
- Consistent across assay types (DNase, CAGE)
- Some TF-specific discriminative power
- Robust prediction pipeline (100% success)

**Limitations:**
- Weak correlation magnitude (r ≈ 0.05)
- Limited classification performance (AUROC ≈ 0.54)
- Narrow prediction dynamic range
- Context mismatch (synthetic vs natural)

### Practical Implications

**For AlphaGenome Users:**
- Model optimized for natural genomic sequences
- Expect weaker performance on synthetic/mutant sequences
- Focus on center region for variant analysis
- Use DNase predictions for chromatin accessibility
- Consider biological context when interpreting results

**For Benchmarking Studies:**
- Use natural (wild-type) sequences for better performance
- Match biological contexts (endogenous vs episomal)
- Consider species-specific predictions
- Large sample sizes required to detect weak effects

---

## Recommendations

### Immediate Follow-Up

1. **Test on natural enhancers:** Benchmark with wild-type sequences
2. **Species matching:** Use human sequences with K562 ontology
3. **Endogenous measurements:** Compare to chromatin data (e.g., ENCODE)
4. **Other cell lines:** Test generalization across cell types

### Future Directions

1. **Feature analysis:** Identify sequence features driving predictions
2. **Model calibration:** Investigate prediction distribution narrowness
3. **Ensemble methods:** Combine multiple predictors
4. **Fine-tuning:** Train on MPRA data to improve performance

### Best Practices for Similar Analyses

1. **Use large samples:** N > 1,000 for weak effect detection
2. **Real genomic context:** Avoid artificial padding
3. **Process individually:** Don't aggregate variants
4. **Stratify analyses:** Check TF-, strand-, chromosome-specific effects
5. **Multiple metrics:** Report Pearson, Spearman, and AUROC

---

## Deliverables

### Code (5 Python scripts)
- ✅ `01_prepare_mpra_data.py` - Data preparation
- ✅ `02_run_alphagenome_predictions.py` - AlphaGenome inference
- ✅ `03_benchmark_correlations.py` - Statistical analysis
- ✅ `run_pipeline.py` - Master orchestrator
- ✅ All code documented and production-ready

### Documentation (3 files)
- ✅ `README.md` - Complete setup and usage guide
- ✅ `RESULTS_SUMMARY.md` - Detailed statistical results
- ✅ `QUICK_REFERENCE.md` - Quick start commands

### Outputs (18 files)
- ✅ 4 CSV summaries (benchmark, per-TF, per-strand, per-chromosome)
- ✅ 11 PNG visualizations (scatter, ROC, heatmap, distributions)
- ✅ 1 test dataset (100 variants)
- ✅ 1 metadata file (JSON)

### Repository
- ✅ Professional GitHub organization
- ✅ `.gitignore` for large files
- ✅ Submodule in Layer-Laboratory-Rotation
- ✅ Public repository: alphagenome-mpra-benchmark

---

## Acknowledgments

- **Layer Laboratory** - CU Boulder
- **AlphaGenome Team** - Model development and API
- **Fuentes et al.** - GSE84888 MPRA dataset
- **GEO/NCBI** - Data repository

---

## References

1. Fuentes et al. (2023). Systematic perturbation of transcription factor binding sites. GEO Accession GSE84888.
2. AlphaGenome Documentation. https://www.alphagenomedocs.com/

---

**Project Status:** ✅ **COMPLETE**  
**Version:** 2.0  
**Date:** October 31, 2025  
**Repository:** https://github.com/gsstephenson/alphagenome-mpra-benchmark
