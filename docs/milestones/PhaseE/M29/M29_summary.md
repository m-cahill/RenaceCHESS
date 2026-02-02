# M29 Summary: GPU Benchmarking & Training Time Estimation

**Status:** ✅ CLOSED  
**Phase:** E (Release)  
**ADR Reference:** GPU-BENCHMARKING-001  
**Completion Date:** 2026-02-02  
**Verdict:** Infrastructure-validated; real-data benchmark intentionally deferred to M31

---

## Executive Summary

M29 establishes empirical, hardware-specific training performance characteristics for RenaceCHESS on RTX 5090 (Blackwell architecture). The milestone validates GPU compatibility, benchmark infrastructure, and prepares for production training time estimation.

---

## M29-SYNTHETIC-INFRA-PROBE ✅ COMPLETE

**Date:** 2026-02-02  
**Status:** PASS

### What Was Validated

| Check | Result |
|-------|--------|
| RTX 5090 Detection | ✅ NVIDIA GeForce RTX 5090 (31.84 GB VRAM) |
| Blackwell SM120 Support | ✅ PyTorch 2.10.0+cu128 / CUDA 12.8 |
| Training Loop Execution | ✅ 16 runs, all successful |
| Batch 512 OOM | ✅ No OOM at any batch size |
| AMP Support | ✅ Functional, marginal gains on synthetic |
| Benchmark Artifact Generation | ✅ TrainingBenchmarkReportV1 schema validated |
| Determinism Hash | ✅ `sha256:6bcb9f317465cc...` |

### Synthetic Benchmark Results (Policy-only, FP32)

| Batch Size | Samples/sec | VRAM Peak |
|------------|-------------|-----------|
| 64 | 6,535 | 0.05 GB |
| 128 | 88,568 | 0.05 GB |
| 256 | 212,955 | 0.05 GB |
| 512 | 301,620 | 0.05 GB |

### Synthetic Benchmark Results (Policy+Outcome, FP32)

| Batch Size | Samples/sec | VRAM Peak |
|------------|-------------|-----------|
| 64 | 38,224 | 0.05 GB |
| 128 | 85,577 | 0.06 GB |
| 256 | 141,831 | 0.06 GB |
| 512 | 200,666 | 0.06 GB |

### Interpretation

> Synthetic benchmark validated Blackwell compatibility and training infrastructure.  
> Real-data benchmark required for timing confidence.

**Synthetic does NOT provide:**
- Real I/O costs
- Real feature extraction overhead
- Real memory fragmentation
- Production-accurate throughput estimates

**Time-to-train estimate confidence:** LOW (as expected)

---

## Pending: Real-Data Benchmark

**Required for M29 completion:**

1. One real-data benchmark run with:
   - Real v2 dataset manifest
   - Real frozen eval manifest
   - ~100k positions
   - Batch 256, FP32/AMP, policy+outcome

2. This provides:
   - Real dataloader cost
   - Real feature extraction cost
   - Real memory pressure
   - Production-relevant throughput slope

---

## Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Benchmark Report (Synthetic) | `benchmark_report.json` | ✅ Generated |
| TrainingBenchmarkReportV1 Schema | `contracts/schemas/v1/training_benchmark_report.v1.schema.json` | ✅ Complete |
| Schema Tests | `tests/test_m29_benchmark_schema.py` | ✅ 41 tests passing |
| Benchmark Script | `scripts/benchmark_training.py` | ✅ M29 mode + synthetic mode |

---

## Environment Details

```
GPU: NVIDIA GeForce RTX 5090
VRAM: 31.84 GB
CUDA: 12.8
Driver: 576.88
PyTorch: 2.10.0+cu128
Python: 3.12.10
OS: Windows 11
CPU: AMD64 Family 26 Model 68 (8 cores)
```

---

## Closeout Verdict

> **M29 — GPU-BENCHMARKING-001 is CLOSED.**
>
> This milestone validated Blackwell (RTX 5090) compatibility, training-loop execution, memory headroom, and benchmark instrumentation using a synthetic workload.
>
> No production v2 dataset manifest exists yet; therefore, real-data benchmarking was intentionally deferred to M31, where it naturally coincides with full training.
>
> Synthetic results are explicitly labeled low-confidence and were used only to validate feasibility and unblock Phase E progression.

---

## What This Unlocks

- ✅ **M30** — Frozen eval scale planning (uses synthetic throughput as conservative baseline)
- ✅ **M31** — Full training (first real-data touchpoint, includes real-data benchmark)
- ❌ No fake "benchmark dataset" needed
- ❌ No retroactive data archaeology

---

**Last Updated:** 2026-02-02  
**Closed By:** RediAI Audit Lead

