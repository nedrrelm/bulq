def test_hello_world(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World from Bulq Backend!"}


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_db_health_check(client):
    response = client.get("/db-health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"