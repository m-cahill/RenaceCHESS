"""Tests for M15 personality models and schema validation.

This module tests the PersonalityConfigV1, SafetyEnvelopeV1 Pydantic models
and validates them against the JSON schema.
"""

import json
from pathlib import Path

import jsonschema
import pytest

from renacechess.contracts.models import PersonalityConfigV1, SafetyEnvelopeV1
from renacechess.personality.interfaces import PersonalityModuleV1, StructuralContext


class TestPersonalityInterfaceImport:
    """Tests to verify personality interface module loads correctly."""

    def test_interface_module_imports(self):
        """Test that personality interface module imports without error."""
        # Verify the protocol classes exist
        assert PersonalityModuleV1 is not None
        assert StructuralContext is not None

    def test_interface_is_protocol(self):
        """Test that PersonalityModuleV1 is a Protocol."""
        # Protocol classes have _is_protocol attribute
        assert hasattr(PersonalityModuleV1, "__protocol_attrs__") or hasattr(
            PersonalityModuleV1, "_is_protocol"
        )


class TestSafetyEnvelopeV1:
    """Tests for SafetyEnvelopeV1 model."""

    def test_default_values(self):
        """Test that SafetyEnvelopeV1 has correct defaults."""
        envelope = SafetyEnvelopeV1()
        assert envelope.top_k == 5
        assert envelope.delta_p_max == 0.15
        assert envelope.entropy_min == 0.5
        assert envelope.entropy_max == 3.0
        assert envelope.base_reachable is True

    def test_custom_values(self):
        """Test SafetyEnvelopeV1 with custom values."""
        envelope = SafetyEnvelopeV1(
            top_k=10,
            delta_p_max=0.25,
            entropy_min=0.1,
            entropy_max=4.0,
            base_reachable=False,
        )
        assert envelope.top_k == 10
        assert envelope.delta_p_max == 0.25
        assert envelope.entropy_min == 0.1
        assert envelope.entropy_max == 4.0
        assert envelope.base_reachable is False

    def test_alias_input(self):
        """Test SafetyEnvelopeV1 accepts camelCase aliases."""
        envelope = SafetyEnvelopeV1(
            topK=15,
            deltaPMax=0.3,
            entropyMin=0.2,
            entropyMax=5.0,
            baseReachable=True,
        )
        assert envelope.top_k == 15
        assert envelope.delta_p_max == 0.3
        assert envelope.entropy_min == 0.2
        assert envelope.entropy_max == 5.0
        assert envelope.base_reachable is True

    def test_entropy_bounds_validation_valid(self):
        """Test entropy bounds validation passes for valid values."""
        # entropy_min < entropy_max - should pass
        envelope = SafetyEnvelopeV1(entropy_min=0.5, entropy_max=3.0)
        assert envelope.entropy_min == 0.5
        assert envelope.entropy_max == 3.0

        # entropy_min == entropy_max - should pass (edge case)
        envelope_equal = SafetyEnvelopeV1(entropy_min=1.0, entropy_max=1.0)
        assert envelope_equal.entropy_min == 1.0
        assert envelope_equal.entropy_max == 1.0

    def test_entropy_bounds_validation_invalid(self):
        """Test entropy bounds validation fails for invalid values."""
        with pytest.raises(ValueError, match="entropy_min.*must be <= entropy_max"):
            SafetyEnvelopeV1(entropy_min=3.0, entropy_max=0.5)

    def test_top_k_bounds(self):
        """Test top_k bounds validation."""
        # Valid minimum
        envelope_min = SafetyEnvelopeV1(top_k=1)
        assert envelope_min.top_k == 1

        # Valid maximum
        envelope_max = SafetyEnvelopeV1(top_k=100)
        assert envelope_max.top_k == 100

        # Invalid below minimum
        with pytest.raises(ValueError):
            SafetyEnvelopeV1(top_k=0)

        # Invalid above maximum
        with pytest.raises(ValueError):
            SafetyEnvelopeV1(top_k=101)

    def test_delta_p_max_bounds(self):
        """Test delta_p_max bounds validation."""
        # Valid minimum
        envelope_min = SafetyEnvelopeV1(delta_p_max=0.0)
        assert envelope_min.delta_p_max == 0.0

        # Valid maximum
        envelope_max = SafetyEnvelopeV1(delta_p_max=1.0)
        assert envelope_max.delta_p_max == 1.0

        # Invalid below minimum
        with pytest.raises(ValueError):
            SafetyEnvelopeV1(delta_p_max=-0.1)

        # Invalid above maximum
        with pytest.raises(ValueError):
            SafetyEnvelopeV1(delta_p_max=1.1)

    def test_json_serialization(self):
        """Test JSON serialization uses camelCase aliases."""
        envelope = SafetyEnvelopeV1(
            top_k=10,
            delta_p_max=0.2,
            entropy_min=0.3,
            entropy_max=2.5,
            base_reachable=True,
        )
        json_dict = envelope.model_dump(mode="json", by_alias=True)

        assert "topK" in json_dict
        assert "deltaPMax" in json_dict
        assert "entropyMin" in json_dict
        assert "entropyMax" in json_dict
        assert "baseReachable" in json_dict

        # Verify values
        assert json_dict["topK"] == 10
        assert json_dict["deltaPMax"] == 0.2


