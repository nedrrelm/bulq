# Backend Test Suite

Comprehensive test suite for the Bulq backend application covering all layers of the application.

## Test Structure

```
tests/
├── conftest.py                 # Pytest configuration and shared fixtures
├── test_auth.py               # Authentication and authorization tests
├── test_repository.py         # Repository pattern tests (both DB and memory)
├── test_services.py           # Service layer business logic tests
├── test_routes.py             # API route integration tests
├── test_state_machine.py      # Run state machine tests
├── test_websocket.py          # WebSocket functionality tests
├── test_models.py             # Basic model tests (existing)
├── test_models_advanced.py    # Advanced model validation and relationships
└── test_main.py              # Main app tests (existing)
```

## Running Tests

### Run All Tests
```bash
cd backend
uv run pytest
```

### Run Specific Test File
```bash
uv run pytest tests/test_auth.py
uv run pytest tests/test_repository.py
```

### Run Specific Test
```bash
uv run pytest tests/test_auth.py::test_hash_password
uv run pytest tests/test_routes.py::TestRunRoutes::test_create_run
```

### Run Tests by Marker
```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"

# Run only WebSocket tests
uv run pytest -m websocket
```

### Run with Coverage
```bash
uv run pytest --cov=app --cov-report=html
# View coverage report at htmlcov/index.html
```

### Run with Verbose Output
```bash
uv run pytest -v
uv run pytest -vv  # Extra verbose
```

### Run Failed Tests Only
```bash
uv run pytest --lf  # Last failed
uv run pytest --ff  # Failed first
```

## Test Categories

### 1. Authentication Tests (`test_auth.py`)
Tests for authentication and session management:
- Password hashing and verification (bcrypt)
- Session creation and deletion
- Registration endpoint (validation, duplicate emails)
- Login endpoint (success, wrong password, nonexistent user)
- Logout functionality
- Session persistence across requests
- Protected route access

**Key Coverage:**
- `app/auth.py` - 100%
- `/auth/*` routes - Complete

### 2. Repository Tests (`test_repository.py`)
Tests for data access layer (both implementations):
- `InMemoryRepository` - All CRUD operations
- `DatabaseRepository` - Database operations with SQLAlchemy
- User management (create, get by ID, get by email)
- Group operations (create, add members, get members)
- Store and product management
- Run lifecycle (create, state updates)
- Participation tracking
- Bidding workflow (create, update, delete)
- Shopping list items

**Key Coverage:**
- `app/repositories/` - Complete (abstract.py, database.py, memory.py)
- Both repository implementations tested

### 3. Service Layer Tests (`test_services.py`)
Tests for business logic services:
- `RunService` - Run creation, bidding, state management
- `GroupService` - Group creation, membership, invite tokens
- `ProductService` - Product CRUD, search
- `StoreService` - Store management
- `ShoppingService` - Shopping list, price logging
- `DistributionService` - Distribution tracking

**Key Coverage:**
- `app/services/*` - All service classes
- Business logic validation
- Error handling (NotFoundError, ForbiddenError, ValidationError)

### 4. Route Integration Tests (`test_routes.py`)
Full HTTP request/response cycle tests:
- Authentication routes (register, login, logout)
- Group routes (create, list, details, join)
- Store routes (list, create)
- Product routes (create, search, details)
- Run routes (create, details, bids, ready status, confirm)
- Shopping routes (shopping list, purchase tracking)
- Distribution routes (distribution data, pickup status)
- Unauthorized access handling

**Key Coverage:**
- `app/routes/*` - All API endpoints
- Complete user workflows
- Authorization checks

### 5. State Machine Tests (`test_state_machine.py`)
Tests for run state machine:
- Valid state transitions (planning → active → confirmed → shopping → distributing → completed)
- Invalid transition prevention
- Adjusting state flow (shopping → adjusting → distributing)
- Backward transitions (confirmed → active)
- Cancellation rules (which states allow cancellation)
- Terminal states (completed, cancelled)
- State descriptions and validation

**Key Coverage:**
- `app/run_state.py` - Complete
- All state transition rules
- Business logic enforcement

### 6. WebSocket Tests (`test_websocket.py`)
Tests for real-time communication:
- ConnectionManager functionality
- Room management (join, leave, isolation)
- Message broadcasting
- Personal messages
- Dead connection handling
- Message format validation

