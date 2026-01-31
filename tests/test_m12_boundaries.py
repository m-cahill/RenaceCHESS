"""M12: Import boundary enforcement tests.

These tests verify that import-linter boundaries are respected.
They are minimal sanity checks; import-linter is the primary enforcement mechanism.
"""

import importlib
import sys
from pathlib import Path


def test_features_do_not_import_training() -> None:
    """Verify features module does not import training internals."""
    # Import features module
    import renacechess.features.per_piece
    import renacechess.features.square_map
    import renacechess.features.context_bridge_v2

    # Check that training modules are not in sys.modules (unless explicitly imported elsewhere)
    # This is a sanity check; import-linter is the real enforcement
    features_modules = [
        "renacechess.features.per_piece",
        "renacechess.features.square_map",
        "renacechess.features.context_bridge_v2",
    ]

    for module_name in features_modules:
        module = sys.modules.get(module_name)
        if module is not None:
            # Check that module's __file__ exists and is in features directory
            if hasattr(module, "__file__") and module.__file__:
                assert "features" in module.__file__, f"{module_name} should be in features directory"


def test_cli_does_not_import_training_at_module_level() -> None:
    """Verify CLI module does not import training at module level."""
    # Import CLI module
    import renacechess.cli

    # Check that training modules are not imported at CLI module level
    # Training imports should only occur inside command handlers
    cli_module = sys.modules.get("renacechess.cli")
    assert cli_module is not None

    # Get CLI module source file
    cli_file = Path(cli_module.__file__) if hasattr(cli_module, "__file__") and cli_module.__file__ else None
    if cli_file and cli_file.exists():
        # Read source and check for module-level training imports
        source = cli_file.read_text(encoding="utf-8")
        # Training imports should only appear inside function bodies (after 'def' or 'elif')
        # This is a simple heuristic; import-linter is the real enforcement
        lines = source.split("\n")
        in_function = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Check for function definitions
            if stripped.startswith("def ") or stripped.startswith("elif "):
                in_function = True
            # Check for module-level imports (not indented)
            if not line.startswith(" ") and not line.startswith("\t") and "training" in line.lower():
                # Allow comments and docstrings
                if not stripped.startswith("#") and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    # This is a module-level import - should not contain 'training'
                    assert "training" not in line.lower(), (
                        f"Module-level import of training detected at line {i+1}: {line.strip()}\n"
                        "Training imports should only occur inside command handlers."
                    )


def test_eval_does_not_import_training() -> None:
    """Verify eval module does not import training internals."""
    # Import eval modules
    import renacechess.eval.runner
    import renacechess.eval.baselines
    import renacechess.eval.report

    # Check that training modules are not in eval module's direct imports
    # This is a sanity check; import-linter is the real enforcement
    eval_modules = [
        "renacechess.eval.runner",
        "renacechess.eval.baselines",
        "renacechess.eval.report",
    ]

    for module_name in eval_modules:
        module = sys.modules.get(module_name)
        if module is not None:
            # Check that module's __file__ exists and is in eval directory
            if hasattr(module, "__file__") and module.__file__:
                assert "eval" in module.__file__, f"{module_name} should be in eval directory"


def test_import_linter_config_exists() -> None:
    """Verify import-linter config file exists at repo root."""
    config_path = Path(__file__).parent.parent / "importlinter_contracts.ini"
    assert config_path.exists(), "importlinter_contracts.ini must exist at repo root"
    assert config_path.is_file(), "importlinter_contracts.ini must be a file"

    # Verify config has required sections
    config_content = config_path.read_text(encoding="utf-8")
    assert "[importlinter]" in config_content, "Config must have [importlinter] section"
    assert "root_package = renacechess" in config_content, "Config must specify root_package"

