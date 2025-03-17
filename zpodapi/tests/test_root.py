from fastapi.testclient import TestClient


def test_root(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["X-zPod-API"] == "true"
