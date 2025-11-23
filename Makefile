.PHONY: help test test-docker test-local test-syntax test-config test-utils test-docs build-test clean

help:
	@echo "Interactive Wand - Testing Commands"
	@echo ""
	@echo "Local Testing (macOS/Linux):"
	@echo "  make test-local       Run all tests locally"
	@echo "  make test-syntax      Run syntax validation only"
	@echo "  make test-config      Run config validation only"
	@echo "  make test-utils       Run utils tests only"
	@echo "  make test-docs        Run documentation tests only"
	@echo ""
	@echo "Docker Testing:"
	@echo "  make test-docker      Run all tests in Docker"
	@echo "  make build-test       Build test Docker image"
	@echo "  make test-docker-all  Run comprehensive Docker test suite"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove test artifacts and cache"

# Local testing (no Docker required)
test-local:
	@echo "Running all tests locally..."
	@python3 tests/run_all_tests.py

test-syntax:
	@echo "Running syntax validation..."
	@python3 tests/test_syntax.py

test-config:
	@echo "Running configuration tests..."
	@python3 tests/test_config.py

test-utils:
	@echo "Running utils module tests..."
	@python3 tests/test_utils.py

test-docs:
	@echo "Running documentation tests..."
	@python3 tests/test_documentation.py

# Docker testing
build-test:
	@echo "Building test Docker image..."
	@docker build -f Dockerfile.test -t interactive-wand-test .

test-docker: build-test
	@echo "Running tests in Docker..."
	@docker run --rm interactive-wand-test python3 tests/run_all_tests.py

test-docker-all: build-test
	@echo "Running comprehensive Docker test suite..."
	@docker-compose -f docker-compose.test.yml run --rm test-all

test-docker-syntax: build-test
	@docker-compose -f docker-compose.test.yml run --rm test-syntax

test-docker-config: build-test
	@docker-compose -f docker-compose.test.yml run --rm test-config

test-docker-utils: build-test
	@docker-compose -f docker-compose.test.yml run --rm test-utils

test-docker-docs: build-test
	@docker-compose -f docker-compose.test.yml run --rm test-docs

# Default target
test: test-local

# Cleanup
clean:
	@echo "Cleaning up test artifacts..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete!"
