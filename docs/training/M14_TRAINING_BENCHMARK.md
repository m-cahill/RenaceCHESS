# M14 Training Benchmark Report

**Document Version:** 1.0.0  
**Status:** 📋 TEMPLATE (awaiting benchmark execution)  
**Milestone:** M14 — TRAIN-PACK-001  

---

## Purpose

This document provides a template for recording training benchmark results on local hardware. It establishes the format and requirements for reproducible training throughput measurement.

**Important:** This document is a TEMPLATE. Actual benchmark results should be recorded by running `scripts/benchmark_training.py` and documenting the output here or in a follow-on document.

---

## Prerequisites

Before running the benchmark:

1. **Dataset manifest** (v2 format) must exist at a known path
2. **Frozen eval manifest** must exist for contamination protection
3. **Local GPU** is recommended but not required (CPU fallback available)
4. **Python environment** with `renacechess[dev]` installed

---

## Hardware Specification Template

Fill in this section after running the benchmark:

| Attribute | Value |
|-----------|-------|
| **GPU Model** | `<e.g., NVIDIA RTX 5090>` |
| **GPU VRAM** | `<e.g., 32 GB GDDR7>` |
| **CPU** | `<e.g., AMD Ryzen 9 7950X>` |
| **RAM** | `<e.g., 64 GB DDR5>` |
| **PyTorch Version** | `<e.g., 2.2.0+cu121>` |
| **Python Version** | `<e.g., 3.12.1>` |
| **OS** | `<e.g., Windows 11 Pro>` |

---

## Dataset Information Template

| Attribute | Value |
|-----------|-------|
| **Manifest Path** | `<path to manifest.json>` |
| **Manifest Digest** | `<16-char hex digest>` |
| **Total Records** | `<number of training records>` |
| **Frozen Eval Overlap** | `PASS` / `FAIL` |

---

## Benchmark Configuration

The following settings were used for benchmarking:

| Parameter | Value |
|-----------|-------|
| **Max Samples** | 1000 (default) |
| **Max Steps** | 100 (default) |
| **Seed** | 42 |
| **Batch Size** | 1 (per-sample for timing accuracy) |

---

## Policy Head Benchmark Results Template

| Metric | Value |
|--------|-------|
| **Model Type** | `BaselinePolicyV1` |
| **Samples Processed** | `<number>` |
| **Steps Completed** | `<number>` |
| **Total Time (seconds)** | `<value>` |
| **Samples/Second** | `<value>` |
| **Step Time (mean, ms)** | `<value>` |
| **Step Time (p95, ms)** | `<value>` |
| **GPU Memory Peak (MB)** | `<value>` or `N/A` |

### Training Time Projections (Policy)

Based on benchmark results, projected training times:

| Dataset Size | Epochs | Estimated Time |
|--------------|--------|----------------|
| 10K positions | 10 | `<calculate>` |
| 100K positions | 10 | `<calculate>` |
| 1M positions | 10 | `<calculate>` |
| 10M positions | 10 | `<calculate>` |

*Formula:* `time = (dataset_size × epochs) / samples_per_second`

---

## Outcome Head Benchmark Results Template

| Metric | Value |
|--------|-------|
| **Model Type** | `OutcomeHeadV1` |
| **Samples Processed** | `<number>` |
| **Steps Completed** | `<number>` |
| **Total Time (seconds)** | `<value>` |
| **Samples/Second** | `<value>` |
| **Step Time (mean, ms)** | `<value>` |
| **Step Time (p95, ms)** | `<value>` |
| **GPU Memory Peak (MB)** | `<value>` or `N/A` |

### Training Time Projections (Outcome Head)

Based on benchmark results, projected training times:

| Dataset Size | Epochs | Estimated Time |
|--------------|--------|----------------|
| 10K positions | 10 | `<calculate>` |
| 100K positions | 10 | `<calculate>` |
| 1M positions | 10 | `<calculate>` |
| 10M positions | 10 | `<calculate>` |

---

## Reproduction Instructions

To reproduce these benchmark results:

```bash
# 1. Install RenaceCHESS with dev dependencies
pip install -e ".[dev]"

# 2. Run the benchmark script
python scripts/benchmark_training.py \
    --manifest <path-to-manifest.json> \
    --frozen-eval-manifest <path-to-frozen-eval-manifest.json> \
    --output benchmark_results.json

# 3. Review the JSON output and update this document
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--manifest` | Path to dataset manifest v2 | Required |
| `--frozen-eval-manifest` | Path to frozen eval manifest | Required |
| `--output` | Path for JSON results | None |
| `--max-samples` | Maximum samples to benchmark | 1000 |
| `--max-steps` | Maximum training steps | 100 |
| `--seed` | Random seed | 42 |
| `--skip-policy` | Skip policy benchmark | False |
| `--skip-outcome` | Skip outcome benchmark | False |

---

## Interpretation Guidelines

### Samples Per Second

- **> 1000 samples/sec**: Excellent throughput
- **100-1000 samples/sec**: Good throughput
- **< 100 samples/sec**: May need optimization

### GPU Memory Usage

- If peak memory is close to total VRAM, consider reducing batch size
- Memory should not exceed 80% of VRAM for stable training

### Step Time Variance

- High p95/mean ratio indicates variable processing time
- Consider profiling for optimization opportunities

---

## Warnings and Disclaimers

> **This document does NOT represent final training results.**
>
> - No production models are trained as part of M14
> - Benchmark uses a small slice of data for timing only
> - Actual training may have different characteristics at scale
> - Results are hardware-specific and not portable

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-31 | 1.0.0 | Initial template created (M14) |

---

**Template Created:** 2026-01-31  
**Awaiting:** Benchmark execution on local hardware