class TestPersonalityConfigV1:
    """Tests for PersonalityConfigV1 model."""

    def test_minimal_config(self):
        """Test PersonalityConfigV1 with minimal required fields."""
        config = PersonalityConfigV1(
            personality_id="style.test.v1",
            display_name="Test Personality",
            description="A test personality for validation",
        )
        assert config.schema_version == "personality_config.v1"
        assert config.personality_id == "style.test.v1"
        assert config.display_name == "Test Personality"
        assert config.description == "A test personality for validation"
        assert config.enabled is True
        assert config.tunable_parameters == {}
        assert config.safety_envelope is not None

    def test_full_config(self):
        """Test PersonalityConfigV1 with all fields."""
        config = PersonalityConfigV1(
            personality_id="style.pawn_clamp.v1",
            display_name="Pawn Clamp",
            description="GM-style personality that restricts opponent mobility via pawn pushes",
            safety_envelope=SafetyEnvelopeV1(top_k=8, delta_p_max=0.2),
            tunable_parameters={"aggression": 0.7, "mobility_weight": 0.8},
            enabled=True,
        )
        assert config.personality_id == "style.pawn_clamp.v1"
        assert config.safety_envelope.top_k == 8
        assert config.tunable_parameters["aggression"] == 0.7
        assert config.tunable_parameters["mobility_weight"] == 0.8

    def test_alias_input(self):
        """Test PersonalityConfigV1 accepts camelCase aliases."""
        config = PersonalityConfigV1(
            schemaVersion="personality_config.v1",
            personalityId="style.test.v1",
            displayName="Test",
            description="Test personality",
            safetyEnvelope=SafetyEnvelopeV1(),
            tunableParameters={"weight": 0.5},
            enabled=False,
        )
        assert config.schema_version == "personality_config.v1"
        assert config.personality_id == "style.test.v1"
        assert config.display_name == "Test"
        assert config.tunable_parameters["weight"] == 0.5
        assert config.enabled is False

    def test_personality_id_pattern_valid(self):
        """Test valid personality ID patterns."""
        valid_ids = [
            "style.pawn_clamp.v1",
            "tactical.aggressive.v2",
            "positional.solid.v1",
            "a.b.c",
            "style123.test_name.v1",
        ]
        for pid in valid_ids:
            config = PersonalityConfigV1(
                personality_id=pid,
                display_name="Test",
                description="Test",
            )
            assert config.personality_id == pid

    def test_personality_id_pattern_invalid(self):
        """Test invalid personality ID patterns."""
        invalid_ids = [
            "style",  # No dots
            "Style.test.v1",  # Uppercase
            ".style.test",  # Starts with dot
            "style..test",  # Double dots
            "123.test.v1",  # Starts with number
        ]
        for pid in invalid_ids:
            with pytest.raises(ValueError):
                PersonalityConfigV1(
                    personality_id=pid,
                    display_name="Test",
                    description="Test",
                )

    def test_json_serialization(self):
        """Test JSON serialization uses camelCase aliases."""
        config = PersonalityConfigV1(
            personality_id="style.test.v1",
            display_name="Test",
            description="Test personality",
            tunable_parameters={"weight": 0.5},
        )
        json_dict = config.model_dump(mode="json", by_alias=True)

        assert "schemaVersion" in json_dict
        assert "personalityId" in json_dict
        assert "displayName" in json_dict
        assert "safetyEnvelope" in json_dict
        assert "tunableParameters" in json_dict

        # Verify nested object uses aliases
        assert "topK" in json_dict["safetyEnvelope"]
        assert "deltaPMax" in json_dict["safetyEnvelope"]

    def test_json_round_trip(self):
        """Test JSON serialization and deserialization round-trip."""
        original = PersonalityConfigV1(
            personality_id="style.test.v1",
            display_name="Test Personality",
            description="A test personality",
            safety_envelope=SafetyEnvelopeV1(top_k=10, delta_p_max=0.25),
            tunable_parameters={"weight": 0.7},
            enabled=True,
        )

        # Serialize to JSON
        json_str = original.model_dump_json(by_alias=True)

        # Deserialize back
        restored = PersonalityConfigV1.model_validate_json(json_str)

        # Verify equality
        assert restored.personality_id == original.personality_id
        assert restored.display_name == original.display_name
        assert restored.safety_envelope.top_k == original.safety_envelope.top_k
        assert restored.safety_envelope.delta_p_max == original.safety_envelope.delta_p_max
        assert restored.tunable_parameters == original.tunable_parameters


