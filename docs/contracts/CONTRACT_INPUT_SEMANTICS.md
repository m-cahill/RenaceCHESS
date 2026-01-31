# Contract Input Semantics — RenaceCHESS

**Version:** 1.0  
**Status:** ✅ FROZEN  
**Established:** M13 — CONTRACT-INPUT-SEMANTICS-001  
**Supersedes:** Implicit behavior (pre-M13)

---

## Purpose

This document defines the **explicit, authoritative contract** for how Pydantic models in RenaceCHESS accept input data. This contract resolves ambiguity revealed in M12 regarding dict-based model instantiation under Pydantic v2.

---

## Contract Rule: Alias-Only Dict Inputs

### **Option A (Confirmed): Alias-Only Dict Inputs**

**Final rule:**

* **Dict inputs MUST use alias (camelCase) keys**
* **Keyword arguments MAY use snake_case**
* **No implicit normalization inside Pydantic**
* **No acceptance of snake_case dicts at model boundaries**

This is a **first-class contract**, not a workaround.

---

## Detailed Semantics

### Dict-Based Instantiation

When instantiating a Pydantic model from a dictionary:

```python
# ✅ CORRECT: Use camelCase alias keys
model = MyModel.model_validate({
    "schemaVersion": "v1",  # camelCase alias
    "skillBucket": "1200-1400",  # camelCase alias
})

# ❌ INCORRECT: snake_case keys in dict
model = MyModel.model_validate({
    "schema_version": "v1",  # snake_case - violates contract
    "skill_bucket": "1200-1400",  # snake_case - violates contract
})
```

### Keyword Argument Instantiation

When instantiating via keyword arguments:

```python
# ✅ CORRECT: snake_case keyword arguments
model = MyModel(
    schema_version="v1",  # snake_case Python attribute
    skill_bucket="1200-1400",  # snake_case Python attribute
)

# ✅ ALSO CORRECT: camelCase aliases as keyword arguments
model = MyModel(
    schemaVersion="v1",  # camelCase alias
    skillBucket="1200-1400",  # camelCase alias
)
```

### JSON Deserialization

When deserializing from JSON:

```python
# ✅ CORRECT: JSON uses camelCase (by_alias=True)
json_str = '{"schemaVersion": "v1", "skillBucket": "1200-1400"}'
model = MyModel.model_validate_json(json_str)

# ✅ CORRECT: Normalize dict before validation if needed
json_dict = {"schemaVersion": "v1", "skillBucket": "1200-1400"}
model = MyModel.model_validate(json_dict)
```

---

## Boundary Normalization

### Principle

**Normalization must happen at contract boundaries**, not inside Pydantic models.

### Where Normalization Is Required

Normalization is required when:

1. **External data enters the system** (e.g., feature extractors, adapters)
2. **Data crosses a contract boundary** (e.g., from dict → Pydantic model)
3. **Legacy code provides snake_case dicts** (must normalize before validation)

### Normalization Pattern

```python
from renacechess.contracts.validation import normalize_dict_keys_to_aliases

# At boundary: normalize before validation
raw_dict = {"schema_version": "v1", "skill_bucket": "1200-1400"}
normalized = normalize_dict_keys_to_aliases(raw_dict, MyModel)
model = MyModel.model_validate(normalized)
```

### Where Normalization Is NOT Required

Normalization is **not** required when:

1. **Keyword arguments are used** (Pydantic handles both snake_case and camelCase)
2. **JSON is already in camelCase** (by_alias=True serialization)
3. **Data originates from model.model_dump(by_alias=True)**

---

## Migration Guide

### For Tests

**Before (incorrect):**
```python
def test_model_validation():
    data = {
        "schema_version": "v1",  # snake_case
        "skill_bucket": "1200-1400",  # snake_case
    }
    model = MyModel.model_validate(data)  # ❌ Violates contract
```

**After (correct):**
```python
def test_model_validation():
    data = {
        "schemaVersion": "v1",  # camelCase alias
        "skillBucket": "1200-1400",  # camelCase alias
    }
    model = MyModel.model_validate(data)  # ✅ Complies with contract
```

**Alternative (also correct):**
```python
def test_model_validation():
    model = MyModel(
        schema_version="v1",  # snake_case keyword argument
        skill_bucket="1200-1400",  # snake_case keyword argument
    )  # ✅ Complies with contract
```

### For Feature Extractors

**Before (incorrect):**
```python
def extract_features(board):
    return MyModel.model_validate({
        "schema_version": "v1",  # snake_case
    })  # ❌ Violates contract
```

**After (correct):**
```python
def extract_features(board):
    return MyModel.model_validate({
        "schemaVersion": "v1",  # camelCase alias
    })  # ✅ Complies with contract
```

**Alternative (also correct):**
```python
def extract_features(board):
    return MyModel(
        schema_version="v1",  # snake_case keyword argument
    )  # ✅ Complies with contract
```

---

## Rationale

### Why Option A (Alias-Only Dict Inputs)?

1. **Cleanest mental model**: Dicts represent wire/JSON format (camelCase), Python code uses snake_case
2. **Aligns with JSON schemas**: JSON Schema uses camelCase, dicts should match
3. **Avoids Pydantic internals**: No reliance on `populate_by_name` or internal behavior
4. **Explicit and unambiguous**: No dual-key acceptance reduces complexity

### Why Not Option B (Dual-Key Acceptance)?

1. **Higher complexity**: Requires normalization everywhere
2. **Ambiguity**: Which key takes precedence?
3. **Maintenance burden**: More code paths to test and maintain

---

## Enforcement

### CI Enforcement

* Tests must comply with this contract
* CI will fail if tests violate contract semantics
* No exceptions or workarounds

### Code Review

* All dict-based model instantiation must use camelCase alias keys
* Boundary normalization must be explicit and visible
* No implicit normalization inside Pydantic models

---

## Related Documents

* `docs/contracts/CLI_CONTRACT.md` — CLI contract (established in M12)
* `docs/governance/supply_chain.md` — Supply-chain governance (established in M12)
* `docs/audit/DeferredIssuesRegistry.md` — PYDANTIC-DICT-CONTRACT-001 (resolved by this document)

---

## Version History

| Version | Date | Milestone | Change |
|---------|------|-----------|--------|
| 1.0 | 2026-02-01 | M13 | Initial contract established |

---

**This contract is FROZEN and immutable. Any changes require a new version and explicit governance review.**
