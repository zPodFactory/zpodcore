"""A client library for accessing zPod API"""

from .client import AuthenticatedClient, Client

__version__ = "0.6.1"

__all__ = (
    "AuthenticatedClient",
    "Client",
)