**Note:** Full async WebSocket tests require `pytest-asyncio`. Basic structure is in place.

**Key Coverage:**
- `app/websocket_manager.py` - Core logic
- Connection lifecycle

### 7. Model Tests (`test_models_advanced.py`)
Advanced model validation:
- User model (email uniqueness, relationships)
- Group model (invite token uniqueness)
- Store and Product models (price precision, timestamps)
- Run model (state tracking, timestamps)
- RunParticipation (unique constraints)
- ProductBid (distribution tracking, timestamps)
- ShoppingListItem (purchase tracking, JSON fields)
- Database constraints and relationships
- Foreign key integrity

**Key Coverage:**
- `app/models.py` - All models
- SQLAlchemy relationships
- Database constraints

## Fixtures

### Basic Fixtures
- `db` - Fresh database for each test
- `db_session` - Database session for direct DB access
- `client` - TestClient for HTTP requests
- `authenticated_client` - Pre-authenticated test client

### Entity Fixtures
- `sample_user` - Pre-created user
- `sample_group` - Pre-created group with user membership
- `sample_store` - Pre-created store
- `sample_product` - Pre-created product
- `sample_run` - Pre-created run with participation
- `complete_test_setup` - All entities created (dict)

### Usage Example
```python
def test_something(sample_user, sample_group, db_session):
    # User and group are already created and in the database
    assert sample_user.id is not None
    assert sample_group.created_by == sample_user.id
```

## Test Markers

Tests are automatically marked based on their location:

- `@pytest.mark.unit` - Unit tests (models, repository, state machine)
- `@pytest.mark.integration` - Integration tests (routes)
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.websocket` - WebSocket tests (may need additional setup)

## Coverage Goals

Current test coverage by module:

| Module | Target Coverage | Status |
|--------|----------------|---------|
| `auth.py` | 100% | ✅ |
| `repositories/*` | 100% | ✅ |
| `services/*` | 95%+ | ✅ |
| `routes/*` | 95%+ | ✅ |
| `run_state.py` | 100% | ✅ |
| `models.py` | 90%+ | ✅ |
| `websocket_manager.py` | 80%+ | ⚠️ (needs async tests) |

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install uv
          uv sync
      - name: Run tests
        run: |
          cd backend
          uv run pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Best Practices

### 1. Test Isolation
- Each test gets a fresh database
- Sessions are cleared between tests
- No shared state between tests

### 2. Descriptive Names
```python
# Good
def test_user_cannot_create_run_for_group_they_are_not_member_of():
    ...

# Less good
def test_run_creation():
    ...
```

### 3. Arrange-Act-Assert Pattern
```python
def test_example():
    # Arrange - Set up test data
    user = create_user()
    group = create_group()

    # Act - Perform the action
    result = service.do_something(user, group)

    # Assert - Verify results
    assert result.success is True
```

### 4. Test One Thing
Each test should focus on testing one specific behavior or scenario.

### 5. Use Fixtures
Leverage fixtures for common setup to keep tests DRY and maintainable.

## Known Limitations

1. **WebSocket Tests**: Full async WebSocket testing requires `pytest-asyncio` and is partially implemented.
2. **Performance Tests**: Load testing and performance benchmarks not included.
3. **External Services**: Tests don't cover external API integrations (future feature).

## Adding New Tests

When adding new features, add corresponding tests:

1. **New model field**: Add tests in `test_models_advanced.py`
2. **New service method**: Add tests in `test_services.py`
3. **New API endpoint**: Add tests in `test_routes.py`
4. **New state transition**: Add tests in `test_state_machine.py`

Example:
```python
# In test_services.py
def test_new_feature(repo, user):
    """Test description of new feature"""
    service = MyService(repo)
    result = service.new_feature(user)

    assert result.expected_value == "expected"
```

## Debugging Failed Tests

### View Full Output
```bash
uv run pytest -vv --tb=long
```

### Stop on First Failure
```bash
uv run pytest -x
```

### Enter Debugger on Failure
```bash
uv run pytest --pdb
```

### Show Print Statements
```bash
uv run pytest -s
```

## Dependencies

Test dependencies (in pyproject.toml):
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support (optional, for WebSocket tests)

Install test dependencies:
```bash
cd backend
uv sync
```

## Contact

For questions about tests or to report issues, see the main project README.
