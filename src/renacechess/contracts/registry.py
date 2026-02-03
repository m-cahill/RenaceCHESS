"""Contract registry generator and validator for M34 release lock."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from renacechess.contracts.models import ContractEntryV1, ContractRegistryV1


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of file content."""
    content = file_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def discover_v1_schemas(schemas_dir: Path) -> list[Path]:
    """Discover all v1 schema files in the schemas directory.

    Note: Some schemas are named .v2 but are actually v1 contracts (e.g.,
    dataset_manifest.v2.schema.json, context_bridge.v2.schema.json). These
    are included because they are part of the v1 contract set.
    """
    v1_schemas: list[Path] = []
    
    # Legacy v2-named schemas that are actually v1 contracts
    legacy_v2_contracts = {
        "dataset_manifest.v2.schema.json",
        "context_bridge.v2.schema.json",
    }
    
    # Find all .schema.json files
    for schema_file in schemas_dir.glob("*.schema.json"):
        filename = schema_file.name
        
        # Include legacy v2-named contracts
        if filename in legacy_v2_contracts:
            v1_schemas.append(schema_file)
            continue
        
        # Include files that are explicitly v1 or legacy (no version in name)
        # Exclude v2+ schemas (except the legacy ones above)
        if ".v2." in filename or ".v3." in filename or ".v4." in filename or ".v5." in filename:
            continue
        v1_schemas.append(schema_file)
    
    # Sort for deterministic output
    return sorted(v1_schemas)


