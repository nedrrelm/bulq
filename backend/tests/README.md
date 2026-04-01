# Backend Tests

Comprehensive unit test suite for the Bulq backend API.

## Overview

- **Total Tests**: 1,860
- **Coverage**: 57%
- **Test Execution Time**: ~25 seconds
- **Test Files**: 46

## Test Structure

```
tests/
├── unit/
│   ├── core/               # Domain logic tests (324 tests)
│   ├── infrastructure/     # Infrastructure tests (229 tests)
│   ├── repositories/       # Data access tests (589 tests)
│   ├── services/           # Business logic tests (326 tests)
│   └── schemas/            # API schema tests (267 tests)
└── conftest.py             # Shared fixtures
```

## Running Tests

### All Tests
```bash
just test
```

### Verbose Output
```bash
just test -v
```

### Specific Test File
```bash
just test tests/unit/services/test_run_service.py -v
```

### With Coverage
```bash
just test --cov=app --cov-report=html
```

### By Test Class
```bash
just test tests/unit/services/test_run_service.py::TestCreateRun -v
```

### By Test Method
```bash
just test tests/unit/services/test_run_service.py::TestCreateRun::test_create_run_success -v
```

### By Category
```bash
# Core tests
just test tests/unit/core -v

# Infrastructure tests
just test tests/unit/infrastructure -v

# Repository tests
just test tests/unit/repositories -v

# Service tests
just test tests/unit/services -v

# Schema tests
just test tests/unit/schemas -v
```

## Test Categories

### Core Tests (324 tests, 4 files)
Domain logic and state machine validation:
- **test_error_codes.py**: Error code validation and structure (28 tests)
- **test_exceptions.py**: Exception hierarchy and behavior (80 tests)
- **test_run_state_machine.py**: State transitions and permissions (215 tests)
- **test_success_codes.py**: Success code validation (1 test)

**Coverage**: 100% for all core modules

### Infrastructure Tests (229 tests, 4 files)
Core infrastructure components:
- **test_auth.py**: Authentication and authorization (38 tests)
- **test_config.py**: Configuration management (58 tests)
- **test_event_bus.py**: Event bus functionality (53 tests)
- **test_request_context.py**: Request context management (80 tests)

**Coverage**:
- auth.py: 100%
- config.py: 100%
- event_bus.py: 100%
- request_context.py: 100%
- session_store.py: 94%

### Repository Tests (589 tests, 9 files)
Data access layer for all entities:
- **test_bid_repository.py**: Bid operations (60 tests)
- **test_group_repository.py**: Group operations (66 tests)
- **test_notification_repository.py**: Notification operations (48 tests)
- **test_product_repository.py**: Product operations (72 tests)
- **test_reassignment_repository.py**: Reassignment operations (50 tests)
- **test_run_repository.py**: Run operations (80 tests)
- **test_shopping_repository.py**: Shopping operations (62 tests)
- **test_store_repository.py**: Store operations (62 tests)
- **test_user_repository.py**: User operations (89 tests)

**Coverage**:
- Memory implementations: 99-100%
- Abstract interfaces: 69-73%
- Database implementations: 23-42% (not primary focus)

### Service Tests (326 tests, 14 files)
Business logic for all services:
- **test_admin_service.py**: Admin operations (5 tests)
- **test_bid_service.py**: Bid management (28 tests)
- **test_distribution_service.py**: Distribution logic (14 tests)
- **test_group_invite_service.py**: Group invitations (20 tests)
- **test_group_management_service.py**: Group management (4 tests)
- **test_group_membership_service.py**: Group memberships (32 tests)
- **test_group_query_service.py**: Group queries (11 tests)
- **test_notification_service.py**: Notifications (12 tests)
- **test_product_service.py**: Product management (10 tests)
- **test_reassignment_service.py**: Reassignments (16 tests)
- **test_run_notification_service.py**: Run notifications (2 tests)
- **test_run_service.py**: Run management (96 tests)
- **test_run_state_service.py**: Run state transitions (66 tests)
- **test_shopping_service.py**: Shopping operations (10 tests)

**Coverage**:
- High coverage services: 80-96%
- Core business services: 66-91%
- Admin service: 50%

### Schema Tests (267 tests, 12 files)
Pydantic model validation:
- **test_admin_schemas.py**: Admin schemas (20 tests)
- **test_auth_schemas.py**: Authentication schemas (32 tests)
- **test_common_schemas.py**: Common schemas (12 tests)
- **test_distribution_schemas.py**: Distribution schemas (10 tests)
- **test_group_schemas.py**: Group schemas (28 tests)
- **test_notification_schemas.py**: Notification schemas (8 tests)
- **test_product_schemas.py**: Product schemas (20 tests)
- **test_reassignment_schemas.py**: Reassignment schemas (10 tests)
- **test_run_schemas.py**: Run schemas (56 tests)
- **test_search_schemas.py**: Search schemas (8 tests)
- **test_shopping_schemas.py**: Shopping schemas (30 tests)
- **test_store_schemas.py**: Store schemas (18 tests)

