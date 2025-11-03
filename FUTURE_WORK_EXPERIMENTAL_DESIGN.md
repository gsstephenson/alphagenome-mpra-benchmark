# Experimental Design: Endogenous Variant Validation of AlphaGenome

**Proposed Study:** AlphaGenome Benchmark on Naturally Occurring Variants with Native Chromatin Measurements  
**Date:** November 3, 2025  
**Based on findings from:** GSE84888 MPRA edge case analysis (Version 3.0)

---

## 🎯 Executive Summary

### Why This Experiment is Essential

The GSE84888 MPRA analysis revealed that **episomal context, not synthetic mutations, limits AlphaGenome's predictive performance**. To properly validate the model's capabilities on its intended use case, we need to test on:

1. **Naturally occurring variants** (not synthetic perturbations)
2. **Endogenous chromatin measurements** (not episomal plasmid reporters)
3. **Species-matched predictions** (human variants + human model + human cell line)
4. **Genomic context preserved** (variants in native chromosomal locations)

### Expected Impact

- **Addresses primary limitation** identified in GSE84888 analysis
- **Fair test** of AlphaGenome's design goals
- **Clinically relevant** (disease-associated variants)
- **Publishable** (fills gap in field's validation standards)
- **Expected improvement**: r = 0.09 (MPRA) → r = 0.5-0.7 (endogenous)

---

## 📊 Experimental Design Overview

### Study Title
**"Systematic Validation of AlphaGenome Predictions Using Naturally Occurring Variants with Allele-Specific Chromatin Measurements"**

### Central Hypothesis
**AlphaGenome's chromatin accessibility predictions will show strong correlations (r > 0.5) with endogenous measurements when tested on naturally occurring variants in their native genomic context.**

### Key Contrasts with GSE84888

| Aspect | GSE84888 (Edge Case) | Proposed Study (Proper Test) |
|--------|---------------------|------------------------------|
| **Variants** | Synthetic mutations | Natural SNPs/indels |
| **Context** | Episomal plasmids | Native chromosomes |
| **Species** | Mouse→Human | Human→Human |
| **Chromatin** | MPRA reporter | ATAC-seq/DNase-seq |
| **Selection** | Designed perturbations | Evolutionary filtered |
| **Expected r** | 0.05-0.09 (observed) | 0.5-0.7 (predicted) |

---

## 🔬 Detailed Experimental Plan

### Phase 1: Dataset Selection and Integration

#### Primary Dataset: GTEx eQTLs + ENCODE Chromatin (RECOMMENDED)

**Why this combination?**
1. **GTEx**: Largest resource of naturally occurring regulatory variants
   - 838 donors, 49 tissues
   - ~1M significant eQTLs identified
   - Expression quantitative trait loci = proven regulatory function
   
2. **ENCODE**: Comprehensive chromatin maps
   - K562 has extensive DNase-seq, ATAC-seq, ChIP-seq
   - Multiple replicates for statistical power
   - Standardized processing pipelines

**Integration Strategy:**

```
Step 1: Select variants
- GTEx eQTLs in K562-relevant genes (blood/hematopoietic)
- Filter: MAF > 0.05 (common variants)
- Filter: |effect size| > 0.2 (strong regulatory effects)
- Filter: Within DNase hypersensitive sites (DHSs)
- Expected N: ~5,000-10,000 variants

Step 2: Obtain chromatin measurements
- ENCODE K562 DNase-seq (ENCSR000EOT)
- ENCODE K562 ATAC-seq (ENCSR868FGK)
- Process allele-specific accessibility if possible
- Quantify: signal intensity at variant position ± 1KB

Step 3: AlphaGenome predictions
- Extract 2048bp windows centered on each variant
- Predict: DNase, RNA-seq, CAGE for both alleles
- Calculate: Δ prediction between alleles
- Ontology: K562 (EFO:0002067)

Step 4: Statistical analysis
- Correlate: Δ AlphaGenome vs Δ chromatin accessibility
- Correlate: Δ AlphaGenome vs gene expression effect size
- Compare: performance vs Enformer, Basenji2, DeepSEA
```

#### Alternative Dataset: Allele-Specific Chromatin QTLs

**Source:** Kumasaka et al. (2019) Nature Genetics  
**Description:** 14,179 variants with allele-specific chromatin accessibility

```
Advantages:
- Direct allele-specific measurements (gold standard)
- Proven causal variants (not just correlative)
- Published dataset (readily available)
- Multiple cell types available

Disadvantages:
- Smaller N than GTEx
- May not have K562 specifically
- Need to access controlled data
```

#### Validation Dataset: ClinVar Pathogenic Variants

**Purpose:** Test clinical relevance

```
Select:
- Pathogenic variants in regulatory regions
- Benign variants as negative controls
- Matched by position and MAF

Question: Can AlphaGenome distinguish pathogenic from benign
regulatory variants based on predicted chromatin disruption?

Expected outcome: AUROC > 0.7 for pathogenic classification
```

---

### Phase 2: Technical Implementation

#### 2.1 Data Processing Pipeline

```python
# Pseudocode for pipeline

# Step 1: Variant extraction
variants = load_gtex_eqtls()
variants = filter_by_maf(variants, min_maf=0.05)
variants = filter_by_effect_size(variants, min_abs_beta=0.2)
variants = intersect_with_k562_dhs(variants)
# Expected: 5,000-10,000 variants

# Step 2: Sequence extraction
for variant in variants:
    ref_seq = extract_sequence(hg38, variant.chr, 
                                variant.pos - 1024, 
                                variant.pos + 1024)
    alt_seq = introduce_variant(ref_seq, variant)
    sequences.append({'variant_id': variant.id,
                      'ref_seq': ref_seq,
                      'alt_seq': alt_seq})

# Step 3: AlphaGenome predictions
for seq_pair in sequences:
    ref_pred = alphagенome_predict(seq_pair['ref_seq'], 
                                    ontology='K562')
    alt_pred = alphagенome_predict(seq_pair['alt_seq'], 
                                    ontology='K562')
    delta_pred = alt_pred - ref_pred
    predictions.append(delta_pred)

# Step 4: Chromatin measurements
for variant in variants:
    ref_signal = get_dnase_signal(variant, allele='ref')
    alt_signal = get_dnase_signal(variant, allele='alt')
    delta_observed = alt_signal - ref_signal
    observations.append(delta_observed)

# Step 5: Statistical analysis
correlation = pearsonr(predictions, observations)
# Expected: r > 0.5, p < 1e-100
```

#### 2.2 Computational Requirements

```
Predictions needed:
- N variants: ~10,000
- 2 alleles per variant: 20,000 sequences
- Rate: ~4 sequences/second
- Total time: ~1.4 hours (with checkpointing)

Storage:
- Sequences: ~50 MB
- Predictions: ~5 MB
- Chromatin data: ~500 MB (processed)
- Total: <1 GB

Compute:
- Same infrastructure as GSE84888 (conda env)
- API access to AlphaGenome
- Standard workstation sufficient
```

#### 2.3 Quality Control Measures

```
Pre-analysis QC:
✓ Verify all variants are in hg38 coordinates
✓ Check sequence extraction (no N's, correct strand)
✓ Validate chromatin signal coverage (no gaps)
✓ Confirm MAF matches between datasets

Post-prediction QC:
✓ Check prediction distributions (no outliers)
✓ Verify both alleles predicted successfully
✓ Compare ref allele predictions to genome-wide baseline
✓ Test for batch effects (if multiple runs)

Statistical QC:
✓ Test for population structure confounding
✓ Check for linkage disequilibrium effects
✓ Validate assumptions (normality, homoscedasticity)
✓ Multiple testing correction (Bonferroni/FDR)
```

---

### Phase 3: Analysis Plan

#### 3.1 Primary Analysis: Correlation Assessment

**Primary Endpoint:** Pearson correlation between Δ AlphaGenome prediction and Δ chromatin accessibility

```
Analysis 1: Overall performance
- Correlation: All variants pooled
- Expected: r = 0.5-0.7 (strong positive)
- Power: N=10,000 gives >99% power for r>0.3

Analysis 2: Stratified by effect size
- Q1 (small effects): r = ?
- Q2-Q3 (moderate): r = ?
- Q4 (large effects): r = ?
- Hypothesis: Larger effects → stronger correlation

Analysis 3: Stratified by genomic context
- Promoters: r = ?
- Enhancers: r = ?
- Insulators: r = ?
- Gene bodies: r = ?
- Hypothesis: Promoters show strongest correlation
```

#### 3.2 Secondary Analyses

**A. Comparison to Gene Expression**

```
Question: Do AlphaGenome predictions correlate with 
          actual gene expression changes (eQTL effect size)?

Method:
- Match variants to target genes
- Correlate: Δ AlphaGenome vs GTEx effect size (beta)
- Interpretation: Does chromatin prediction explain expression?

Expected: r = 0.3-0.5 (moderate, mediated by chromatin)
```

**B. Distance Decay Analysis**

```
Question: How far from variant does AlphaGenome prediction change?

Method:
- For each variant, measure Δ prediction at:
  - 0 bp (variant position)
  - ±100 bp, ±500 bp, ±1000 bp
- Plot: Effect size vs distance
- Fit: Exponential decay model

Expected: Half-maximum distance ~200-500 bp
Interpretation: Effective "influence radius" of variants
```

**C. Motif Disruption Analysis**

```
Question: Are large prediction changes explained by TF motif disruption?

Method:
- Scan variants for known TF motifs (JASPAR database)
- Classify: motif-disrupting vs non-motif
- Compare: Δ prediction between groups

Expected: Motif-disrupting shows 2-3× larger Δ prediction
```

**D. Cell-Type Specificity**

```
Question: Are predictions specific to K562 biology?

Method:
- Re-run predictions with different ontologies:
  - K562 (blood)
  - HepG2 (liver)
  - H1-ESC (stem cells)
- Correlate each with K562 chromatin measurements
- Compare correlation strengths

Expected: K562 predictions >> other cell types (r_K562 = 0.6, r_other = 0.3)
Validates: Cell-type-specific predictions
```

#### 3.3 Benchmarking Against Other Models

```
Compare AlphaGenome to:

1. Enformer (Avsec et al. 2021)
   - Transformer architecture
   - 200KB sequence context
   - CAGE, DNase, histone predictions

2. Basenji2 (Kelley et al. 2018)
   - CNN architecture
   - 128KB sequence context
   - Multi-task prediction

3. DeepSEA (Zhou & Troyanskaya 2015)
   - CNN architecture
   - 1KB sequence context
   - 919 chromatin features

Method:
- Same variant set for all models
- Same evaluation metrics
- Report: correlation, AUROC, MAE, R²

Expected AlphaGenome performance:
- Better than DeepSEA (larger context)
- Comparable to Basenji2
- Slightly behind Enformer (largest context)
```

---

### Phase 4: Validation and Robustness

#### 4.1 Cross-Validation Strategy

```
5-Fold Cross-Validation:
- Split variants by chromosome
- Train-free evaluation (all models pre-trained)
- Ensure no data leakage between folds
- Report: mean ± SD correlation across folds

Chromosome holdout:
- Test on chr1, chr2, chr3 separately
- Check for chromosome-specific biases
```

#### 4.2 Negative Controls

```
Control 1: Scrambled sequences
- Randomly shuffle 2048bp windows
- Predict with AlphaGenome
- Expected: No correlation with chromatin (r ~ 0)

Control 2: Synonymous variants
- Variants that don't change regulatory elements
- Expected: Minimal Δ prediction (<10% of regulatory variants)

Control 3: Permutation test
- Randomly shuffle variant-chromatin pairs
- Re-calculate correlation 10,000 times
- Empirical p-value calculation
```

#### 4.3 Sensitivity Analyses

```
Test robustness to:

1. Variant frequency
   - Rare (MAF < 0.01)
   - Common (MAF > 0.05)
   - Does model work across frequency spectrum?

2. Genomic context
   - GC-rich regions
   - Repeat-masked regions
   - Gene-dense vs gene-desert

3. Chromatin state
   - Active promoters (H3K4me3+)
   - Active enhancers (H3K27ac+)
   - Poised enhancers (H3K4me1+)
   - Heterochromatin (H3K9me3+)
```

---

## 📈 Expected Outcomes and Interpretation

### Scenario 1: Strong Correlation (r = 0.5-0.7) ✅ HYPOTHESIS SUPPORTED

**Interpretation:**
- AlphaGenome successfully predicts endogenous chromatin accessibility
- Episomal context was indeed the limitation in GSE84888
- Model is validated for regulatory variant interpretation

**Impact:**
- ⭐⭐⭐ High-impact publication (Nature Methods, Genome Research)
- Establishes AlphaGenome as gold standard for variant effect prediction
- Clinical applications: pathogenic variant classification

**Next steps:**
- Expand to more cell types
- Test on disease-associated variants
- Develop interpretation tools (feature attribution)

---

### Scenario 2: Moderate Correlation (r = 0.3-0.5) ~ PARTIAL SUPPORT

**Interpretation:**
- AlphaGenome captures signal better than MPRA (r=0.09)
- But still room for improvement
- May need larger sequence context (>2048bp)

**Impact:**
- ⭐⭐ Solid publication (PLOS Computational Biology, NAR)
- Model useful but with caveats
- Identifies areas for model improvement

**Next steps:**
- Analyze failure modes (where predictions are worst)
- Test if Enformer (200KB context) performs better
- Consider fine-tuning on variant data

---

### Scenario 3: Weak Correlation (r < 0.3) ❌ HYPOTHESIS REJECTED

**Interpretation:**
- Fundamental model limitations beyond context
- May not capture variant-specific effects well
- Context window (2048bp) may be too large for local variants

**Impact:**
- ⭐ Important negative result (eLife, G3)
- Identifies model limitations clearly
- Informs future model development

**Next steps:**
- Deep dive into failure modes
- Feature attribution to understand model behavior
- Consider hybrid approaches (AlphaGenome + motif models)

---

## 💡 Why This Experiment is Worthwhile

### Scientific Value

#### 1. **Addresses Critical Gap in Field**
```
Current state:
- Genomic models trained on massive datasets
- But validation mostly on synthetic data
- Real-world performance unclear

This study provides:
- First comprehensive validation on natural variants
- Direct measurement of clinical utility
- Benchmark for future models
```

#### 2. **Resolves GSE84888 Ambiguity**
```
GSE84888 showed:
- Weak correlations (r = 0.09)
- But unclear if due to:
  a) Model failure
  b) Episomal context mismatch
  c) Cross-species issues

This study answers:
- Test (a) directly with proper benchmark
- Expected outcome: r increases 5-7× (0.09 → 0.5-0.7)
- Confirms: Context was the issue, not the model
```

#### 3. **Establishes Validation Standards**
```
Impact on field:
- Defines what "proper validation" means
- MPRA useful for mechanisms, not model validation
- Future models must meet this standard
- Raises bar for genomics methods
```

### Clinical Value

#### 4. **Variant Interpretation Pipeline**
```
Applications:
- Classify pathogenic regulatory variants
- Prioritize variants for functional follow-up
- Predict drug response (pharmacogenomics)
- Personalized medicine applications

Example use case:
Patient has VUS (variant of uncertain significance)
→ AlphaGenome predicts chromatin disruption
→ Reclassify as likely pathogenic
→ Inform clinical decision-making
```

#### 5. **Disease Mechanism Insights**
```
For each disease-associated variant:
- Predict chromatin changes
- Identify affected TF binding
- Map downstream gene targets
- Propose mechanistic hypotheses

Example: Diabetes GWAS variant in FTO locus
→ AlphaGenome shows chromatin closing
→ Affects IRX3 gene 1MB away
→ Explains obesity association
```

### Practical Value

#### 6. **Computationally Efficient**
```
Resources needed:
- Time: ~2 hours prediction + 1 week analysis
- Cost: Minimal (API access + compute)
- Data: Publicly available
- Personnel: 1 person can complete

Return on investment: HIGH
- Fast turnaround
- Low cost
- High impact potential
```

#### 7. **Reproducible and Extensible**
```
Design features:
- All data publicly available
- Code reusable (from GSE84888 pipeline)
- Can extend to other cell types
- Community resource

Enables:
- Other labs to validate their models
- Systematic comparison across models
- Iterative improvement
```

### Strategic Value

#### 8. **Positions Lab as Leader**
```
Demonstrates:
- Rigorous validation methodology
- Understanding of model limitations
- Practical applications focus
- Bridge between ML and biology

Attracts:
- Collaborations with ML groups
- Funding for method development
- High-profile publications
- Clinical translation opportunities
```

---

## 🎯 Success Criteria

### Primary Success Metrics

| Metric | Minimum Success | Target | Stretch Goal |
|--------|----------------|--------|--------------|
| **Pearson r** | > 0.3 | > 0.5 | > 0.7 |
| **p-value** | < 0.001 | < 1e-10 | < 1e-100 |
| **AUROC (path/benign)** | > 0.6 | > 0.7 | > 0.8 |
| **N variants** | > 5,000 | > 10,000 | > 20,000 |
| **Publication tier** | PLOS CB | Genome Res | Nature Methods |

### Secondary Success Metrics

- ✅ Outperform DeepSEA (r > 0.3)
- ✅ Comparable to Basenji2 (r within 10%)
- ✅ Cell-type specificity demonstrated
- ✅ Distance decay quantified
- ✅ Motif disruption enrichment shown

---

## 📅 Timeline and Milestones

### Month 1: Data Preparation
- Week 1-2: Download and process GTEx eQTLs
- Week 3: Download and process ENCODE chromatin data
- Week 4: Quality control and variant filtering

### Month 2: Predictions
- Week 1: Extract sequences for all variant pairs
- Week 2-3: Run AlphaGenome predictions (with checkpointing)
- Week 4: Quality control of predictions

### Month 3: Analysis
- Week 1: Primary correlation analysis
- Week 2: Secondary analyses (stratification, etc.)
- Week 3: Benchmark against other models
- Week 4: Validation and robustness checks

### Month 4: Manuscript
- Week 1-2: Figure generation and refinement
- Week 3: Manuscript writing
- Week 4: Internal review and submission

**Total duration: 4 months** (part-time work)

---

## 💰 Resource Requirements

### Personnel
- 1 graduate student or postdoc (20-40% effort)
- PI oversight (5% effort)

### Computational
- Same infrastructure as GSE84888
- Existing conda environment
- AlphaGenome API access
- Standard workstation sufficient

### Budget
- Data download: $0 (public)
- Compute: $0 (existing resources)
- AlphaGenome API: $0 (assuming free academic access)
- Total: **$0 direct costs**

### Data Storage
- ~1 GB total (manageable)
- Can use existing infrastructure

---

## 🔗 Integration with GSE84888 Study

### How This Builds on Previous Work

```
GSE84888 (Edge Case Test):
- Identified: Episomal context as primary limitation
- Showed: Model robustness to synthetic sequences
- Revealed: PPARγ paradox (context vs motif)

This Study (Proper Validation):
- Addresses: Episomal limitation directly
- Tests: Model on intended use case
- Validates: Clinical applications

Together:
- Complete picture of model capabilities
- Both edge cases and typical use
- Publication narrative: "From adversarial testing to clinical validation"
```

### Combined Publication Strategy

**Option 1: Two Papers**
```
Paper 1 (GSE84888): "Edge Case Analysis of AlphaGenome"
- Focus: Model robustness testing
- Venue: Bioinformatics, BMC Bioinformatics

Paper 2 (This study): "Clinical Validation of AlphaGenome"
- Focus: Natural variant predictions
- Venue: Nature Methods, Genome Research
```

**Option 2: Single Comprehensive Paper**
```
Title: "Systematic Validation of AlphaGenome: From Adversarial
        Testing to Clinical Applications"

Structure:
- Part 1: GSE84888 (establishes limitations)
- Part 2: Natural variants (addresses limitations)
- Part 3: Clinical applications (ClinVar validation)

Venue: Nature Methods, Nature Communications
Impact: Higher profile due to completeness
```

---

## 📚 Key References and Prior Art

### Similar Studies to Learn From

1. **Enformer validation** (Avsec et al. 2021, Nature Methods)
   - Used: MPRA + endogenous ChIP-seq
   - Found: r = 0.76 on TSS activity
   - Lesson: Need large context (200KB)

2. **Basenji2** (Kelley et al. 2018, Genome Research)
   - Used: Roadmap Epigenomics data
   - Found: r = 0.65 average across marks
   - Lesson: Cell-type specificity crucial

3. **DeepSEA** (Zhou & Troyanskaya 2015, Nature Methods)
   - Used: ENCODE chromatin features
   - Found: AUROC = 0.94 for classification
   - Lesson: Classification easier than regression

4. **ExPecto** (Zhou et al. 2018, Nature Genetics)
   - Used: GTEx eQTLs
   - Found: r = 0.39 for expression prediction
   - Lesson: Chromatin → expression is noisy

### Datasets to Use

1. **GTEx v8**: 838 donors, 17,382 samples
   - Portal: gtexportal.org
   - Format: VCF + expression matrices
   - Access: Public (dbGaP for genotypes)

2. **ENCODE K562**: Extensive chromatin data
   - Portal: encodeproject.org
   - Datasets: ENCSR000EOT (DNase), ENCSR868FGK (ATAC)
   - Format: bigWig, BAM
   - Access: Public

3. **ClinVar**: 1.6M variants (Dec 2024)
   - Portal: ncbi.nlm.nih.gov/clinvar
   - Classifications: Pathogenic, benign, VUS
   - Format: VCF
   - Access: Public

---

## 🎓 Expected Publications

### Primary Paper

**Title**: "Validation of AlphaGenome Chromatin Predictions on Naturally Occurring Regulatory Variants"

**Authors**: [Your name], [Collaborators], [PI]

**Target Journal**: Nature Methods (IF: 36.1) or Genome Research (IF: 7.0)

**Expected Citations**: 50-100 in first year (high impact methods paper)

### Significance Statements

**For high-tier journal (Nature Methods):**
```
"Genomic deep learning models are increasingly used for variant 
interpretation, but validation on their intended use cases has been 
limited. Here we systematically evaluate AlphaGenome's chromatin 
accessibility predictions on 10,000 naturally occurring regulatory 
variants with matched endogenous measurements. We demonstrate strong 
predictive performance (r = 0.6) for native chromatin changes, 
contrasting with weak correlations on episomal reporters (r = 0.09). 
Our results establish benchmarking standards for regulatory variant 
prediction and enable clinical interpretation of non-coding mutations."
```

**For specialized journal (Genome Research):**
```
"We present a comprehensive validation of AlphaGenome predictions using
GTEx eQTLs matched to ENCODE chromatin accessibility data. Our analysis
of 10,000 variants reveals that model predictions strongly correlate
with endogenous chromatin changes (r = 0.6) but not with episomal
MPRA measurements (r = 0.09), resolving ambiguity about model 
performance. These findings establish AlphaGenome as a reliable tool
for regulatory variant interpretation and define standards for 
validating genomic prediction models."
```

---

## ✅ Conclusion: Why This Experiment Should Be Done

### The Bottom Line

**GSE84888 told us WHAT doesn't work (MPRA episomal context)**  
**This study will tell us WHAT DOES work (endogenous chromatin)**

### The Case for Investment

1. **Low risk**: Uses established methods and public data
2. **High reward**: Nature Methods-level publication potential
3. **Fast**: 4 months to completion
4. **Cheap**: ~$0 direct costs
5. **Impactful**: Establishes validation standards for field
6. **Enables**: Clinical applications of AlphaGenome
7. **Scalable**: Framework applies to any genomic model

### The Scientific Opportunity

This is the **natural next step** after GSE84888:
- We identified the problem (episomal context)
- We proposed the solution (endogenous variants)
- We have the tools (AlphaGenome API, existing code)
- We have the data (GTEx, ENCODE - public)
- We have the expertise (proven by GSE84888 completion)

**This experiment will definitively answer**: 
*"Does AlphaGenome work for its intended purpose?"*

Current answer: **"We don't know—only tested on edge cases"**  
After this study: **"Yes, r = 0.6 on natural variants" (hopefully!)**

---

## 📧 Next Steps to Initiate

### Immediate Actions (Week 1)

1. ✅ Review this design with PI
2. ✅ Check AlphaGenome API access for larger studies
3. ✅ Download GTEx eQTL summary statistics
4. ✅ Download ENCODE K562 chromatin bigWigs
5. ✅ Adapt GSE84888 code for new analysis

### Funding Opportunities (if needed)

- NIH R21 (exploratory): "Validation of AI-driven regulatory variant prediction"
- NSF CAREER: "Computational methods for non-coding variant interpretation"
- Foundation grants: March of Dimes, American Heart Association
- Industry partnerships: 23andMe, Color Genomics

### Collaboration Opportunities

- **Computational**: Enformer team (DeepMind/Calico)
- **Clinical**: Medical genetics labs (variant interpretation)
- **Data**: GTEx consortium, ENCODE consortium
- **Method**: Pritchard lab (DeepSEA), Troyanskaya lab

---

**Status**: Ready to initiate upon approval  
**Risk level**: Low  
**Expected impact**: High  
**Recommendation**: Proceed

---

*Document prepared: November 3, 2025*  
*Based on: GSE84888 MPRA Analysis (Version 3.0)*  
*Next update: Upon project initiation*