def generate_contract_registry(
    schemas_dir: Path,
    registry_output: Path,
    frozen_at: datetime | None = None,
) -> ContractRegistryV1:
    """Generate contract registry from discovered v1 schemas.

    Args:
        schemas_dir: Directory containing v1 schema files
        registry_output: Path where registry JSON will be written
        frozen_at: Timestamp for freezing (defaults to now)

    Returns:
        ContractRegistryV1 registry object
    """
    if frozen_at is None:
        frozen_at = datetime.now(UTC)
    
    # Discover all v1 schemas
    schema_files = discover_v1_schemas(schemas_dir)
    
    # Build contract entries
    contracts: list[ContractEntryV1] = []
    
    # Milestone mapping (manually curated based on renacechess.md)
    milestone_map: dict[str, str] = {
        "context_bridge.schema.json": "M04",
        "context_bridge.v2.schema.json": "M11",
        "dataset_manifest.schema.json": "M01",
        "dataset_manifest.v2.schema.json": "M03",
        "ingest_receipt.schema.json": "M02",
        "eval_report.v1.schema.json": "M04",
        "eval_report.v2.schema.json": "M05",
        "eval_report.v3.schema.json": "M06",
        "eval_report.v4.schema.json": "M07",
        "eval_report.v5.schema.json": "M09",
        "frozen_eval_manifest.v1.schema.json": "M06",
        "frozen_eval_manifest.v2.schema.json": "M30",
        "eval_set_provenance.v1.schema.json": "M30",
        "PerPieceFeaturesV1.schema.json": "M11",
        "SquareMapFeaturesV1.schema.json": "M11",
        "personality_config.v1.schema.json": "M15",
        "personality_eval_artifact.v1.schema.json": "M18",
        "advice_facts.v1.schema.json": "M19",
        "elo_bucket_deltas.v1.schema.json": "M20",
        "coaching_draft.v1.schema.json": "M21",
        "coaching_evaluation.v1.schema.json": "M21",
        "coaching_surface.v1.schema.json": "M22",
        "calibration_metrics.v1.schema.json": "M24",
        "calibration_delta.v1.schema.json": "M25",
        "recalibration_parameters.v1.schema.json": "M25",
        "recalibration_gate.v1.schema.json": "M26",
        "runtime_recalibration_report.v1.schema.json": "M27",
        "runtime_recalibration_delta.v1.schema.json": "M27",
        "runtime_recalibration_activation_policy.v1.schema.json": "M28",
        "runtime_recalibration_decision.v1.schema.json": "M28",
        "training_benchmark_report.v1.schema.json": "M29",
        "training_config_lock.v1.schema.json": "M31",
        "training_run_report.v1.schema.json": "M31",
        "post_train_eval_report.v1.schema.json": "M32",
        "policy_eval_metrics.v1.schema.json": "M32",
        "outcome_eval_metrics.v1.schema.json": "M32",
        "delta_metrics.v1.schema.json": "M32",
        "external_proof_pack.v1.schema.json": "M33",
    }
    
    # Model name mapping (manually curated)
    model_map: dict[str, str] = {
        "context_bridge.schema.json": "ContextBridgePayload",
        "context_bridge.v2.schema.json": "ContextBridgePayloadV2",
        "dataset_manifest.schema.json": "DatasetManifest",
        "dataset_manifest.v2.schema.json": "DatasetManifestV2",
        "ingest_receipt.schema.json": "IngestReceiptV1",
        "eval_report.v1.schema.json": "EvalReportV1",
        "eval_report.v2.schema.json": "EvalReportV2",
        "eval_report.v3.schema.json": "EvalReportV3",
        "eval_report.v4.schema.json": "EvalReportV4",
        "eval_report.v5.schema.json": "EvalReportV5",
        "frozen_eval_manifest.v1.schema.json": "FrozenEvalManifestV1",
        "frozen_eval_manifest.v2.schema.json": "FrozenEvalManifestV2",
        "eval_set_provenance.v1.schema.json": "EvalSetProvenanceV1",
        "PerPieceFeaturesV1.schema.json": "PerPieceFeaturesV1",
        "SquareMapFeaturesV1.schema.json": "SquareMapFeaturesV1",
        "personality_config.v1.schema.json": "PersonalityConfigV1",
        "personality_eval_artifact.v1.schema.json": "PersonalityEvalArtifactV1",
        "advice_facts.v1.schema.json": "AdviceFactsV1",
        "elo_bucket_deltas.v1.schema.json": "EloBucketDeltaFactsV1",
        "coaching_draft.v1.schema.json": "CoachingDraftV1",
        "coaching_evaluation.v1.schema.json": "CoachingEvaluationV1",
        "coaching_surface.v1.schema.json": "CoachingSurfaceV1",
        "calibration_metrics.v1.schema.json": "CalibrationMetricsV1",
        "calibration_delta.v1.schema.json": "CalibrationDeltaV1",
        "recalibration_parameters.v1.schema.json": "RecalibrationParametersV1",
        "recalibration_gate.v1.schema.json": "RecalibrationGateV1",
        "runtime_recalibration_report.v1.schema.json": "RuntimeRecalibrationReportV1",
        "runtime_recalibration_delta.v1.schema.json": "RuntimeRecalibrationDeltaV1",
        "runtime_recalibration_activation_policy.v1.schema.json": (
            "RuntimeRecalibrationActivationPolicyV1"
        ),
        "runtime_recalibration_decision.v1.schema.json": "RuntimeRecalibrationDecisionV1",
        "training_benchmark_report.v1.schema.json": "TrainingBenchmarkReportV1",
        "training_config_lock.v1.schema.json": "TrainingConfigLockV1",
        "training_run_report.v1.schema.json": "TrainingRunReportV1",
        "post_train_eval_report.v1.schema.json": "PostTrainEvalReportV1",
        "policy_eval_metrics.v1.schema.json": "PolicyEvalMetricsV1",
        "outcome_eval_metrics.v1.schema.json": "OutcomeEvalMetricsV1",
        "delta_metrics.v1.schema.json": "DeltaMetricsV1",
        "external_proof_pack.v1.schema.json": "ExternalProofPackV1",
    }
    
    # Purpose mapping (manually curated)
    purpose_map: dict[str, str] = {
        "context_bridge.schema.json": "Context Bridge payload for LLM grounding (v1)",
        "context_bridge.v2.schema.json": "Context Bridge payload with structural cognition (v2)",
        "dataset_manifest.schema.json": "Dataset manifest (v1)",
        "dataset_manifest.v2.schema.json": "Dataset manifest with assembly config (v2)",
        "ingest_receipt.schema.json": "Ingestion receipt artifact",
        "eval_report.v1.schema.json": "Evaluation report (v1)",
        "eval_report.v2.schema.json": "Evaluation report with accuracy metrics (v2)",
        "eval_report.v3.schema.json": "Evaluation report with conditioned metrics (v3)",
        "eval_report.v4.schema.json": "Evaluation report with HDI (v4)",
        "eval_report.v5.schema.json": "Evaluation report with outcome metrics (v5)",
        "frozen_eval_manifest.v1.schema.json": "Frozen evaluation set manifest (v1)",
        "frozen_eval_manifest.v2.schema.json": "Frozen evaluation set manifest (v2, 10k positions)",
        "eval_set_provenance.v1.schema.json": "Evaluation set provenance artifact",
        "PerPieceFeaturesV1.schema.json": "Per-piece structural cognition features",
        "SquareMapFeaturesV1.schema.json": "Square-level structural cognition features",
        "personality_config.v1.schema.json": "Personality module configuration",
        "personality_eval_artifact.v1.schema.json": "Personality evaluation artifact",
        "advice_facts.v1.schema.json": "Coaching advice facts contract",
        "elo_bucket_deltas.v1.schema.json": "Elo-bucket delta facts for cross-bucket comparison",
        "coaching_draft.v1.schema.json": "LLM-generated coaching draft",
        "coaching_evaluation.v1.schema.json": "Coaching translation evaluation metrics",
        "coaching_surface.v1.schema.json": "Coaching CLI surface output",
        "calibration_metrics.v1.schema.json": "Calibration metrics (ECE, Brier, NLL)",
        "calibration_delta.v1.schema.json": "Calibration improvement delta",
        "recalibration_parameters.v1.schema.json": "Temperature scaling recalibration parameters",
        "recalibration_gate.v1.schema.json": "Runtime recalibration gate artifact",
        "runtime_recalibration_report.v1.schema.json": "Runtime recalibration evaluation report",
        "runtime_recalibration_delta.v1.schema.json": "Runtime recalibration delta metrics",
        "runtime_recalibration_activation_policy.v1.schema.json": "Recalibration activation policy",
        "runtime_recalibration_decision.v1.schema.json": "Recalibration activation decision",
        "training_benchmark_report.v1.schema.json": "Training benchmark report",
        "training_config_lock.v1.schema.json": "Immutable training configuration lock",
        "training_run_report.v1.schema.json": "Training run execution report",
        "post_train_eval_report.v1.schema.json": "Post-training evaluation report",
        "policy_eval_metrics.v1.schema.json": "Policy evaluation metrics",
        "outcome_eval_metrics.v1.schema.json": "Outcome evaluation metrics",
        "delta_metrics.v1.schema.json": "Delta metrics (trained vs baseline)",
        "external_proof_pack.v1.schema.json": "External proof pack manifest",
    }
    
    for schema_file in schema_files:
        filename = schema_file.name
        schema_hash = compute_file_hash(schema_file)
        milestone = milestone_map.get(filename, "UNKNOWN")
        model_name = model_map.get(filename)
        purpose = purpose_map.get(filename, f"Schema: {filename}")
        
        contracts.append(
            ContractEntryV1(
                filename=filename,
                schema_hash=schema_hash,
                introduced_milestone=milestone,
                purpose=purpose,
                pydantic_model=model_name,
            )
        )
    
    # Create registry
    registry = ContractRegistryV1(
        frozen_at=frozen_at,
        contracts=contracts,
    )
    
    # Write registry with pretty formatting
    json_str = registry.model_dump_json(by_alias=True)
    # Parse and re-serialize with proper indentation
    json_data = json.loads(json_str)
    formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False, sort_keys=False)
    registry_output.write_text(formatted_json, encoding="utf-8")
    
    return registry


