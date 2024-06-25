"""A client library for accessing zPod API"""

from .client import AuthenticatedClient, Client

__version__ = "0.7.0"

__all__ = (
    "AuthenticatedClient",
    "Client",
)
