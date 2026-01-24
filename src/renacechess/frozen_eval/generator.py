"""Frozen evaluation manifest generation for M06.

This module implements deterministic selection of evaluation records with
stratification by conditioning axes (skill, time control, time pressure).
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from renacechess.contracts.models import (
    DatasetManifestV2,
    FrozenEvalManifestCoverageShortfall,
    FrozenEvalManifestRecord,
    FrozenEvalManifestSourceRef,
    FrozenEvalManifestStratificationTargets,
    FrozenEvalManifestV1,
)
from renacechess.determinism import canonical_hash, canonical_json_dump


def generate_frozen_eval_manifest(
    source_manifest_path: Path,
    target_total_records: int = 10000,
    min_per_skill_bucket: int = 500,
    created_at: datetime | None = None,
) -> FrozenEvalManifestV1:
    """Generate frozen evaluation manifest from source dataset manifest.

    Args:
        source_manifest_path: Path to source dataset manifest v2.
        target_total_records: Target total record count (default: 10,000).
        min_per_skill_bucket: Hard minimum records per skill bucket if available (default: 500).
        created_at: Override creation timestamp (for testing).

    Returns:
        Frozen evaluation manifest v1 model.

    Raises:
        FileNotFoundError: If source manifest doesn't exist.
        ValueError: If source manifest is invalid or has insufficient labeled records.

    Note:
        M06 decision: If dataset cannot satisfy minimums, still produce a frozen set
        (do not fail generation unless total labeled < 1,000).
    """
    # Load source manifest
    if not source_manifest_path.exists():
        raise FileNotFoundError(f"Source manifest not found: {source_manifest_path}")

    with source_manifest_path.open() as f:
        manifest_dict = json.load(f)

    source_manifest = DatasetManifestV2.model_validate(manifest_dict)

    # Read all shards and extract labeled records with conditioning metadata
    records: list[FrozenEvalManifestRecord] = []
    manifest_dir = source_manifest_path.parent

    for shard_ref in source_manifest.shard_refs:
        # Try relative to manifest directory first
        shard_path = manifest_dir / shard_ref.path
        if not shard_path.exists():
            # Try absolute path
            shard_path = Path(shard_ref.path)

        if not shard_path.exists():
            raise FileNotFoundError(f"Shard file not found: {shard_ref.path}")

        with shard_path.open() as f:
            for line in f:
                record_dict = json.loads(line.strip())

                # Only include labeled records (with chosenMove)
                if "chosenMove" not in record_dict or record_dict["chosenMove"] is None:
                    continue

                # Extract conditioning metadata
                conditioning = record_dict.get("conditioning", {})
                skill_bucket_id = conditioning.get("skillBucketId")
                time_control_class = conditioning.get("timeControlClass")
                time_pressure_bucket_raw = conditioning.get("timePressureBucket")
                # Normalize legacy uppercase values to lowercase (M06 format)
                if time_pressure_bucket_raw == "NORMAL":
                    time_pressure_bucket = "normal"
                elif time_pressure_bucket_raw == "LOW":
                    time_pressure_bucket = "low"
                elif time_pressure_bucket_raw == "TROUBLE":
                    time_pressure_bucket = "trouble"
                else:
                    time_pressure_bucket = time_pressure_bucket_raw

                # Compute record key (FEN:ply)
                fen = record_dict["position"]["fen"]
                # Infer ply from meta if available, else use hash
                meta = record_dict.get("meta", {})
                input_hash = meta.get("inputHash", "")
                record_key = f"{fen}:{input_hash[:8]}"

                records.append(
                    FrozenEvalManifestRecord(
                        record_key=record_key,
                        shard_id=shard_ref.shard_id,
                        shard_hash=shard_ref.hash,
                        skill_bucket_id=skill_bucket_id,
                        time_control_class=time_control_class,
                        time_pressure_bucket=time_pressure_bucket,
                    )
                )

    # Check minimum total labeled records
    if len(records) < 1000:
        raise ValueError(
            f"Insufficient labeled records for frozen eval: {len(records)} < 1,000 minimum"
        )

    # Stratify by skill bucket
    records_by_skill = defaultdict(list)
    for record in records:
        bucket_id = record.skill_bucket_id or "unknown"
        records_by_skill[bucket_id].append(record)

    # Select records with stratification
    selected_records = []
    coverage_shortfalls = []

    # Hard minimum per skill bucket (if available)
    for bucket_id, bucket_records in records_by_skill.items():
        if len(bucket_records) < min_per_skill_bucket:
            coverage_shortfalls.append(
                FrozenEvalManifestCoverageShortfall(
                    axis="skillBucketId",
                    value=bucket_id,
                    target=min_per_skill_bucket,
                    actual=len(bucket_records),
                )
            )

    # Simple proportional selection (deterministic)
    # Sort by skill bucket ID for determinism
    sorted_buckets = sorted(records_by_skill.items())

    # Compute proportional allocation
    total_available = len(records)
    records_per_bucket = {}

    for bucket_id, bucket_records in sorted_buckets:
        proportion = len(bucket_records) / total_available
        allocated = max(
            (
                min_per_skill_bucket
                if len(bucket_records) >= min_per_skill_bucket
                else len(bucket_records)
            ),
            int(target_total_records * proportion),
        )
        records_per_bucket[bucket_id] = min(allocated, len(bucket_records))

    # Adjust if over-allocated
    total_allocated = sum(records_per_bucket.values())
    if total_allocated > target_total_records:
        # Proportionally reduce
        scale = target_total_records / total_allocated
        for bucket_id in records_per_bucket:
            records_per_bucket[bucket_id] = int(records_per_bucket[bucket_id] * scale)

    # Select records (deterministic: first N from each bucket after sorting by record_key)
    for bucket_id, bucket_records in sorted_buckets:
        count = records_per_bucket[bucket_id]
        sorted_bucket_records = sorted(bucket_records, key=lambda r: r.record_key)
        selected_records.extend(sorted_bucket_records[:count])

    # Compute counts by conditioning axes
    counts_by_skill: dict[str, int] = defaultdict(int)
    counts_by_time_control: dict[str, int] = defaultdict(int)
    counts_by_time_pressure: dict[str, int] = defaultdict(int)

    for record in selected_records:
        counts_by_skill[record.skill_bucket_id or "unknown"] += 1
        counts_by_time_control[record.time_control_class or "unknown"] += 1
        counts_by_time_pressure[record.time_pressure_bucket or "unknown"] += 1

    # Build manifest (without hash)
    if created_at is None:
        created_at = datetime.now()

    # Compute manifest hash first (exclude manifestHash field)
    # Build dict without hash for hashing
    manifest_dict_for_hash = {
        "schemaVersion": 1,
        "createdAt": created_at.isoformat(),
        "sourceManifestRef": {
            "datasetDigest": source_manifest.dataset_digest,
            "manifestPath": str(source_manifest_path),
        },
        "records": [
            {
                "recordKey": r.record_key,
                "shardId": r.shard_id,
                "shardHash": r.shard_hash,
                "skillBucketId": r.skill_bucket_id,
                "timeControlClass": r.time_control_class,
                "timePressureBucket": r.time_pressure_bucket,
            }
            for r in selected_records
        ],
        "stratificationTargets": {
            "totalRecords": target_total_records,
            "minPerSkillBucket": min_per_skill_bucket,
        },
        "countsBySkillBucketId": dict(counts_by_skill),
        "countsByTimeControlClass": dict(counts_by_time_control),
        "countsByTimePressureBucket": dict(counts_by_time_pressure),
        "coverageShortfalls": [
            {
                "axis": s.axis,
                "value": s.value,
                "target": s.target,
                "actual": s.actual,
            }
            for s in coverage_shortfalls
        ],
    }
    manifest_bytes = canonical_json_dump(manifest_dict_for_hash)
    from renacechess.determinism import stable_hash

    manifest_hash = stable_hash(manifest_bytes)

    # Build manifest with computed hash
    manifest = FrozenEvalManifestV1(
        schema_version=1,
        created_at=created_at,
        source_manifest_ref=FrozenEvalManifestSourceRef(
            dataset_digest=source_manifest.dataset_digest,
            manifest_path=str(source_manifest_path),
        ),
        records=selected_records,
        stratification_targets=FrozenEvalManifestStratificationTargets(
            total_records=target_total_records,
            min_per_skill_bucket=min_per_skill_bucket,
        ),
        counts_by_skill_bucket_id=dict(counts_by_skill),
        counts_by_time_control_class=dict(counts_by_time_control),
        counts_by_time_pressure_bucket=dict(counts_by_time_pressure),
        coverage_shortfalls=coverage_shortfalls,
        manifest_hash=manifest_hash,
    )

    return manifest


def write_frozen_eval_manifest(manifest: FrozenEvalManifestV1, output_path: Path) -> None:
    """Write frozen eval manifest to disk.

    Args:
        manifest: Frozen evaluation manifest v1 model.
        output_path: Path to write manifest file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_dict = manifest.model_dump(mode="json", by_alias=True, exclude_none=True)
    manifest_bytes = canonical_json_dump(manifest_dict)

    with output_path.open("wb") as f:
        f.write(manifest_bytes)
