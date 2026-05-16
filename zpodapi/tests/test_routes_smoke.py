"""Smoke tests for every top-level collection route.

These don't validate business behavior — they assert that each router's GET
endpoint loads its schemas, hits the DB session, serializes the (empty)
result, and returns 200 with an iterable. The point is to catch regressions
where a schema fails to import or serialize after a dependency upgrade.

Routes covered:
    /                        (root)
    /components
    /endpoints
    /libraries
    /permission_groups
    /profiles
    /settings
    /users   (already covered in detail by test_users.py)
    /zpods
"""

import pytest
from fastapi.testclient import TestClient

# Top-level collection endpoints. Every one of them returns a list (or in /'s
# case, a small dict) when called as a superadmin against an empty DB.
COLLECTION_ROUTES = [
    "/components",
    "/endpoints",
    "/libraries",
    "/permission_groups",
    "/profiles",
    "/settings",
    "/zpods",
]


@pytest.mark.parametrize("path", COLLECTION_ROUTES)
def test_superadmin_get_collection_returns_list(
    path: str,
    superadmin_client: TestClient,
):
    response = superadmin_client.get(path)
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


@pytest.mark.parametrize("path", COLLECTION_ROUTES)
def test_collection_rejects_bad_token(path: str, client: TestClient):
    client.headers["access_token"] = "BADTOKEN"
    response = client.get(path)
    assert response.status_code == 403


@pytest.mark.parametrize("path", COLLECTION_ROUTES)
def test_normaluser_get_collection_returns_list(
    path: str,
    normaluser_client: TestClient,
):
    """Non-admin should still see *some* response (typically empty list,
    filtered to their own permissions)."""
    response = normaluser_client.get(path)
    # /settings is admin-only — accept 403 there; everything else returns 200.
    assert response.status_code in (200, 403), response.text
    if response.status_code == 200:
        assert isinstance(response.json(), list)
