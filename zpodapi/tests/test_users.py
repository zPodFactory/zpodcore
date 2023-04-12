from fastapi.testclient import TestClient


def ignore(data, *keys):
    if type(data) == list:
        return [{k: row[k] for k in row if k not in keys} for row in data]
    return {k: data[k] for k in data if k not in keys}


def test_bad_token(client: TestClient):
    client.headers["access_token"] = "BADTOKEN"
    response = client.get("/users")
    assert response.status_code == 403


def test_normaluser_create_user(normaluser_client: TestClient):
    user = dict(
        username="testuser",
        email="testuser@zpodfactory.io",
        description="Description",
        superadmin=False,
    )
    response = normaluser_client.post("/users", json=user)
    assert response.status_code == 403


def test_superadmin_create_user(superadmin_client: TestClient):
    user = dict(
        username="testuser",
        email="testuser@zpodfactory.io",
        description="Description",
        superadmin=False,
    )

    response = superadmin_client.post("/users", json=user)
    data = response.json()
    assert response.status_code == 201
    assert ignore(data, "id", "creation_date", "last_connection_date") == user

    for key in user:
        assert user[key] == data[key]


def test_superadmin_create_user_with_duplicated_username(superadmin_client: TestClient):
    user = dict(
        username="superuser",
        email="testuser@zpodfactory.io",
        description="Description",
        superadmin=False,
    )

    response = superadmin_client.post("/users", json=user)
    assert response.status_code == 422


def test_superadmin_get_users(superadmin_client: TestClient):
    response = superadmin_client.get("/users")
    data = response.json()
    assert response.status_code == 200
    assert ignore(data, "id", "creation_date", "last_connection_date") == [
        dict(
            username="superuser",
            email="superuser@zpodfactory.io",
            description="",
            superadmin=True,
        ),
        dict(
            username="normaluser",
            email="normaluser@zpodfactory.io",
            description="",
            superadmin=False,
        ),
    ]


def test_normaluser_get_users(normaluser_client: TestClient):
    response = normaluser_client.get("/users")
    data = response.json()
    assert response.status_code == 200
    assert ignore(data, "id", "creation_date", "last_connection_date") == [
        dict(
            username="normaluser",
            email="normaluser@zpodfactory.io",
            description="",
            superadmin=False,
        ),
    ]


def test_superadmin_get_user_me(superadmin_client: TestClient):
    response = superadmin_client.get("/users/me")
    data = response.json()
    assert response.status_code == 200
    assert ignore(data, "id", "creation_date", "last_connection_date") == {
        "username": "superuser",
        "email": "superuser@zpodfactory.io",
        "description": "",
        "superadmin": True,
    }


def test_normaluser_get_user_me(normaluser_client: TestClient):
    response = normaluser_client.get("/users/me")
    data = response.json()
    assert response.status_code == 200
    assert ignore(data, "id", "creation_date", "last_connection_date") == {
        "username": "normaluser",
        "email": "normaluser@zpodfactory.io",
        "description": "",
        "superadmin": False,
    }


def test_superadmin_get_user_by_username(superadmin_client: TestClient):
    response = superadmin_client.get("/users/username=superuser")
    data = response.json()
    assert response.status_code == 200
    assert ignore(data, "id", "creation_date", "last_connection_date") == {
        "username": "superuser",
        "email": "superuser@zpodfactory.io",
        "description": "",
        "superadmin": True,
    }


def test_superadmin_get_user_by_email(superadmin_client: TestClient):
    response = superadmin_client.get("/users/email=superuser@zpodfactory.io")
    data = response.json()
    assert response.status_code == 200
    assert ignore(data, "id", "creation_date", "last_connection_date") == {
        "username": "superuser",
        "email": "superuser@zpodfactory.io",
        "description": "",
        "superadmin": True,
    }


def test_superadmin_get_user_username_not_found(superadmin_client: TestClient):
    response = superadmin_client.get("/users/username=badusername")
    assert response.status_code == 404


def test_superadmin_get_user_email_not_found(superadmin_client: TestClient):
    response = superadmin_client.get("/users/email=bad@email.com")
    assert response.status_code == 404


def test_superadmin_patch_user(superadmin_client: TestClient):
    response = superadmin_client.patch(
        "/users/username=superuser",
        json={"description": "AdminPatched"},
    )
    data = response.json()
    assert response.status_code == 201
    assert ignore(data, "id", "creation_date", "last_connection_date") == {
        "username": "superuser",
        "email": "superuser@zpodfactory.io",
        "description": "AdminPatched",
        "superadmin": True,
    }


def test_normaluser_patch_user(normaluser_client: TestClient):
    response = normaluser_client.patch(
        "/users/username=normaluser",
        json={"description": "AdminPatched"},
    )
    data = response.json()
    assert response.status_code == 201
    assert ignore(data, "id", "creation_date", "last_connection_date") == {
        "username": "normaluser",
        "email": "normaluser@zpodfactory.io",
        "description": "AdminPatched",
        "superadmin": False,
    }


def test_superadmin_patch_user_missing(superadmin_client: TestClient):
    response = superadmin_client.patch(
        "/users/187",
        json={"description": "AdminPatched"},
    )
    assert response.status_code == 404


def test_normaluser_delete_user_by_username(normaluser_client: TestClient):
    response = normaluser_client.delete("/users/username=normaluser")
    assert response.status_code == 403


def test_superadmin_delete_user_by_username(superadmin_client: TestClient):
    response = superadmin_client.delete("/users/username=superuser")
    assert response.status_code == 204


def test_superadmin_delete_user_by_email(superadmin_client: TestClient):
    response = superadmin_client.delete("/users/email=superuser@zpodfactory.io")
    assert response.status_code == 204


def test_superadmin_delete_user_missing(superadmin_client: TestClient):
    response = superadmin_client.delete(
        "/users/username=bad_username",
    )
    assert response.status_code == 404
