.PHONY: help install install-dev lint format-check type test test-fast docs-check boundary-check secret-scan secret-scan-no-git verify demo clean clean-coverage

help:
	@echo "RenaceCHESS developer shortcuts"
	@echo ""
	@echo "Targets:"
	@echo "  install-dev     Install package with dev dependencies (canonical)"
	@echo "  install         Alias for install-dev (backward compatible)"
	@echo "  lint            Run Ruff lint"
	@echo "  format-check    Check Ruff formatting"
	@echo "  type            Run mypy"
	@echo "  test            Run full pytest suite"
	@echo "  test-fast       Run public docs/boundary guardrail tests without coverage"
	@echo "  docs-check      Run docs navigation test"
	@echo "  boundary-check  Verify private paths are not tracked"
	@echo "  secret-scan     Scan git-tracked tree at HEAD via gitleaks (if installed)"
	@echo "  secret-scan-no-git  Same as secret-scan (uses git archive + gitleaks dir)"
	@echo "  verify          Run common pre-PR verification"
	@echo "  demo            Run sample demo command if sample data exists"
	@echo "  clean           Remove build artifacts and common caches"
	@echo "  clean-coverage  Remove local coverage artifacts"

install: install-dev

install-dev:
	python -m pip install -e ".[dev]"

lint:
	ruff check .

format-check:
	ruff format --check .

type:
	mypy src/renacechess

test:
	pytest

test-fast:
	pytest tests/test_m38_credential_scanner_config.py tests/test_m37_dx_shortcuts.py tests/test_m36_docs_navigation.py tests/test_m35_public_release_boundary.py --no-cov

docs-check:
	pytest tests/test_m36_docs_navigation.py --no-cov

boundary-check:
	python scripts/check_public_release_boundary.py
	git ls-files docs/prompts docs/foundationdocs .cursorrules

secret-scan:
	@if command -v gitleaks >/dev/null 2>&1; then \
		scan_root=$$(mktemp -d); \
		git archive HEAD | tar -x -C "$$scan_root"; \
		gitleaks dir "$$scan_root" --redact --config .gitleaks.toml; \
		rm -rf "$$scan_root"; \
	else \
		echo "gitleaks is not installed. Install it or rely on CI credential scanning."; \
	fi

secret-scan-no-git:
	@if command -v gitleaks >/dev/null 2>&1; then \
		scan_root=$$(mktemp -d); \
		git archive HEAD | tar -x -C "$$scan_root"; \
		gitleaks dir "$$scan_root" --redact --config .gitleaks.toml; \
		rm -rf "$$scan_root"; \
	else \
		echo "gitleaks is not installed. Install it or rely on CI credential scanning."; \
	fi

verify: boundary-check lint format-check type test-fast

demo:
	@if [ -f tests/data/sample.pgn ]; then \
		python -m renacechess.cli demo --pgn tests/data/sample.pgn --out demo.json; \
	else \
		echo "No tests/data/sample.pgn found; see docs/GETTING_STARTED.md for demo options."; \
	fi

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache/ .coverage htmlcov/ coverage.xml
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-coverage:
	python -c "from pathlib import Path; [p.unlink() for p in Path('.').glob('.coverage*') if p.is_file()]"
