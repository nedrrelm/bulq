"""Application configuration."""

from typing import Literal

# Repository mode configuration - Change this line to switch modes
REPO_MODE: Literal["database", "memory"] = "memory"  # Change to "memory" for test data

def get_repo_mode() -> str:
    """Get current repository mode."""
    return REPO_MODE