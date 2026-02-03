"""Tests for M34 contract registry generation and validation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from renacechess.contracts.models import ContractEntryV1, ContractRegistryV1
from renacechess.contracts.registry import (
    compute_file_hash,
    discover_v1_schemas,
    generate_contract_registry,
    validate_contract_registry,
)


class TestContractRegistryModels:
    """Test ContractRegistryV1 and ContractEntryV1 models."""

    def test_contract_entry_v1_creation(self) -> None:
        """Test ContractEntryV1 model creation."""
        entry = ContractEntryV1(
            filename="test.v1.schema.json",
            schema_hash="a" * 64,
            introduced_milestone="M34",
            purpose="Test schema",
            pydantic_model="TestModel",
        )
        assert entry.filename == "test.v1.schema.json"
        assert entry.schema_hash == "a" * 64
        assert entry.introduced_milestone == "M34"
        assert entry.purpose == "Test schema"
        assert entry.pydantic_model == "TestModel"

    def test_contract_entry_v1_optional_model(self) -> None:
        """Test ContractEntryV1 with optional pydantic_model."""
        entry = ContractEntryV1(
            filename="test.v1.schema.json",
            schema_hash="a" * 64,
            introduced_milestone="M34",
            purpose="Test schema",
        )
        assert entry.pydantic_model is None

    def test_contract_registry_v1_creation(self) -> None:
        """Test ContractRegistryV1 model creation."""
        frozen_at = datetime.now(UTC)
        registry = ContractRegistryV1(
            frozen_at=frozen_at,
            contracts=[
                ContractEntryV1(
                    filename="test.v1.schema.json",
                    schema_hash="a" * 64,
                    introduced_milestone="M34",
                    purpose="Test schema",
                )
            ],
        )
        assert registry.schema_version == 1
        assert registry.frozen_at == frozen_at
        assert len(registry.contracts) == 1

    def test_contract_registry_v1_json_serialization(self) -> None:
        """Test ContractRegistryV1 JSON serialization."""
        frozen_at = datetime(2026, 2, 3, 12, 0, 0)
        registry = ContractRegistryV1(
            frozen_at=frozen_at,
            contracts=[
                ContractEntryV1(
                    filename="test.v1.schema.json",
                    schema_hash="a" * 64,
                    introduced_milestone="M34",
                    purpose="Test schema",
                )
            ],
        )
        json_str = registry.model_dump_json(by_alias=True)
        data = json.loads(json_str)
        assert data["schemaVersion"] == 1
        assert data["frozenAt"] == "2026-02-03T12:00:00"
        assert len(data["contracts"]) == 1
        assert data["contracts"][0]["filename"] == "test.v1.schema.json"


class TestRegistryFunctions:
    """Test registry utility functions."""

    def test_compute_file_hash(self, tmp_path: Path) -> None:
        """Test file hash computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content", encoding="utf-8")
        hash1 = compute_file_hash(test_file)
        hash2 = compute_file_hash(test_file)
        assert hash1 == hash2
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_compute_file_hash_different_content(self, tmp_path: Path) -> None:
        """Test file hash changes with content."""
        test_file1 = tmp_path / "test1.txt"
        test_file1.write_text("content 1", encoding="utf-8")
        test_file2 = tmp_path / "test2.txt"
        test_file2.write_text("content 2", encoding="utf-8")
        hash1 = compute_file_hash(test_file1)
        hash2 = compute_file_hash(test_file2)
        assert hash1 != hash2

    def test_discover_v1_schemas(self) -> None:
        """Test v1 schema discovery."""
        schemas_dir = Path("src/renacechess/contracts/schemas/v1")
        schemas = discover_v1_schemas(schemas_dir)
        assert len(schemas) > 0
        # All should be .schema.json files
        assert all(s.name.endswith(".schema.json") for s in schemas)
        # Should include dataset_manifest.v2 (it's a v1 contract, just named v2)
        # But should exclude other v2+ schemas
        v2_plus = [
            s
            for s in schemas
            if (".v2." in s.name or ".v3." in s.name or ".v4." in s.name or ".v5." in s.name)
            and s.name != "dataset_manifest.v2.schema.json"
        ]
        # Note: context_bridge.v2.schema.json is also a v1 contract (M11)
        v2_plus = [s for s in v2_plus if s.name != "context_bridge.v2.schema.json"]
        # These should be minimal (only legacy v2 naming, not actual v2+ contracts)
        assert len(v2_plus) == 0, f"Found unexpected v2+ schemas: {[s.name for s in v2_plus]}"
        # Should include v1 schemas
        v1_schemas = [
            s
            for s in schemas
            if ".v1." in s.name
            or s.name.startswith("context_bridge")
            or s.name.startswith("dataset_manifest")
        ]
        assert len(v1_schemas) > 0

    def test_generate_contract_registry(self, tmp_path: Path) -> None:
        """Test contract registry generation."""
        schemas_dir = Path("src/renacechess/contracts/schemas/v1")
        registry_output = tmp_path / "CONTRACT_REGISTRY_v1.json"

        registry = generate_contract_registry(
            schemas_dir=schemas_dir,
            registry_output=registry_output,
            frozen_at=datetime(2026, 2, 3, 12, 0, 0),
        )

        # Check registry was created
        assert registry_output.exists()
        assert registry.schema_version == 1
        assert len(registry.contracts) > 0

        # Check all contracts have required fields
        for contract in registry.contracts:
            assert contract.filename
            assert len(contract.schema_hash) == 64
            assert contract.introduced_milestone
            assert contract.purpose

        # Check JSON is valid
        registry_data = json.loads(registry_output.read_text(encoding="utf-8"))
        assert registry_data["schemaVersion"] == 1
        assert len(registry_data["contracts"]) == len(registry.contracts)

    def test_validate_contract_registry(self, tmp_path: Path) -> None:
        """Test contract registry validation."""
        schemas_dir = Path("src/renacechess/contracts/schemas/v1")
        registry_output = tmp_path / "CONTRACT_REGISTRY_v1.json"

        # Generate registry
        generate_contract_registry(
            schemas_dir=schemas_dir,
            registry_output=registry_output,
        )

        # Validate should pass
        assert validate_contract_registry(registry_output, schemas_dir) is True

    def test_validate_contract_registry_hash_mismatch(self, tmp_path: Path) -> None:
        """Test validation fails on hash mismatch."""
        schemas_dir = Path("src/renacechess/contracts/schemas/v1")
        registry_output = tmp_path / "CONTRACT_REGISTRY_v1.json"

        # Generate registry
        generate_contract_registry(
            schemas_dir=schemas_dir,
            registry_output=registry_output,
        )

        # Modify a schema file
        first_schema = discover_v1_schemas(schemas_dir)[0]
        original_content = first_schema.read_text(encoding="utf-8")
        first_schema.write_text(original_content + "\n", encoding="utf-8")

        # Validation should fail
        assert validate_contract_registry(registry_output, schemas_dir) is False

        # Restore original
        first_schema.write_text(original_content, encoding="utf-8")
