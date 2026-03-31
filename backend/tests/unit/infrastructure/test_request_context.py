"""Unit tests for request context management.

Tests cover:
- Request ID generation, storage, and retrieval
- Logger creation with request context
- Context isolation and thread safety
- Edge cases and error handling
"""

import logging
import uuid
from unittest.mock import MagicMock

import pytest

from app.infrastructure.request_context import (
    RequestContextLogger,
    generate_request_id,
    get_logger,
    get_request_id,
    set_request_id,
)


class TestRequestIDGeneration:
    """Test request ID generation."""

    def test_generate_request_id_returns_string(self):
        """Test that generate_request_id returns a string."""
        request_id = generate_request_id()

        assert isinstance(request_id, str)

    def test_generate_request_id_is_not_empty(self):
        """Test that generate_request_id returns non-empty string."""
        request_id = generate_request_id()

        assert len(request_id) > 0

    def test_generate_request_id_is_uuid_format(self):
        """Test that generate_request_id returns UUID format."""
        request_id = generate_request_id()

        # Should be able to parse as UUID
        try:
            uuid.UUID(request_id)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False

        assert is_valid_uuid

    def test_generate_request_id_creates_unique_ids(self):
        """Test that generate_request_id creates unique IDs."""
        ids = [generate_request_id() for _ in range(100)]

        # All IDs should be unique
        assert len(set(ids)) == 100

    def test_different_calls_produce_different_ids(self):
        """Test that different calls produce different request IDs."""
        id1 = generate_request_id()
        id2 = generate_request_id()
        id3 = generate_request_id()

        assert id1 != id2
        assert id2 != id3
        assert id1 != id3


class TestRequestIDStorage:
    """Test request ID storage and retrieval."""

    def test_set_request_id_stores_id(self):
        """Test that set_request_id stores ID in context."""
        request_id = 'test-request-id-123'

        set_request_id(request_id)
        result = get_request_id()

        assert result == request_id

    def test_get_request_id_retrieves_stored_id(self):
        """Test that get_request_id retrieves stored ID."""
        request_id = 'test-request-id-456'

        set_request_id(request_id)
        result = get_request_id()

        assert result == request_id

    def test_get_request_id_returns_none_when_not_set(self):
        """Test that get_request_id returns None when not set."""
        # Clear any existing request ID
        from app.infrastructure.request_context import request_id_var

        request_id_var.set(None)

        result = get_request_id()

        assert result is None

    def test_multiple_set_request_id_calls_overwrite(self):
        """Test that multiple set_request_id calls overwrite previous value."""
        set_request_id('first-id')
        set_request_id('second-id')
        set_request_id('third-id')

        result = get_request_id()

        assert result == 'third-id'

    def test_request_id_with_empty_string(self):
        """Test setting request ID with empty string."""
        set_request_id('')

        result = get_request_id()

        assert result == ''

    def test_request_id_with_very_long_string(self):
        """Test setting request ID with very long string."""
        long_id = 'a' * 1000

        set_request_id(long_id)
        result = get_request_id()

        assert result == long_id

    def test_request_id_with_special_characters(self):
        """Test setting request ID with special characters."""
        special_id = 'request-@#$%^&*()_+-=[]{}|;:,.<>?/'

        set_request_id(special_id)
        result = get_request_id()

        assert result == special_id

    def test_request_id_with_uuid_format(self):
        """Test setting request ID with UUID format."""
        uuid_id = '550e8400-e29b-41d4-a716-446655440000'

        set_request_id(uuid_id)
        result = get_request_id()

        assert result == uuid_id


