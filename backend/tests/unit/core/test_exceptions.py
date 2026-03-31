"""Unit tests for custom exception classes.

Tests cover:
- AppException base class initialization and behavior
- All exception subclasses (NotFoundError, UnauthorizedError, ForbiddenError,
  ValidationError, ConflictError, BadRequestError, ConfigurationError)
- Status code validation for all exception types
- Auto-generated messages, custom messages, and details
- Edge cases and exception raising/catching behavior
"""

import pytest
from fastapi import status

from app.core.exceptions import (
    AppException,
    BadRequestError,
    ConfigurationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


class TestAppExceptionBaseClass:
    """Test the AppException base class."""

    def test_initialization_with_all_parameters(self):
        """Test AppException initialization with all parameters provided."""
        exc = AppException(
            code='TEST_ERROR',
            message='Test error message',
            status_code=418,
            user_id='123',
            action='test_action',
        )

        assert exc.code == 'TEST_ERROR'
        assert exc.message == 'Test error message'
        assert exc.status_code == 418
        assert exc.details == {'user_id': '123', 'action': 'test_action'}

    def test_initialization_with_code_only(self):
        """Test AppException initialization with only code parameter."""
        exc = AppException(code='SIMPLE_ERROR')

        assert exc.code == 'SIMPLE_ERROR'
        assert exc.message == 'Error: SIMPLE_ERROR'
        assert exc.status_code == 500
        assert exc.details == {}

    def test_auto_generated_message_when_message_is_none(self):
        """Test that message is auto-generated when None is provided."""
        exc = AppException(code='AUTO_MESSAGE_ERROR', message=None)

        assert exc.message == 'Error: AUTO_MESSAGE_ERROR'

    def test_default_status_code_is_500(self):
        """Test that default status code is 500 (Internal Server Error)."""
        exc = AppException(code='DEFAULT_STATUS')

        assert exc.status_code == 500
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_custom_status_code_override(self):
        """Test that status code can be overridden during initialization."""
        exc = AppException(code='CUSTOM_STATUS', status_code=403)

        assert exc.status_code == 403

    def test_details_kwargs_are_stored_correctly(self):
        """Test that additional kwargs are stored in details dict."""
        exc = AppException(
            code='DETAILS_TEST',
            resource='user',
            resource_id='456',
            operation='delete',
        )

        assert exc.details['resource'] == 'user'
        assert exc.details['resource_id'] == '456'
        assert exc.details['operation'] == 'delete'
        assert len(exc.details) == 3

    def test_exception_message_string_representation(self):
        """Test that exception string representation uses the message."""
        exc = AppException(code='STRING_TEST', message='This is the exception message')

        assert str(exc) == 'This is the exception message'

    def test_empty_details_dict(self):
        """Test initialization with no additional details."""
        exc = AppException(code='NO_DETAILS', message='No details here')

        assert exc.details == {}

    def test_multiple_details_kwargs(self):
        """Test storing multiple detail fields."""
        exc = AppException(
            code='MANY_DETAILS',
            field1='value1',
            field2='value2',
            field3='value3',
            field4='value4',
        )

        assert len(exc.details) == 4
        assert exc.details['field1'] == 'value1'
        assert exc.details['field4'] == 'value4'

    def test_details_with_none_values(self):
        """Test that None values in details are stored correctly."""
        exc = AppException(
            code='NONE_VALUES',
            optional_field=None,
            required_field='value',
        )

        assert exc.details['optional_field'] is None
        assert exc.details['required_field'] == 'value'

    def test_exception_can_be_raised_and_caught(self):
        """Test that AppException can be raised and caught correctly."""
        with pytest.raises(AppException) as exc_info:
            raise AppException(code='RAISED_ERROR', test_detail='test')

        assert exc_info.value.code == 'RAISED_ERROR'
        assert exc_info.value.details['test_detail'] == 'test'

    def test_exception_inherits_from_exception(self):
        """Test that AppException inherits from built-in Exception."""
        exc = AppException(code='INHERITANCE_TEST')

        assert isinstance(exc, Exception)


class TestNotFoundError:
    """Test the NotFoundError exception class."""

    def test_default_status_code_is_404(self):
        """Test that NotFoundError has status code 404."""
        exc = NotFoundError(code='RESOURCE_NOT_FOUND')

        assert exc.status_code == 404
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_initialization_with_code_only(self):
        """Test initialization with just code parameter."""
        exc = NotFoundError(code='USER_NOT_FOUND')

        assert exc.code == 'USER_NOT_FOUND'
        assert exc.message == 'Error: USER_NOT_FOUND'
        assert exc.status_code == 404
        assert exc.details == {}

    def test_initialization_with_code_and_message(self):
        """Test initialization with code and custom message."""
        exc = NotFoundError(code='RUN_NOT_FOUND', message='Run was not found in database')

        assert exc.code == 'RUN_NOT_FOUND'
        assert exc.message == 'Run was not found in database'
        assert exc.status_code == 404

    def test_initialization_with_code_and_details(self):
        """Test initialization with code and details kwargs."""
        exc = NotFoundError(code='PRODUCT_NOT_FOUND', product_id='789', group_id='group-123')

        assert exc.code == 'PRODUCT_NOT_FOUND'
        assert exc.details['product_id'] == '789'
        assert exc.details['group_id'] == 'group-123'
        assert exc.status_code == 404

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        exc = NotFoundError(
            code='BID_NOT_FOUND',
            message='Bid does not exist',
            bid_id='bid-456',
            user_id='user-789',
        )

        assert exc.code == 'BID_NOT_FOUND'
        assert exc.message == 'Bid does not exist'
        assert exc.status_code == 404
        assert exc.details['bid_id'] == 'bid-456'
        assert exc.details['user_id'] == 'user-789'

    def test_inherits_from_app_exception(self):
        """Test that NotFoundError inherits from AppException."""
        exc = NotFoundError(code='INHERITANCE_TEST')

        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)


