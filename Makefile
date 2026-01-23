.PHONY: help lint type test demo clean install

help:
	@echo "RenaceCHESS Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make install    - Install dependencies"
	@echo "  make lint       - Run ruff lint and format check"
	@echo "  make type       - Run mypy type checking"
	@echo "  make test       - Run pytest with coverage"
	@echo "  make demo       - Generate demo payload"
	@echo "  make clean      - Clean build artifacts"

install:
	pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .

type:
	mypy src/renacechess

test:
	pytest

demo:
	python -m renacechess.cli demo --pgn tests/data/sample.pgn --out /tmp/demo.json
	@echo "Demo payload written to /tmp/demo.json"

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache/ .coverage htmlcov/ coverage.xml
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