class TestGetLogger:
    """Test logger creation with request context."""

    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger('test_module')

        assert isinstance(logger, RequestContextLogger)

    def test_get_logger_with_module_name(self):
        """Test get_logger with module name."""
        logger = get_logger('app.test_module')

        assert isinstance(logger, RequestContextLogger)
        assert isinstance(logger._logger, logging.Logger)

    def test_get_logger_with_empty_string_name(self):
        """Test get_logger with empty string name."""
        logger = get_logger('')

        assert isinstance(logger, RequestContextLogger)

    def test_get_logger_wraps_standard_logger(self):
        """Test that get_logger wraps a standard Python logger."""
        logger = get_logger('test_module')

        assert hasattr(logger, '_logger')
        assert isinstance(logger._logger, logging.Logger)

    def test_get_logger_with_different_names_creates_different_loggers(self):
        """Test that loggers with different names have different underlying loggers."""
        logger1 = get_logger('module1')
        logger2 = get_logger('module2')

        assert logger1._logger.name == 'module1'
        assert logger2._logger.name == 'module2'

    def test_get_logger_with_same_name_returns_same_underlying_logger(self):
        """Test that get_logger with same name returns same underlying logger."""
        logger1 = get_logger('test_module')
        logger2 = get_logger('test_module')

        # Should wrap the same underlying logger
        assert logger1._logger.name == logger2._logger.name


class TestRequestContextLogger:
    """Test RequestContextLogger functionality."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return MagicMock(spec=logging.Logger)

    @pytest.fixture
    def context_logger(self, mock_logger):
        """Create a RequestContextLogger with mock logger."""
        return RequestContextLogger(mock_logger)

    def test_logger_has_debug_method(self, context_logger):
        """Test that logger has debug method."""
        assert hasattr(context_logger, 'debug')
        assert callable(context_logger.debug)

    def test_logger_has_info_method(self, context_logger):
        """Test that logger has info method."""
        assert hasattr(context_logger, 'info')
        assert callable(context_logger.info)

    def test_logger_has_warning_method(self, context_logger):
        """Test that logger has warning method."""
        assert hasattr(context_logger, 'warning')
        assert callable(context_logger.warning)

    def test_logger_has_error_method(self, context_logger):
        """Test that logger has error method."""
        assert hasattr(context_logger, 'error')
        assert callable(context_logger.error)

    def test_logger_has_critical_method(self, context_logger):
        """Test that logger has critical method."""
        assert hasattr(context_logger, 'critical')
        assert callable(context_logger.critical)

    def test_logger_has_exception_method(self, context_logger):
        """Test that logger has exception method."""
        assert hasattr(context_logger, 'exception')
        assert callable(context_logger.exception)

    def test_debug_includes_request_id_when_set(self, context_logger, mock_logger):
        """Test that debug log includes request_id when set."""
        set_request_id('test-request-123')

        context_logger.debug('Debug message')

        # Check that the underlying logger was called with extra containing request_id
        mock_logger.debug.assert_called_once()
        call_kwargs = mock_logger.debug.call_args[1]
        assert 'extra' in call_kwargs
        assert call_kwargs['extra']['request_id'] == 'test-request-123'

    def test_info_includes_request_id_when_set(self, context_logger, mock_logger):
        """Test that info log includes request_id when set."""
        set_request_id('test-request-456')

        context_logger.info('Info message')

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs['extra']['request_id'] == 'test-request-456'

    def test_warning_includes_request_id_when_set(self, context_logger, mock_logger):
        """Test that warning log includes request_id when set."""
        set_request_id('test-request-789')

        context_logger.warning('Warning message')

        mock_logger.warning.assert_called_once()
        call_kwargs = mock_logger.warning.call_args[1]
        assert call_kwargs['extra']['request_id'] == 'test-request-789'

    def test_error_includes_request_id_when_set(self, context_logger, mock_logger):
        """Test that error log includes request_id when set."""
        set_request_id('test-request-error')

        context_logger.error('Error message')

        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args[1]
        assert call_kwargs['extra']['request_id'] == 'test-request-error'

    def test_critical_includes_request_id_when_set(self, context_logger, mock_logger):
        """Test that critical log includes request_id when set."""
        set_request_id('test-request-critical')

        context_logger.critical('Critical message')

        mock_logger.critical.assert_called_once()
        call_kwargs = mock_logger.critical.call_args[1]
        assert call_kwargs['extra']['request_id'] == 'test-request-critical'

    def test_exception_includes_request_id_when_set(self, context_logger, mock_logger):
        """Test that exception log includes request_id when set."""
        set_request_id('test-request-exception')

        context_logger.exception('Exception message')

        mock_logger.exception.assert_called_once()
        call_kwargs = mock_logger.exception.call_args[1]
        assert call_kwargs['extra']['request_id'] == 'test-request-exception'

    def test_logger_works_without_request_id_set(self, context_logger, mock_logger):
        """Test that logger works when request_id is not set."""
        # Clear request ID
        from app.infrastructure.request_context import request_id_var

        request_id_var.set(None)

        context_logger.info('Info message')

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        # Should have extra dict but no request_id
        assert 'extra' in call_kwargs
        assert (
            'request_id' not in call_kwargs['extra'] or call_kwargs['extra']['request_id'] is None
        )

    def test_logger_preserves_existing_extra_fields(self, context_logger, mock_logger):
        """Test that logger preserves existing extra fields."""
        set_request_id('test-request-123')

        context_logger.info('Info message', extra={'custom_field': 'custom_value'})

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs['extra']['request_id'] == 'test-request-123'
        assert call_kwargs['extra']['custom_field'] == 'custom_value'

    def test_logger_does_not_overwrite_existing_request_id_in_extra(
        self, context_logger, mock_logger
    ):
        """Test that logger doesn't overwrite existing request_id in extra."""
        set_request_id('context-request-id')

        context_logger.info('Info message', extra={'request_id': 'explicit-request-id'})

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        # Should not overwrite explicit request_id
        assert call_kwargs['extra']['request_id'] == 'explicit-request-id'

    def test_logger_delegates_to_underlying_logger(self, context_logger, mock_logger):
        """Test that logger delegates attribute access to underlying logger."""
        # Set a name attribute on the mock logger
        mock_logger.name = 'test_logger_name'

        # Access an attribute not defined on RequestContextLogger
        result = context_logger.name

        assert result == 'test_logger_name'

    def test_logger_with_args(self, context_logger, mock_logger):
        """Test logger with positional arguments."""
        set_request_id('test-request-123')

        context_logger.info('Message with %s and %d', 'string', 42)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0]
        assert call_args[0] == 'Message with %s and %d'
        assert call_args[1] == 'string'
        assert call_args[2] == 42

    def test_logger_with_kwargs(self, context_logger, mock_logger):
        """Test logger with keyword arguments."""
        set_request_id('test-request-123')

        context_logger.info('Info message', exc_info=True)

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs['exc_info'] is True


