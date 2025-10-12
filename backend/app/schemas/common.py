"""Common schemas used across multiple domains."""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
