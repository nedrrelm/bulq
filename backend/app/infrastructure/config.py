"""Application configuration."""

import os
from typing import Literal

# Environment configuration
ENV = os.getenv('ENV', 'development')
IS_PRODUCTION = ENV == 'production'

# Repository mode configuration
REPO_MODE: Literal['database', 'memory'] = os.getenv('REPO_MODE', 'memory')  # type: ignore

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Validate database configuration in production
if IS_PRODUCTION and REPO_MODE == 'database' and not DATABASE_URL:
    raise RuntimeError('DATABASE_URL must be set when REPO_MODE=database in production!')

# Security configuration
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('SECRET_KEY environment variable must be set!')

# Session configuration
SESSION_EXPIRY_HOURS = int(os.getenv('SESSION_EXPIRY_HOURS', '24'))
SECURE_COOKIES = os.getenv('SECURE_COOKIES', 'false').lower() == 'true'

# Validate secure cookies in production
if IS_PRODUCTION and not SECURE_COOKIES:
    raise RuntimeError('SECURE_COOKIES must be true in production (requires HTTPS)!')

# CORS configuration
ALLOWED_ORIGINS_RAW = os.getenv('ALLOWED_ORIGINS', '')

# Development defaults
if not ALLOWED_ORIGINS_RAW and not IS_PRODUCTION:
    ALLOWED_ORIGINS = ['http://localhost:3000', 'http://localhost:5173']
# Production validation
elif not ALLOWED_ORIGINS_RAW and IS_PRODUCTION:
    raise RuntimeError(
        'ALLOWED_ORIGINS must be set in production! Example: ALLOWED_ORIGINS=https://yourdomain.com'
    )
# Parse comma-separated origins
else:
    ALLOWED_ORIGINS = [
        origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(',') if origin.strip()
    ]

# Business logic limits
MAX_ACTIVE_RUNS_PER_GROUP = int(os.getenv('MAX_ACTIVE_RUNS_PER_GROUP', '100'))
MAX_PRODUCTS_PER_RUN = int(os.getenv('MAX_PRODUCTS_PER_RUN', '100'))
MAX_GROUPS_PER_USER = int(os.getenv('MAX_GROUPS_PER_USER', '100'))
MAX_MEMBERS_PER_GROUP = int(os.getenv('MAX_MEMBERS_PER_GROUP', '100'))