class TestContextIsolation:
    """Test context isolation between different execution contexts."""

    def test_context_is_isolated_per_request(self):
        """Test that request IDs are isolated per context."""
        set_request_id('request-1')

        # Simulate different context (in practice this would be different async tasks or threads)
        assert get_request_id() == 'request-1'

        set_request_id('request-2')
        assert get_request_id() == 'request-2'

    def test_clearing_request_id(self):
        """Test clearing request ID by setting to None."""
        set_request_id('test-request-123')
        assert get_request_id() == 'test-request-123'

        set_request_id(None)
        assert get_request_id() is None

    def test_request_id_isolation_in_sequential_requests(self):
        """Test request ID isolation in sequential request simulation."""
        # Simulate first request
        set_request_id('request-1')
        assert get_request_id() == 'request-1'

        # Simulate second request (clear and set new ID)
        set_request_id('request-2')
        assert get_request_id() == 'request-2'

        # Simulate third request
        set_request_id('request-3')
        assert get_request_id() == 'request-3'

    def test_multiple_loggers_share_same_request_id(self):
        """Test that multiple loggers share the same request ID from context."""
        set_request_id('shared-request-123')

        logger1 = get_logger('module1')
        logger2 = get_logger('module2')

        # Both loggers should use the same request ID from context
        mock_logger1 = MagicMock()
        mock_logger2 = MagicMock()
        logger1._logger = mock_logger1
        logger2._logger = mock_logger2

        logger1.info('Message from logger1')
        logger2.info('Message from logger2')

        # Both should have used the same request ID
        assert mock_logger1.info.call_args[1]['extra']['request_id'] == 'shared-request-123'
        assert mock_logger2.info.call_args[1]['extra']['request_id'] == 'shared-request-123'