class TestUnauthorizedError:
    """Test the UnauthorizedError exception class."""

    def test_default_status_code_is_401(self):
        """Test that UnauthorizedError has status code 401."""
        exc = UnauthorizedError()

        assert exc.status_code == 401
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_default_code_is_auth_required(self):
        """Test that default code is AUTH_REQUIRED."""
        exc = UnauthorizedError()

        assert exc.code == 'AUTH_REQUIRED'
        assert exc.message == 'Error: AUTH_REQUIRED'

    def test_initialization_with_custom_code(self):
        """Test initialization with custom code."""
        exc = UnauthorizedError(code='AUTH_SESSION_EXPIRED')

        assert exc.code == 'AUTH_SESSION_EXPIRED'
        assert exc.status_code == 401

    def test_initialization_with_code_and_message(self):
        """Test initialization with code and custom message."""
        exc = UnauthorizedError(code='AUTH_TOKEN_INVALID', message='Token is not valid')

        assert exc.code == 'AUTH_TOKEN_INVALID'
        assert exc.message == 'Token is not valid'
        assert exc.status_code == 401

    def test_initialization_with_code_and_details(self):
        """Test initialization with code and details kwargs."""
        exc = UnauthorizedError(code='AUTH_EXPIRED', token_id='token-123', expired_at='2026-01-01')

        assert exc.code == 'AUTH_EXPIRED'
        assert exc.details['token_id'] == 'token-123'
        assert exc.details['expired_at'] == '2026-01-01'

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        exc = UnauthorizedError(
            code='AUTH_MISSING',
            message='No authentication provided',
            endpoint='/api/v1/runs',
        )

        assert exc.code == 'AUTH_MISSING'
        assert exc.message == 'No authentication provided'
        assert exc.details['endpoint'] == '/api/v1/runs'

    def test_inherits_from_app_exception(self):
        """Test that UnauthorizedError inherits from AppException."""
        exc = UnauthorizedError()

        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)


class TestForbiddenError:
    """Test the ForbiddenError exception class."""

    def test_default_status_code_is_403(self):
        """Test that ForbiddenError has status code 403."""
        exc = ForbiddenError()

        assert exc.status_code == 403
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_default_code_is_insufficient_permissions(self):
        """Test that default code is INSUFFICIENT_PERMISSIONS."""
        exc = ForbiddenError()

        assert exc.code == 'INSUFFICIENT_PERMISSIONS'
        assert exc.message == 'Error: INSUFFICIENT_PERMISSIONS'

    def test_initialization_with_custom_code(self):
        """Test initialization with custom code."""
        exc = ForbiddenError(code='NOT_RUN_LEADER')

        assert exc.code == 'NOT_RUN_LEADER'
        assert exc.status_code == 403

    def test_initialization_with_code_and_message(self):
        """Test initialization with code and custom message."""
        exc = ForbiddenError(code='NOT_GROUP_ADMIN', message='User is not a group admin')

        assert exc.code == 'NOT_GROUP_ADMIN'
        assert exc.message == 'User is not a group admin'
        assert exc.status_code == 403

    def test_initialization_with_code_and_details(self):
        """Test initialization with code and details kwargs."""
        exc = ForbiddenError(code='NOT_RUN_LEADER', run_id='run-456', user_id='user-789')

        assert exc.code == 'NOT_RUN_LEADER'
        assert exc.details['run_id'] == 'run-456'
        assert exc.details['user_id'] == 'user-789'

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        exc = ForbiddenError(
            code='NOT_GROUP_MEMBER',
            message='Not a member of this group',
            group_id='group-123',
            user_id='user-456',
        )

        assert exc.code == 'NOT_GROUP_MEMBER'
        assert exc.message == 'Not a member of this group'
        assert exc.details['group_id'] == 'group-123'
        assert exc.details['user_id'] == 'user-456'

    def test_inherits_from_app_exception(self):
        """Test that ForbiddenError inherits from AppException."""
        exc = ForbiddenError()

        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)


