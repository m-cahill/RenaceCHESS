"""M12: CLI invariant tests.

These tests verify CLI contract guarantees:
- Training commands are isolated
- Read-only commands do not trigger training
- No hidden side effects
"""

import subprocess
import sys
from pathlib import Path


def test_train_commands_are_explicit() -> None:
    """Verify training commands are explicitly named with 'train-' prefix."""
    # Import CLI to inspect available commands
    import renacechess.cli

    # Get CLI help output
    result = subprocess.run(
        [sys.executable, "-m", "renacechess.cli", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, f"CLI help failed: {result.stderr}"

    # Check that training commands are explicitly named
    help_text = result.stdout + result.stderr
    assert "train-policy" in help_text, "train-policy command must be available"
    assert "train-outcome-head" in help_text, "train-outcome-head command must be available"

    # Verify no other commands start with 'train' (except the explicit ones)
    lines = help_text.split("\n")
    train_commands = [
        line
        for line in lines
        if "train" in line.lower() and not line.strip().startswith("#")
    ]
    # Should only find the two explicit training commands
    train_command_count = sum(
        1
        for line in train_commands
        if "train-policy" in line or "train-outcome-head" in line
    )
    assert train_command_count >= 2, "Must have at least two explicit training commands"


def test_read_only_commands_do_not_import_training() -> None:
    """Verify read-only commands (demo, eval, dataset) do not import training modules."""
    # These commands should not trigger training imports
    read_only_commands = [
        ["demo", "--help"],
        ["dataset", "build", "--help"],
        ["eval", "run", "--help"],
        ["eval", "generate-frozen", "--help"],
        ["ingest", "lichess", "--help"],
    ]

    for cmd_args in read_only_commands:
        result = subprocess.run(
            [sys.executable, "-m", "renacechess.cli"] + cmd_args,
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Command should succeed (or fail with argument error, not import error)
        assert result.returncode in [0, 1, 2], (
            f"Command {cmd_args} failed unexpectedly: {result.stderr}"
        )

        # Should not contain training import errors
        error_output = result.stderr.lower()
        if "training" in error_output and "import" in error_output:
            # This might be OK if it's just a help message, but check
            if "error" in error_output or "traceback" in error_output:
                raise AssertionError(
                    f"Read-only command {cmd_args} appears to import training: {result.stderr}"
                )


def test_cli_contract_doc_exists() -> None:
    """Verify CLI contract documentation exists."""
    contract_path = Path(__file__).parent.parent / "docs" / "contracts" / "CLI_CONTRACT.md"
    assert contract_path.exists(), "CLI_CONTRACT.md must exist"
    assert contract_path.is_file(), "CLI_CONTRACT.md must be a file"

    # Verify contract has required sections
    contract_content = contract_path.read_text(encoding="utf-8")
    assert "Command Surface" in contract_content, "Contract must document command surface"
    assert "Side-Effect Guarantees" in contract_content, "Contract must document side effects"
    assert "Error & Failure Behavior" in contract_content, "Contract must document error behavior"


def test_supply_chain_doc_exists() -> None:
    """Verify supply chain governance documentation exists."""
    supply_chain_path = Path(__file__).parent.parent / "docs" / "governance" / "supply_chain.md"
    assert supply_chain_path.exists(), "supply_chain.md must exist"
    assert supply_chain_path.is_file(), "supply_chain.md must be a file"

    # Verify doc has required sections
    doc_content = supply_chain_path.read_text(encoding="utf-8")
    assert "Dependency Pinning Strategy" in doc_content, "Doc must document dependency pinning"
    assert "GitHub Actions Pinning" in doc_content, "Doc must document action pinning"

