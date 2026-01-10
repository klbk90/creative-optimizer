# Tests for Creative Optimizer

Comprehensive test suite with unit, integration, and E2E tests.

## Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (isolated, fast)
│   ├── test_thompson_sampling.py
│   ├── test_markov_chain.py
│   └── test_security.py
├── integration/             # Integration tests (API endpoints)
│   ├── test_auth_api.py
│   ├── test_utm_api.py
│   └── test_creative_api.py
└── e2e/                     # End-to-end tests (full workflows)
    └── (coming soon)
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run unit tests only
```bash
pytest tests/unit/
```

### Run integration tests only
```bash
pytest tests/integration/
```

### Run specific test file
```bash
pytest tests/unit/test_thompson_sampling.py
```

### Run specific test
```bash
pytest tests/unit/test_thompson_sampling.py::TestThompsonSampling::test_sample_beta_distribution
```

### Run with markers
```bash
# Run only unit tests
pytest -m unit

# Run only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

Then open `htmlcov/index.html` in browser.

## Writing Tests

### Unit Test Example
```python
# tests/unit/test_my_utility.py
import pytest
from utils.my_utility import my_function

class TestMyUtility:
    def test_basic_functionality(self):
        result = my_function(input_data)
        assert result == expected_output
```

### Integration Test Example
```python
# tests/integration/test_my_api.py
import pytest

class TestMyAPI:
    def test_endpoint(self, client, auth_headers):
        response = client.get(
            "/api/v1/endpoint",
            headers=auth_headers
        )
        assert response.status_code == 200
```

## Fixtures

Available fixtures (from `conftest.py`):

- `test_db` - Clean test database (SQLite in-memory)
- `client` - FastAPI test client
- `sample_user` - Pre-created test user
- `auth_token` - JWT token for authenticated requests
- `auth_headers` - Authorization headers dict

## CI/CD Integration

Add to GitHub Actions:

```yaml
- name: Run tests
  run: |
    pip install pytest pytest-cov
    pytest --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Requirements

Install test dependencies:

```bash
pip install pytest pytest-cov pytest-asyncio httpx
```

Or add to `requirements-dev.txt`:
```
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
httpx==0.25.2
```

## Best Practices

1. **Keep tests isolated** - Each test should be independent
2. **Use fixtures** - Share common setup via fixtures
3. **Test edge cases** - Not just happy path
4. **Fast unit tests** - Unit tests should run in milliseconds
5. **Mock external services** - Don't call real APIs in tests
6. **Descriptive names** - Test names should explain what they test
7. **Assert clearly** - One concept per test

## Coverage Goals

- **Unit tests:** >80% coverage
- **Integration tests:** All API endpoints
- **E2E tests:** Critical user flows

## TODO

- [ ] Add E2E tests for complete workflows
- [ ] Add performance/load tests
- [ ] Add frontend tests (Vitest)
- [ ] Integrate with CI/CD pipeline
- [ ] Set up coverage reporting
- [ ] Add mock for external services (Claude API, Modash, etc.)