class TestValidationError:
    """Test the ValidationError exception class."""

    def test_default_status_code_is_422(self):
        """Test that ValidationError has status code 422."""
        exc = ValidationError(code='VALIDATION_FAILED')

        assert exc.status_code == 422
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_initialization_with_code_only(self):
        """Test initialization with just code parameter."""
        exc = ValidationError(code='PRODUCT_NAME_EMPTY')

        assert exc.code == 'PRODUCT_NAME_EMPTY'
        assert exc.message == 'Error: PRODUCT_NAME_EMPTY'
        assert exc.status_code == 422
        assert exc.details == {}

    def test_initialization_with_code_and_message(self):
        """Test initialization with code and custom message."""
        exc = ValidationError(code='BID_QUANTITY_NEGATIVE', message='Quantity must be positive')

        assert exc.code == 'BID_QUANTITY_NEGATIVE'
        assert exc.message == 'Quantity must be positive'
        assert exc.status_code == 422

    def test_initialization_with_code_and_details(self):
        """Test initialization with code and details kwargs."""
        exc = ValidationError(code='BID_QUANTITY_NEGATIVE', quantity=-5, field='quantity')

        assert exc.code == 'BID_QUANTITY_NEGATIVE'
        assert exc.details['quantity'] == -5
        assert exc.details['field'] == 'quantity'

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        exc = ValidationError(
            code='PRICE_TOO_HIGH',
            message='Price exceeds maximum allowed',
            price=999999,
            max_price=10000,
        )

        assert exc.code == 'PRICE_TOO_HIGH'
        assert exc.message == 'Price exceeds maximum allowed'
        assert exc.details['price'] == 999999
        assert exc.details['max_price'] == 10000

    def test_inherits_from_app_exception(self):
        """Test that ValidationError inherits from AppException."""
        exc = ValidationError(code='INHERITANCE_TEST')

        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)


class TestConflictError:
    """Test the ConflictError exception class."""

    def test_default_status_code_is_409(self):
        """Test that ConflictError has status code 409."""
        exc = ConflictError(code='CONFLICT_DETECTED')

        assert exc.status_code == 409
        assert exc.status_code == status.HTTP_409_CONFLICT

    def test_initialization_with_code_only(self):
        """Test initialization with just code parameter."""
        exc = ConflictError(code='ALREADY_GROUP_MEMBER')

        assert exc.code == 'ALREADY_GROUP_MEMBER'
        assert exc.message == 'Error: ALREADY_GROUP_MEMBER'
        assert exc.status_code == 409
        assert exc.details == {}

    def test_initialization_with_code_and_message(self):
        """Test initialization with code and custom message."""
        exc = ConflictError(code='USERNAME_TAKEN', message='Username already exists')

        assert exc.code == 'USERNAME_TAKEN'
        assert exc.message == 'Username already exists'
        assert exc.status_code == 409

    def test_initialization_with_code_and_details(self):
        """Test initialization with code and details kwargs."""
        exc = ConflictError(code='ALREADY_GROUP_MEMBER', group_id='group-123', user_id='user-456')

        assert exc.code == 'ALREADY_GROUP_MEMBER'
        assert exc.details['group_id'] == 'group-123'
        assert exc.details['user_id'] == 'user-456'

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        exc = ConflictError(
            code='DUPLICATE_BID',
            message='User already has a bid on this product',
            product_id='product-789',
            user_id='user-456',
        )

        assert exc.code == 'DUPLICATE_BID'
        assert exc.message == 'User already has a bid on this product'
        assert exc.details['product_id'] == 'product-789'
        assert exc.details['user_id'] == 'user-456'

    def test_inherits_from_app_exception(self):
        """Test that ConflictError inherits from AppException."""
        exc = ConflictError(code='INHERITANCE_TEST')

        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)