def validate_contract_registry(registry_path: Path, schemas_dir: Path) -> bool:
    """Validate that contract registry matches current schema files.

    Args:
        registry_path: Path to registry JSON file
        schemas_dir: Directory containing v1 schema files

    Returns:
        True if validation passes, False otherwise
    """
    # Load registry
    registry_data = json.loads(registry_path.read_text(encoding="utf-8"))
    registry = ContractRegistryV1.model_validate(registry_data)
    
    # Discover current schemas
    current_schemas = discover_v1_schemas(schemas_dir)
    current_filenames = {s.name for s in current_schemas}
    registry_filenames = {c.filename for c in registry.contracts}
    
    # Check for missing schemas
    missing = current_filenames - registry_filenames
    if missing:
        print(f"ERROR: Missing schemas in registry: {missing}")
        return False
    
    # Check for extra schemas in registry
    extra = registry_filenames - current_filenames
    if extra:
        print(f"ERROR: Extra schemas in registry: {extra}")
        return False
    
    # Validate hashes
    for contract in registry.contracts:
        schema_path = schemas_dir / contract.filename
        if not schema_path.exists():
            print(f"ERROR: Schema file not found: {contract.filename}")
            return False
        
        current_hash = compute_file_hash(schema_path)
        if current_hash != contract.schema_hash:
            print(
                f"ERROR: Hash mismatch for {contract.filename}: "
                f"expected {contract.schema_hash}, got {current_hash}"
            )
            return False
    
    print("SUCCESS: Contract registry validation passed")
    return True

