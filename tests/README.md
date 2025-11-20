# DevScout Elite Platform - Tests

This directory contains test suites for the DevScout Elite Platform.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests for individual modules
│   ├── test_resume_parser.py
│   ├── test_nlp_extractor.py
│   ├── test_github_client.py
│   ├── test_metrics_calculator.py
│   └── test_data_quality.py
└── integration/             # Integration tests (TODO)
    └── test_pipeline_integration.py
```

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run unit tests only
```bash
pytest tests/unit/ -v
```

### Run with coverage
```bash
pytest tests/unit/ -v --cov=scripts --cov-report=html
```

### Run specific test file
```bash
pytest tests/unit/test_resume_parser.py -v
```

### Run specific test
```bash
pytest tests/unit/test_nlp_extractor.py::TestNLPExtractor::test_extract_skills -v
```

## Test Coverage Goals

- **Unit Tests**: >80% coverage for core modules
- **Integration Tests**: End-to-end pipeline workflows
- **Performance Tests**: Benchmark critical operations

## Writing Tests

Follow pytest conventions:
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

Example:
```python
import pytest
from scripts.parsers.resume_parser import ResumeParser

def test_resume_extraction():
    parser = ResumeParser()
    text = parser.extract_text("sample.pdf")
    assert len(text) > 0
```

## CI/CD Integration

Tests run automatically on:
- Push to main/develop branches
- Pull request creation
- Manual workflow dispatch

See `.github/workflows/ci.yml` for configuration.