class TestBadRequestError:
    """Test the BadRequestError exception class."""

    def test_default_status_code_is_400(self):
        """Test that BadRequestError has status code 400."""
        exc = BadRequestError(code='BAD_REQUEST')

        assert exc.status_code == 400
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_initialization_with_code_only(self):
        """Test initialization with just code parameter."""
        exc = BadRequestError(code='INVALID_ID_FORMAT')

        assert exc.code == 'INVALID_ID_FORMAT'
        assert exc.message == 'Error: INVALID_ID_FORMAT'
        assert exc.status_code == 400
        assert exc.details == {}

    def test_initialization_with_code_and_message(self):
        """Test initialization with code and custom message."""
        exc = BadRequestError(code='RUN_MAX_PRODUCTS_EXCEEDED', message='Too many products')

        assert exc.code == 'RUN_MAX_PRODUCTS_EXCEEDED'
        assert exc.message == 'Too many products'
        assert exc.status_code == 400

    def test_initialization_with_code_and_details(self):
        """Test initialization with code and details kwargs."""
        exc = BadRequestError(code='RUN_MAX_PRODUCTS_EXCEEDED', max_products=50, current=75)

        assert exc.code == 'RUN_MAX_PRODUCTS_EXCEEDED'
        assert exc.details['max_products'] == 50
        assert exc.details['current'] == 75

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        exc = BadRequestError(
            code='INVALID_DATE_FORMAT',
            message='Date format is incorrect',
            expected_format='YYYY-MM-DD',
            received='01/01/2026',
        )

        assert exc.code == 'INVALID_DATE_FORMAT'
        assert exc.message == 'Date format is incorrect'
        assert exc.details['expected_format'] == 'YYYY-MM-DD'
        assert exc.details['received'] == '01/01/2026'

    def test_inherits_from_app_exception(self):
        """Test that BadRequestError inherits from AppException."""
        exc = BadRequestError(code='INHERITANCE_TEST')

        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)


class TestConfigurationError:
    """Test the ConfigurationError exception class."""

    def test_default_status_code_is_500(self):
        """Test that ConfigurationError has status code 500."""
        exc = ConfigurationError(code='CONFIG_ERROR')

        assert exc.status_code == 500
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_initialization_with_code_only(self):
        """Test initialization with just code parameter."""
        exc = ConfigurationError(code='INVALID_REPO_MODE')

        assert exc.code == 'INVALID_REPO_MODE'
        assert exc.message == 'Error: INVALID_REPO_MODE'
        assert exc.status_code == 500
        assert exc.details == {}

    def test_initialization_with_code_and_message(self):
        """Test initialization with code and custom message."""
        exc = ConfigurationError(code='DATABASE_SESSION_REQUIRED', message='DB session not set')

        assert exc.code == 'DATABASE_SESSION_REQUIRED'
        assert exc.message == 'DB session not set'
        assert exc.status_code == 500

    def test_initialization_with_code_and_details(self):
        """Test initialization with code and details kwargs."""
        exc = ConfigurationError(
            code='INVALID_REPO_MODE', repo_mode='invalid', valid_modes=['mock', 'sqlite']
        )

        assert exc.code == 'INVALID_REPO_MODE'
        assert exc.details['repo_mode'] == 'invalid'
        assert exc.details['valid_modes'] == ['mock', 'sqlite']

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        exc = ConfigurationError(
            code='MISSING_ENV_VAR',
            message='Required environment variable not set',
            var_name='DATABASE_URL',
            required=True,
        )

        assert exc.code == 'MISSING_ENV_VAR'
        assert exc.message == 'Required environment variable not set'
        assert exc.details['var_name'] == 'DATABASE_URL'
        assert exc.details['required'] is True

    def test_inherits_from_app_exception(self):
        """Test that ConfigurationError inherits from AppException."""
        exc = ConfigurationError(code='INHERITANCE_TEST')

        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)