**Coverage**: 100% for all schema modules

## Test Patterns

### Mocking
All tests use `unittest.mock` to isolate components:
- Repository methods mocked in service tests
- Event bus mocked to verify emissions
- External dependencies fully isolated
- No database required for unit tests

### Fixtures
Shared fixtures in `conftest.py`:
- **Users**: `test_user`, `test_admin_user`, `test_organizer`
- **Repositories**: `mock_*_repo` for all 9 repositories
- **Infrastructure**: `mock_event_bus`, `mock_config`
- **Test Data**: Pre-configured runs, groups, bids, products

### Assertions
- Use `pytest.raises` for exception testing
- Verify mock calls with `assert_called_once_with()`
- Check event emissions with event bus mocks
- Validate data structures and transformations

### Test Organization
Each test class follows the pattern:
- **Setup**: Mock dependencies, create test data
- **Action**: Execute the method under test
- **Assert**: Verify results, mock calls, events

## Coverage Report

### Overall Coverage: 57%

**High Coverage Modules (90-100%)**:
- Core domain logic (100%)
- Schema validation (100%)
- Memory repositories (99-100%)
- Infrastructure components (94-100%)
- Group services (93-100%)
- Product service (94%)
- Base service (94%)

**Good Coverage Modules (80-90%)**:
- Bid service (81%)
- Distribution service (80%)
- Reassignment service (84%)
- Notification service (88%)
- Background tasks (88%)
- Run state service (91%)

**Moderate Coverage Modules (50-79%)**:
- Run service (66%)
- Abstract repositories (69-73%)
- Transaction management (65%)
- User repository memory (64%)

**Low Coverage Modules (<50%)**:
- API routes (0% - integration test focus)
- Database implementations (23-42% - not primary focus)
- Event handlers (0% - integration test focus)
- Error handlers (0% - integration test focus)
- Main application (0% - integration test focus)
- Shopping service (46%)
- Admin service (50%)
- WebSocket manager (41%)

### Coverage Notes

The 57% overall coverage is expected because:
1. **API routes** (0%): Integration tests handle endpoint testing
2. **Database implementations** (23-42%): Memory repos are primary test target
3. **Event handlers** (0%): Tested through integration tests
4. **Main application** (0%): Tested through integration tests
5. **Scripts** (0%): Utility scripts, not core logic

**Focus areas have excellent coverage**:
- Core business logic: 80-100%
- Data access abstractions: 99-100%
- Schema validation: 100%
- Infrastructure: 94-100%

## Test Results Summary

```
====================== 1860 passed, 2 warnings in 24.79s =======================
```

- **Total Tests**: 1,860
- **Passed**: 1,860 (100%)
- **Failed**: 0
- **Skipped**: 0
- **Warnings**: 2 (minor)
- **Execution Time**: 24.79 seconds
- **Average per test**: ~13ms

## Contributing

When adding new features:

1. **Write tests first** (TDD approach)
2. **Achieve >80% coverage** for new code
3. **Follow existing patterns**:
   - One test file per source file
   - Descriptive test class names (TestFeatureName)
   - Clear test method names (test_action_scenario_outcome)
   - Use fixtures from conftest.py
4. **Mock external dependencies**
5. **Verify event emissions** when applicable
6. **Run linting**: `just lint`
7. **Ensure all tests pass**: `just test`

## Code Quality

All tests pass code quality checks:
- **Ruff format**: All files formatted correctly
- **Ruff lint**: Zero errors, zero warnings
- **Type hints**: Consistent across test suite
- **Naming conventions**: PEP 8 compliant

## Viewing Coverage Reports

After running tests with coverage:
```bash
just test --cov=app --cov-report=html
```

Open the HTML report:
```bash
# Linux
xdg-open htmlcov/index.html

# macOS
open htmlcov/index.html
```

## Test Performance

The test suite is optimized for speed:
- **Parallel execution**: Can run with `pytest -n auto`
- **Fast mocks**: No database or network calls
- **Isolated tests**: No shared state between tests
- **Quick fixtures**: Efficient setup and teardown

To run tests in parallel:
```bash
just test -n auto
```

## Continuous Integration

Tests run automatically on:
- Every pull request
- Every push to main branch
- Pre-deployment checks

CI requirements:
- All 1,860 tests must pass
- Lint checks must pass
- Coverage must maintain or improve

---

**Last Updated**: 2026-04-01
**Test Suite Version**: 1.0.0
**Total Lines of Test Code**: ~15,000+
