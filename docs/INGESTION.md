# RenaceCHESS Ingestion

This document describes the ingestion pipeline for downloading and caching Lichess database exports.

## Overview

RenaceCHESS provides a deterministic, audit-friendly ingestion pipeline for Lichess database exports. The pipeline supports:

- Downloading from Lichess monthly dumps (standard rated games)
- Caching artifacts with SHA-256 verification
- Optional decompression of `.zst` files to `.pgn`
- Generating versioned "ingest receipts" for reproducibility

## Lichess Database Exports

Lichess database exports are published at [database.lichess.org](https://database.lichess.org/) and are released under **CC0** (public domain). The monthly game dumps are:

- Format: `.pgn.zst` (Zstandard-compressed PGN)
- Pattern: `lichess_db_standard_rated_YYYY-MM.pgn.zst`
- Size: Very large (multi-GB for recent months)
- Availability: Monthly dumps going back several years

**Important:** Full-history downloads require significant storage. For local experiments, we recommend starting with small early months (e.g., 2013-01, 2014-01) which are typically smaller.

## Usage

### Ingest Lichess Monthly Dump

```bash
# Ingest a specific month
renacechess ingest lichess \
  --month 2024-01 \
  --out ./ingested/ \
  --cache-dir ~/.renacechess/cache \
  --decompress
```

**Options:**
- `--month YYYY-MM`: Month to ingest (required)
- `--out <dir>`: Output directory for receipt copy (required)
- `--cache-dir <dir>`: Cache directory (default: `~/.renacechess/cache`)
- `--decompress`: Decompress `.zst` to `.pgn` (optional)

### Ingest from URL or Local File

```bash
# Ingest from explicit URL
renacechess ingest url \
  --url https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst \
  --out ./ingested/ \
  --decompress

# Ingest from local file
renacechess ingest url \
  --url file:///path/to/file.pgn \
  --out ./ingested/

# Ingest from local file path (Windows/Unix)
renacechess ingest url \
  --url /path/to/file.pgn \
  --out ./ingested/
```

## Cache Layout

The cache directory structure is:

```
<cache_dir>/
├── sources/
│   └── <source_id>/
│       └── <filename>          # Cached artifact
├── receipts/
│   └── <source_id>.json        # Ingest receipt
└── derived/
    └── <source_id>/
        └── <filename>          # Decompressed artifacts (if --decompress used)
```

**Source ID:** Deterministic 16-character hex hash computed from source specification (preset/URL, month, resolved URI).

## Ingest Receipts

Each ingestion produces an **ingest receipt** that documents:

- Source URI and metadata (ETag, Last-Modified, Content-Length if available)
- Cached artifact location, SHA-256 hash, size, and media type
- Derived artifacts (decompressed files) if decompression was used
- Provenance (tool version, platform, Python version)

The receipt is the **proof of reproducibility**—it allows you to verify that you have the exact same artifact that was downloaded.

### Receipt Schema

Receipts conform to the Ingest Receipt schema (v1). See `src/renacechess/contracts/schemas/v1/ingest_receipt.schema.json` for the full schema.

Example receipt:

```json
{
  "schemaVersion": "v1",
  "createdAt": "2024-01-01T12:00:00",
  "source": {
    "uri": "https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst",
    "resolvedUri": "https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst",
    "etag": "\"abc123\"",
    "lastModified": "Mon, 01 Jan 2024 12:00:00 GMT",
    "contentLength": 1000000000
  },
  "artifact": {
    "cachePath": "sources/abc123def456/lichess_db_standard_rated_2024-01.pgn.zst",
    "sha256": "a1b2c3d4e5f6...",
    "sizeBytes": 1000000000,
    "mediaType": "application/zstd",
    "compression": "zstd"
  },
  "derived": {
    "decompressedPath": "derived/abc123def456/lichess_db_standard_rated_2024-01.pgn",
    "decompressedSha256": "f6e5d4c3b2a1...",
    "decompressedSizeBytes": 5000000000
  },
  "provenance": {
    "toolVersion": "0.1.0",
    "platform": "linux-x86_64",
    "pythonVersion": "3.11.0"
  }
}
```

## Cache Hits

If you ingest the same source twice, the second run will be a **cache hit**:

- No re-download occurs
- Existing cached artifact is reused
- Receipt is loaded from cache (deterministic)
- Output message indicates cache hit

This ensures:
- **Determinism:** Same source always produces same receipt
- **Efficiency:** No redundant downloads
- **Reproducibility:** Receipts are stable across runs

## Decompression

When `--decompress` is used:

1. The `.zst` file is stream-decompressed to `.pgn`
2. SHA-256 hash is computed during decompression (streaming)
3. Decompressed file is stored in `cache/derived/<source_id>/`
4. Receipt is updated with `derived` section

**Note:** Decompression requires the `zstandard` library (installed automatically with package dependencies).

## Determinism Guarantees

The ingestion pipeline guarantees:

1. **Deterministic source IDs:** Same source specification → same source ID
2. **Deterministic receipts:** Same source → same receipt (when cached)
3. **SHA-256 verification:** All artifacts are verified via SHA-256
4. **Atomic writes:** All file writes are atomic (temp file + rename)

## Offline Testing

All ingestion tests are **offline and deterministic**:

- No external network calls in CI
- Tests use local file fixtures
- `.zst` fixtures created programmatically when zstandard is available
- Golden file regression tests for receipt stability

## Integration with Dataset Builder

After ingestion, you can use the cached (or decompressed) PGN files with the dataset builder:

```bash
# Ingest and decompress
renacechess ingest lichess --month 2024-01 --out ./ingested/ --decompress

# Build dataset from decompressed PGN
renacechess dataset build \
  --pgn ~/.renacechess/cache/derived/<source_id>/lichess_db_standard_rated_2024-01.pgn \
  --out ./datasets/2024-01/ \
  --max-positions 1000000
```

## Troubleshooting

### Large File Sizes

Lichess monthly dumps are very large. For local experiments:
- Start with early months (2013-2015) which are smaller
- Use `--decompress` only when needed
- Monitor disk space in cache directory

### Network Issues

If downloads fail:
- Check network connectivity
- Verify URL is accessible
- Check cache directory permissions
- Review error messages for specific issues

### Cache Directory

Default cache location: `~/.renacechess/cache`

To use a custom location:
```bash
renacechess ingest lichess --month 2024-01 --out ./ingested/ --cache-dir /custom/path
```

## License Note

Lichess database exports are released under **CC0** (public domain) and are freely available for download and redistribution. See [database.lichess.org](https://database.lichess.org/) for details.