class TestStatusCodeValidation:
    """Test status code validation for all exception classes."""

    @pytest.mark.parametrize(
        'exception_class,expected_status_code',
        [
            (NotFoundError, 404),
            (UnauthorizedError, 401),
            (ForbiddenError, 403),
            (ValidationError, 422),
            (ConflictError, 409),
            (BadRequestError, 400),
            (ConfigurationError, 500),
        ],
    )
    def test_exception_default_status_codes(self, exception_class, expected_status_code):
        """Test that all exception classes have correct default status codes."""
        if exception_class in (UnauthorizedError, ForbiddenError):
            # These have default codes, so no code parameter needed
            exc = exception_class()
        else:
            # Others require a code parameter
            exc = exception_class(code='TEST_CODE')

        assert exc.status_code == expected_status_code

    @pytest.mark.parametrize(
        'exception_class,status_name',
        [
            (NotFoundError, status.HTTP_404_NOT_FOUND),
            (UnauthorizedError, status.HTTP_401_UNAUTHORIZED),
            (ForbiddenError, status.HTTP_403_FORBIDDEN),
            (ValidationError, status.HTTP_422_UNPROCESSABLE_CONTENT),
            (ConflictError, status.HTTP_409_CONFLICT),
            (BadRequestError, status.HTTP_400_BAD_REQUEST),
            (ConfigurationError, status.HTTP_500_INTERNAL_SERVER_ERROR),
        ],
    )
    def test_exception_status_codes_match_fastapi_constants(self, exception_class, status_name):
        """Test that status codes match FastAPI status code constants."""
        if exception_class in (UnauthorizedError, ForbiddenError):
            exc = exception_class()
        else:
            exc = exception_class(code='TEST_CODE')

        assert exc.status_code == status_name


class TestExceptionRaisingAndCatching:
    """Test that exceptions can be raised and caught correctly."""

    def test_raise_and_catch_not_found_error(self):
        """Test raising and catching NotFoundError."""
        with pytest.raises(NotFoundError) as exc_info:
            raise NotFoundError(code='USER_NOT_FOUND', user_id='123')

        assert exc_info.value.code == 'USER_NOT_FOUND'
        assert exc_info.value.status_code == 404
        assert exc_info.value.details['user_id'] == '123'

    def test_raise_and_catch_unauthorized_error(self):
        """Test raising and catching UnauthorizedError."""
        with pytest.raises(UnauthorizedError) as exc_info:
            raise UnauthorizedError(code='AUTH_EXPIRED')

        assert exc_info.value.code == 'AUTH_EXPIRED'
        assert exc_info.value.status_code == 401

    def test_raise_and_catch_forbidden_error(self):
        """Test raising and catching ForbiddenError."""
        with pytest.raises(ForbiddenError) as exc_info:
            raise ForbiddenError(code='NOT_RUN_LEADER', run_id='run-123')

        assert exc_info.value.code == 'NOT_RUN_LEADER'
        assert exc_info.value.details['run_id'] == 'run-123'

    def test_raise_and_catch_validation_error(self):
        """Test raising and catching ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(code='INVALID_QUANTITY', quantity=-5)

        assert exc_info.value.code == 'INVALID_QUANTITY'
        assert exc_info.value.details['quantity'] == -5

    def test_raise_and_catch_conflict_error(self):
        """Test raising and catching ConflictError."""
        with pytest.raises(ConflictError) as exc_info:
            raise ConflictError(code='DUPLICATE_ENTRY')

        assert exc_info.value.code == 'DUPLICATE_ENTRY'

    def test_raise_and_catch_bad_request_error(self):
        """Test raising and catching BadRequestError."""
        with pytest.raises(BadRequestError) as exc_info:
            raise BadRequestError(code='INVALID_FORMAT')

        assert exc_info.value.code == 'INVALID_FORMAT'

    def test_raise_and_catch_configuration_error(self):
        """Test raising and catching ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError(code='MISSING_CONFIG')

        assert exc_info.value.code == 'MISSING_CONFIG'

    def test_catch_app_exception_catches_all_subclasses(self):
        """Test that catching AppException catches all exception subclasses."""
        with pytest.raises(AppException):
            raise NotFoundError(code='TEST')

        with pytest.raises(AppException):
            raise UnauthorizedError(code='TEST')

        with pytest.raises(AppException):
            raise ForbiddenError(code='TEST')

        with pytest.raises(AppException):
            raise ValidationError(code='TEST')

        with pytest.raises(AppException):
            raise ConflictError(code='TEST')

        with pytest.raises(AppException):
            raise BadRequestError(code='TEST')

        with pytest.raises(AppException):
            raise ConfigurationError(code='TEST')

    def test_exception_details_accessible_after_catch(self):
        """Test that exception details are accessible after catching."""
        try:
            raise NotFoundError(code='USER_NOT_FOUND', user_id='123', group_id='456')
        except AppException as exc:
            assert exc.code == 'USER_NOT_FOUND'
            assert exc.status_code == 404
            assert exc.details['user_id'] == '123'
            assert exc.details['group_id'] == '456'

        try:
            raise ValidationError(code='INVALID_QUANTITY', quantity=-5, field='quantity')
        except AppException as exc:
            assert exc.code == 'INVALID_QUANTITY'
            assert exc.status_code == 422
            assert exc.details['quantity'] == -5