class TestPersonalitySchemaValidation:
    """Tests for JSON schema validation."""

    @pytest.fixture
    def schema(self):
        """Load the personality config JSON schema."""
        schema_path = Path("src/renacechess/contracts/schemas/v1/personality_config.v1.schema.json")
        with open(schema_path, encoding="utf-8") as f:
            return json.load(f)

    def test_minimal_valid_config(self, schema):
        """Test minimal valid config validates against schema."""
        config = {
            "schemaVersion": "personality_config.v1",
            "personalityId": "style.test.v1",
            "displayName": "Test",
            "description": "A test personality",
        }
        jsonschema.validate(config, schema)

    def test_full_valid_config(self, schema):
        """Test full valid config validates against schema."""
        config = {
            "schemaVersion": "personality_config.v1",
            "personalityId": "style.pawn_clamp.v1",
            "displayName": "Pawn Clamp",
            "description": "GM-style pawn restriction personality",
            "safetyEnvelope": {
                "topK": 10,
                "deltaPMax": 0.2,
                "entropyMin": 0.3,
                "entropyMax": 4.0,
                "baseReachable": True,
            },
            "tunableParameters": {
                "aggression": 0.7,
                "mobility_weight": 0.8,
            },
            "enabled": True,
        }
        jsonschema.validate(config, schema)

    def test_missing_required_field(self, schema):
        """Test missing required field fails validation."""
        config = {
            "schemaVersion": "personality_config.v1",
            "personalityId": "style.test.v1",
            # Missing displayName and description
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(config, schema)

    def test_invalid_personality_id_pattern(self, schema):
        """Test invalid personality ID pattern fails validation."""
        config = {
            "schemaVersion": "personality_config.v1",
            "personalityId": "InvalidStyle",  # Uppercase, no dots
            "displayName": "Test",
            "description": "Test",
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(config, schema)

    def test_invalid_schema_version(self, schema):
        """Test invalid schema version fails validation."""
        config = {
            "schemaVersion": "personality_config.v2",  # Wrong version
            "personalityId": "style.test.v1",
            "displayName": "Test",
            "description": "Test",
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(config, schema)

    def test_safety_envelope_invalid_top_k(self, schema):
        """Test invalid top_k in safety envelope fails validation."""
        config = {
            "schemaVersion": "personality_config.v1",
            "personalityId": "style.test.v1",
            "displayName": "Test",
            "description": "Test",
            "safetyEnvelope": {
                "topK": 0,  # Below minimum
            },
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(config, schema)

    def test_tunable_parameters_type(self, schema):
        """Test tunableParameters requires numeric values."""
        config = {
            "schemaVersion": "personality_config.v1",
            "personalityId": "style.test.v1",
            "displayName": "Test",
            "description": "Test",
            "tunableParameters": {
                "weight": "not_a_number",  # String instead of number
            },
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(config, schema)

    def test_pydantic_and_schema_consistency(self, schema):
        """Test that Pydantic model output validates against JSON schema."""
        config = PersonalityConfigV1(
            personality_id="style.test.v1",
            display_name="Test Personality",
            description="A test personality for validation",
            safety_envelope=SafetyEnvelopeV1(top_k=10, delta_p_max=0.2),
            tunable_parameters={"weight": 0.7},
            enabled=True,
        )

        # Serialize to dict with aliases (JSON schema uses aliases)
        json_dict = config.model_dump(mode="json", by_alias=True)

        # Should validate against schema
        jsonschema.validate(json_dict, schema)
