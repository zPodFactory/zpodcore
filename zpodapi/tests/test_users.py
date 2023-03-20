from fastapi.testclient import TestClient


def ignore(data, *keys):
    if type(data) == list:
        return [{k: row[k] for k in row if k not in keys} for row in data]
    return {k: data[k] for k in data if k not in keys}


def test_bad_token(client: TestClient):
    client.headers["access_token"] = "BADTOKEN"

    response = client.get("/users")
    assert response.status_code == 403


def test_create_user(authed_client: TestClient):
    user = dict(
        username="testuser",
        email="testuser@zpodfactory.io",
        description="Description",
        ssh_key="ssh_key",
        superadmin=False,
    )

    response = authed_client.post("/user", json=user)
    data = response.json()
    assert response.status_code == 201
    assert ignore(data, "api_token", "creation_date", "last_connection_date") == user

    for key in user:
        assert user[key] == data[key]


def test_create_user_with_duplicated_username(authed_client: TestClient):
    user = dict(
        username="superuser",
        email="testuser@zpodfactory.io",
        description="Description",
        ssh_key="ssh_key",
        superadmin=False,
    )

    response = authed_client.post("/user", json=user)
    assert response.status_code == 422


def test_get_users(authed_client: TestClient):
    response = authed_client.get("/users")
    data = response.json()
    assert response.status_code == 200
    assert ignore(data, "creation_date", "last_connection_date") == [
        dict(
            username="superuser",
            email="superuser@zpodfactory.io",
            description="",
            api_token="APITOKEN",
            ssh_key="",
            superadmin=True,
        )
    ]


def test_get_user_me(authed_client: TestClient):
    response = authed_client.get("/user/me")
    data = response.json()
    assert response.status_code == 200
    assert ignore(data, "creation_date", "last_connection_date") == {
        "username": "superuser",
        "email": "superuser@zpodfactory.io",
        "description": "",
        "api_token": "APITOKEN",
        "ssh_key": "",
        "superadmin": True,
    }


def test_get_user_by_username(authed_client: TestClient):
    response = authed_client.get("/user?username=superuser")
    data = response.json()
    assert response.status_code == 200
    assert ignore(data, "creation_date", "last_connection_date") == {
        "username": "superuser",
        "email": "superuser@zpodfactory.io",
        "description": "",
        "api_token": "APITOKEN",
        "ssh_key": "",
        "superadmin": True,
    }


def test_get_user_by_email(authed_client: TestClient):
    response = authed_client.get("/user?email=superuser@zpodfactory.io")
    data = response.json()
    assert response.status_code == 200
    assert ignore(data, "creation_date", "last_connection_date") == {
        "username": "superuser",
        "email": "superuser@zpodfactory.io",
        "description": "",
        "api_token": "APITOKEN",
        "ssh_key": "",
        "superadmin": True,
    }


def test_get_user_username_not_found(authed_client: TestClient):
    response = authed_client.get("/user?username=badusername")
    assert response.status_code == 404


def test_get_user_email_not_found(authed_client: TestClient):
    response = authed_client.get("/user?email=bad@email.com")
    assert response.status_code == 404


def test_patch_user(authed_client: TestClient):
    response = authed_client.patch(
        "/user?username=superuser",
        json={"description": "AdminPatched"},
    )
    data = response.json()
    assert response.status_code == 201
    assert ignore(data, "creation_date", "last_connection_date") == {
        "username": "superuser",
        "email": "superuser@zpodfactory.io",
        "description": "AdminPatched",
        "api_token": "APITOKEN",
        "ssh_key": "",
        "superadmin": True,
    }


def test_patch_user_missing(authed_client: TestClient):
    response = authed_client.patch(
        "/user/187",
        json={"description": "AdminPatched"},
    )
    assert response.status_code == 404


def test_delete_user_by_username(authed_client: TestClient):
    response = authed_client.delete("/user?username=superuser")
    assert response.status_code == 204


def test_delete_user_by_email(authed_client: TestClient):
    response = authed_client.delete("/user?email=superuser@zpodfactory.io")
    assert response.status_code == 204


def test_delete_user_missing(authed_client: TestClient):
    response = authed_client.delete(
        "/user/username=bad_username",
    )
    assert response.status_code == 404
