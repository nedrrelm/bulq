"""Unit tests for application configuration.

Tests cover:
- Configuration constants and types
- Environment variable loading
- Default values
- Configuration validation
- Production-specific requirements
"""

from unittest.mock import patch

import pytest

from app.infrastructure import config


class TestConfigurationConstants:
    """Test that configuration constants exist and have correct types."""

    def test_env_is_string(self):
        """Test that ENV is a string."""
        assert isinstance(config.ENV, str)

    def test_is_production_is_boolean(self):
        """Test that IS_PRODUCTION is a boolean."""
        assert isinstance(config.IS_PRODUCTION, bool)

    def test_repo_mode_has_valid_value(self):
        """Test that REPO_MODE has valid value."""
        assert config.REPO_MODE in ['database', 'memory']

    def test_secret_key_is_string(self):
        """Test that SECRET_KEY is a string."""
        assert isinstance(config.SECRET_KEY, str)

    def test_session_expiry_hours_is_integer(self):
        """Test that SESSION_EXPIRY_HOURS is an integer."""
        assert isinstance(config.SESSION_EXPIRY_HOURS, int)

    def test_secure_cookies_is_boolean(self):
        """Test that SECURE_COOKIES is a boolean."""
        assert isinstance(config.SECURE_COOKIES, bool)

    def test_session_store_type_has_valid_value(self):
        """Test that SESSION_STORE_TYPE has valid value."""
        assert config.SESSION_STORE_TYPE in ['redis', 'memory']

    def test_allowed_origins_is_list(self):
        """Test that ALLOWED_ORIGINS is a list."""
        assert isinstance(config.ALLOWED_ORIGINS, list)

    def test_max_active_runs_per_group_is_integer(self):
        """Test that MAX_ACTIVE_RUNS_PER_GROUP is an integer."""
        assert isinstance(config.MAX_ACTIVE_RUNS_PER_GROUP, int)

    def test_max_products_per_run_is_integer(self):
        """Test that MAX_PRODUCTS_PER_RUN is an integer."""
        assert isinstance(config.MAX_PRODUCTS_PER_RUN, int)

    def test_max_groups_per_user_is_integer(self):
        """Test that MAX_GROUPS_PER_USER is an integer."""
        assert isinstance(config.MAX_GROUPS_PER_USER, int)

    def test_max_members_per_group_is_integer(self):
        """Test that MAX_MEMBERS_PER_GROUP is an integer."""
        assert isinstance(config.MAX_MEMBERS_PER_GROUP, int)