class TestRequestContextEdgeCases:
    """Test edge cases in request context."""

    def test_set_request_id_with_none(self):
        """Test setting request ID to None."""
        set_request_id('test-request-123')
        set_request_id(None)

        result = get_request_id()
        assert result is None

    def test_get_request_id_default_value(self):
        """Test that get_request_id returns None by default."""
        # Create a new context variable state
        from app.infrastructure.request_context import request_id_var

        request_id_var.set(None)

        result = get_request_id()
        assert result is None

    def test_generate_and_set_request_id_flow(self):
        """Test typical flow of generating and setting request ID."""
        request_id = generate_request_id()
        set_request_id(request_id)

        result = get_request_id()
        assert result == request_id

    def test_logger_with_special_characters_in_message(self):
        """Test logger with special characters in message."""
        logger = get_logger('test_module')
        mock_logger = MagicMock()
        logger._logger = mock_logger

        set_request_id('test-request-123')

        special_message = 'Message with 🔐 unicode and @#$%^&*() special chars'
        logger.info(special_message)

        mock_logger.info.assert_called_once()
        assert mock_logger.info.call_args[0][0] == special_message

    def test_logger_with_empty_message(self):
        """Test logger with empty message."""
        logger = get_logger('test_module')
        mock_logger = MagicMock()
        logger._logger = mock_logger

        set_request_id('test-request-123')

        logger.info('')

        mock_logger.info.assert_called_once()

    def test_request_id_format_from_generate_request_id(self):
        """Test that request IDs from generate_request_id are valid UUIDs."""
        for _ in range(10):
            request_id = generate_request_id()

            # Should be valid UUID
            try:
                uuid_obj = uuid.UUID(request_id)
                assert str(uuid_obj) == request_id
            except ValueError:
                pytest.fail(f'Generated request_id "{request_id}" is not a valid UUID')

    def test_logger_getattr_delegation(self):
        """Test that logger __getattr__ properly delegates to underlying logger."""
        logger = get_logger('test_module')

        # Access standard logger attributes
        assert hasattr(logger, 'name')
        assert hasattr(logger, 'level')
        assert hasattr(logger, 'parent')
        assert hasattr(logger, 'propagate')

    def test_empty_extra_dict_handling(self):
        """Test logger with empty extra dict."""
        logger = get_logger('test_module')
        mock_logger = MagicMock()
        logger._logger = mock_logger

        set_request_id('test-request-123')

        logger.info('Message', extra={})

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs['extra']['request_id'] == 'test-request-123'

    @pytest.mark.parametrize(
        'log_level',
        ['debug', 'info', 'warning', 'error', 'critical', 'exception'],
    )
    def test_all_log_levels_include_request_id(self, log_level):
        """Test that all log levels include request_id."""
        logger = get_logger('test_module')
        mock_logger = MagicMock()
        logger._logger = mock_logger

        set_request_id('test-request-all-levels')

        log_method = getattr(logger, log_level)
        log_method('Test message')

        underlying_log_method = getattr(mock_logger, log_level)
        underlying_log_method.assert_called_once()
        call_kwargs = underlying_log_method.call_args[1]
        assert call_kwargs['extra']['request_id'] == 'test-request-all-levels'
