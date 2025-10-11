"""Application configuration."""

import os
from typing import Literal

# Repository mode configuration
REPO_MODE: Literal["database", "memory"] = os.getenv("REPO_MODE", "memory")  # type: ignore

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable must be set!")

# Session configuration
SESSION_EXPIRY_HOURS = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))
SECURE_COOKIES = os.getenv("SECURE_COOKIES", "false").lower() == "true"

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

# Business logic limits
MAX_ACTIVE_RUNS_PER_GROUP = int(os.getenv("MAX_ACTIVE_RUNS_PER_GROUP", "100"))
MAX_PRODUCTS_PER_RUN = int(os.getenv("MAX_PRODUCTS_PER_RUN", "100"))
MAX_GROUPS_PER_USER = int(os.getenv("MAX_GROUPS_PER_USER", "100"))
MAX_MEMBERS_PER_GROUP = int(os.getenv("MAX_MEMBERS_PER_GROUP", "100"))