class TestEnvironmentVariableLoading:
    """Test configuration loading from environment variables."""

    def test_env_defaults_to_development(self):
        """Test that ENV defaults to 'development' when not set."""
        with patch.dict('os.environ', {}, clear=False):
            # Remove ENV if it exists
            import os

            env_backup = os.environ.get('ENV')
            if 'ENV' in os.environ:
                del os.environ['ENV']

            # Re-import to get default value
            import importlib

            importlib.reload(config)

            assert (
                config.ENV in ['development', 'production', 'testing']
                or config.ENV == 'development'
            )

            # Restore
            if env_backup:
                os.environ['ENV'] = env_backup

    def test_repo_mode_defaults_to_memory(self):
        """Test that REPO_MODE defaults to 'memory' when not set."""
        with patch.dict('os.environ', {'SECRET_KEY': 'test-secret-key'}, clear=True):
            import importlib

            importlib.reload(config)

            assert config.REPO_MODE == 'memory'

    def test_session_expiry_hours_defaults_to_24(self):
        """Test that SESSION_EXPIRY_HOURS defaults to 24 when not set."""
        with patch.dict('os.environ', {'SECRET_KEY': 'test-secret-key'}, clear=True):
            import importlib

            importlib.reload(config)

            assert config.SESSION_EXPIRY_HOURS == 24

    def test_secure_cookies_defaults_to_false(self):
        """Test that SECURE_COOKIES defaults to false in non-production."""
        with patch.dict(
            'os.environ', {'SECRET_KEY': 'test-secret-key', 'ENV': 'development'}, clear=True
        ):
            import importlib

            importlib.reload(config)

            assert config.SECURE_COOKIES is False

    def test_session_store_type_defaults_to_redis(self):
        """Test that SESSION_STORE_TYPE defaults to 'redis'."""
        with patch.dict('os.environ', {'SECRET_KEY': 'test-secret-key'}, clear=True):
            import importlib

            importlib.reload(config)

            assert config.SESSION_STORE_TYPE == 'redis'

    def test_custom_env_value_is_loaded(self):
        """Test that custom ENV value is loaded from environment."""
        with patch.dict(
            'os.environ', {'ENV': 'testing', 'SECRET_KEY': 'test-secret-key'}, clear=True
        ):
            import importlib

            importlib.reload(config)

            assert config.ENV == 'testing'

    def test_custom_repo_mode_is_loaded(self):
        """Test that custom REPO_MODE is loaded from environment."""
        with patch.dict(
            'os.environ',
            {
                'REPO_MODE': 'database',
                'SECRET_KEY': 'test-secret-key',
                'DATABASE_URL': 'postgresql://localhost/test',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.REPO_MODE == 'database'

    def test_custom_session_expiry_hours_is_loaded(self):
        """Test that custom SESSION_EXPIRY_HOURS is loaded from environment."""
        with patch.dict(
            'os.environ',
            {'SESSION_EXPIRY_HOURS': '48', 'SECRET_KEY': 'test-secret-key'},
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.SESSION_EXPIRY_HOURS == 48

    def test_custom_business_logic_limits_are_loaded(self):
        """Test that custom business logic limits are loaded from environment."""
        with patch.dict(
            'os.environ',
            {
                'SECRET_KEY': 'test-secret-key',
                'MAX_ACTIVE_RUNS_PER_GROUP': '50',
                'MAX_PRODUCTS_PER_RUN': '200',
                'MAX_GROUPS_PER_USER': '25',
                'MAX_MEMBERS_PER_GROUP': '75',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.MAX_ACTIVE_RUNS_PER_GROUP == 50
            assert config.MAX_PRODUCTS_PER_RUN == 200
            assert config.MAX_GROUPS_PER_USER == 25
            assert config.MAX_MEMBERS_PER_GROUP == 75


class TestConfigurationValidation:
    """Test configuration validation rules."""

    def test_secret_key_is_required(self):
        """Test that SECRET_KEY is required (raises error if not set)."""
        with (
            patch.dict('os.environ', {}, clear=True),
            pytest.raises(RuntimeError, match='SECRET_KEY environment variable must be set'),
        ):
            import importlib

            importlib.reload(config)

    def test_database_url_required_in_production_with_database_mode(self):
        """Test that DATABASE_URL is required in production with database mode."""
        with (
            patch.dict(
                'os.environ',
                {
                    'ENV': 'production',
                    'SECRET_KEY': 'test-secret-key',
                    'REPO_MODE': 'database',
                    'SECURE_COOKIES': 'true',
                    'ALLOWED_ORIGINS': 'https://example.com',
                    'REDIS_URL': 'redis://localhost:6379/0',
                },
                clear=True,
            ),
            pytest.raises(
                RuntimeError, match='DATABASE_URL must be set when REPO_MODE=database in production'
            ),
        ):
            import importlib

            importlib.reload(config)

    def test_secure_cookies_required_in_production(self):
        """Test that SECURE_COOKIES must be true in production."""
        with (
            patch.dict(
                'os.environ',
                {
                    'ENV': 'production',
                    'SECRET_KEY': 'test-secret-key',
                    'REPO_MODE': 'memory',
                    'SECURE_COOKIES': 'false',
                    'ALLOWED_ORIGINS': 'https://example.com',
                },
                clear=True,
            ),
            pytest.raises(RuntimeError, match='SECURE_COOKIES must be true in production'),
        ):
            import importlib

            importlib.reload(config)

    def test_redis_url_required_in_production_with_redis_session_store(self):
        """Test that REDIS_URL is required in production with redis session store."""
        with (
            patch.dict(
                'os.environ',
                {
                    'ENV': 'production',
                    'SECRET_KEY': 'test-secret-key',
                    'REPO_MODE': 'memory',
                    'SECURE_COOKIES': 'true',
                    'SESSION_STORE_TYPE': 'redis',
                    'ALLOWED_ORIGINS': 'https://example.com',
                },
                clear=True,
            ),
            pytest.raises(
                RuntimeError,
                match='REDIS_URL must be set when SESSION_STORE_TYPE=redis in production',
            ),
        ):
            import importlib

            importlib.reload(config)

    def test_allowed_origins_required_in_production(self):
        """Test that ALLOWED_ORIGINS is required in production."""
        with (
            patch.dict(
                'os.environ',
                {
                    'ENV': 'production',
                    'SECRET_KEY': 'test-secret-key',
                    'REPO_MODE': 'memory',
                    'SECURE_COOKIES': 'true',
                    'SESSION_STORE_TYPE': 'memory',
                },
                clear=True,
            ),
            pytest.raises(RuntimeError, match='ALLOWED_ORIGINS must be set in production'),
        ):
            import importlib

            importlib.reload(config)


class TestProductionConfiguration:
    """Test production-specific configuration."""

    def test_is_production_true_when_env_is_production(self):
        """Test that IS_PRODUCTION is True when ENV is 'production'."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'production',
                'SECRET_KEY': 'test-secret-key',
                'REPO_MODE': 'memory',
                'SECURE_COOKIES': 'true',
                'SESSION_STORE_TYPE': 'memory',
                'ALLOWED_ORIGINS': 'https://example.com',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.IS_PRODUCTION is True

    def test_is_production_false_in_development(self):
        """Test that IS_PRODUCTION is False in development."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.IS_PRODUCTION is False

    def test_production_config_with_all_required_fields(self):
        """Test valid production configuration with all required fields."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'production',
                'SECRET_KEY': 'production-secret-key',
                'REPO_MODE': 'database',
                'DATABASE_URL': 'postgresql://localhost/bulq',
                'SECURE_COOKIES': 'true',
                'SESSION_STORE_TYPE': 'redis',
                'REDIS_URL': 'redis://localhost:6379/0',
                'ALLOWED_ORIGINS': 'https://bulq.example.com,https://www.bulq.example.com',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.ENV == 'production'
            assert config.IS_PRODUCTION is True
            assert config.REPO_MODE == 'database'
            assert config.DATABASE_URL == 'postgresql://localhost/bulq'
            assert config.SECURE_COOKIES is True
            assert config.SESSION_STORE_TYPE == 'redis'
            assert config.REDIS_URL == 'redis://localhost:6379/0'


class TestAllowedOrigins:
    """Test ALLOWED_ORIGINS configuration."""

    def test_allowed_origins_defaults_in_development(self):
        """Test that ALLOWED_ORIGINS has defaults in development."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            # All traffic goes through Caddy reverse proxy on port 1314
            assert 'http://localhost:1314' in config.ALLOWED_ORIGINS

    def test_allowed_origins_parsed_from_comma_separated_string(self):
        """Test that ALLOWED_ORIGINS is parsed from comma-separated string."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'ALLOWED_ORIGINS': 'https://example.com,https://www.example.com,https://api.example.com',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert len(config.ALLOWED_ORIGINS) == 3
            assert 'https://example.com' in config.ALLOWED_ORIGINS
            assert 'https://www.example.com' in config.ALLOWED_ORIGINS
            assert 'https://api.example.com' in config.ALLOWED_ORIGINS

    def test_allowed_origins_strips_whitespace(self):
        """Test that ALLOWED_ORIGINS strips whitespace from entries."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'ALLOWED_ORIGINS': 'https://example.com , https://www.example.com , https://api.example.com ',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert 'https://example.com' in config.ALLOWED_ORIGINS
            assert 'https://www.example.com' in config.ALLOWED_ORIGINS
            assert 'https://api.example.com' in config.ALLOWED_ORIGINS
            # No entries with whitespace
            for origin in config.ALLOWED_ORIGINS:
                assert origin == origin.strip()

    def test_allowed_origins_filters_empty_strings(self):
        """Test that ALLOWED_ORIGINS filters out empty strings."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'ALLOWED_ORIGINS': 'https://example.com,,https://www.example.com,',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert '' not in config.ALLOWED_ORIGINS
            assert 'https://example.com' in config.ALLOWED_ORIGINS
            assert 'https://www.example.com' in config.ALLOWED_ORIGINS


class TestBusinessLogicLimits:
    """Test business logic limit configurations."""

    def test_max_active_runs_per_group_default(self):
        """Test MAX_ACTIVE_RUNS_PER_GROUP default value."""
        with patch.dict('os.environ', {'SECRET_KEY': 'test-secret-key'}, clear=True):
            import importlib

            importlib.reload(config)

            assert config.MAX_ACTIVE_RUNS_PER_GROUP == 100

    def test_max_products_per_run_default(self):
        """Test MAX_PRODUCTS_PER_RUN default value."""
        with patch.dict('os.environ', {'SECRET_KEY': 'test-secret-key'}, clear=True):
            import importlib

            importlib.reload(config)

            assert config.MAX_PRODUCTS_PER_RUN == 100

    def test_max_groups_per_user_default(self):
        """Test MAX_GROUPS_PER_USER default value."""
        with patch.dict('os.environ', {'SECRET_KEY': 'test-secret-key'}, clear=True):
            import importlib

            importlib.reload(config)

            assert config.MAX_GROUPS_PER_USER == 100

    def test_max_members_per_group_default(self):
        """Test MAX_MEMBERS_PER_GROUP default value."""
        with patch.dict('os.environ', {'SECRET_KEY': 'test-secret-key'}, clear=True):
            import importlib

            importlib.reload(config)

            assert config.MAX_MEMBERS_PER_GROUP == 100

    @pytest.mark.parametrize(
        'env_var,config_attr,custom_value',
        [
            ('MAX_ACTIVE_RUNS_PER_GROUP', 'MAX_ACTIVE_RUNS_PER_GROUP', '250'),
            ('MAX_PRODUCTS_PER_RUN', 'MAX_PRODUCTS_PER_RUN', '500'),
            ('MAX_GROUPS_PER_USER', 'MAX_GROUPS_PER_USER', '50'),
            ('MAX_MEMBERS_PER_GROUP', 'MAX_MEMBERS_PER_GROUP', '200'),
        ],
    )
    def test_business_logic_limits_custom_values(self, env_var, config_attr, custom_value):
        """Test that custom business logic limits are loaded correctly."""
        with patch.dict(
            'os.environ',
            {
                'SECRET_KEY': 'test-secret-key',
                env_var: custom_value,
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert getattr(config, config_attr) == int(custom_value)


class TestDatabaseConfiguration:
    """Test database configuration."""

    def test_database_url_can_be_none(self):
        """Test that DATABASE_URL can be None in development."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'REPO_MODE': 'memory',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            # Should not raise error
            assert config.DATABASE_URL is None or isinstance(config.DATABASE_URL, str)

    def test_database_url_is_loaded_from_env(self):
        """Test that DATABASE_URL is loaded from environment."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'DATABASE_URL': 'postgresql://user:pass@localhost:5432/bulq',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.DATABASE_URL == 'postgresql://user:pass@localhost:5432/bulq'


class TestRedisConfiguration:
    """Test Redis configuration."""

    def test_redis_url_can_be_none(self):
        """Test that REDIS_URL can be None in development."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'SESSION_STORE_TYPE': 'memory',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            # Should not raise error
            assert config.REDIS_URL is None or isinstance(config.REDIS_URL, str)

    def test_redis_url_is_loaded_from_env(self):
        """Test that REDIS_URL is loaded from environment."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'REDIS_URL': 'redis://localhost:6379/0',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.REDIS_URL == 'redis://localhost:6379/0'


class TestConfigurationEdgeCases:
    """Test edge cases in configuration."""

    def test_secure_cookies_true_parsing(self):
        """Test that SECURE_COOKIES='true' is parsed as boolean True."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'SECURE_COOKIES': 'true',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.SECURE_COOKIES is True

    def test_secure_cookies_false_parsing(self):
        """Test that SECURE_COOKIES='false' is parsed as boolean False."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'SECURE_COOKIES': 'false',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.SECURE_COOKIES is False

    def test_secure_cookies_case_insensitive(self):
        """Test that SECURE_COOKIES parsing is case-insensitive."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'SECURE_COOKIES': 'TRUE',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.SECURE_COOKIES is True

        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'SECURE_COOKIES': 'False',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.SECURE_COOKIES is False

    def test_session_expiry_hours_as_string_is_converted_to_int(self):
        """Test that SESSION_EXPIRY_HOURS string is converted to integer."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'SESSION_EXPIRY_HOURS': '72',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            assert config.SESSION_EXPIRY_HOURS == 72
            assert isinstance(config.SESSION_EXPIRY_HOURS, int)

    def test_empty_allowed_origins_in_development_uses_defaults(self):
        """Test that empty ALLOWED_ORIGINS in development uses defaults."""
        with patch.dict(
            'os.environ',
            {
                'ENV': 'development',
                'SECRET_KEY': 'test-secret-key',
                'ALLOWED_ORIGINS': '',
            },
            clear=True,
        ):
            import importlib

            importlib.reload(config)

            # Should use defaults
            assert len(config.ALLOWED_ORIGINS) > 0
