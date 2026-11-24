MOVIE = {"title": "Dune", "genre": "Sci-Fi", "release_date": "2024-03-01", "budget_usd": 1000}
REPORT = {"report_date": "2024-03-05", "region": "us", "revenue_usd": 500, "tickets_sold": 50}


def test_register_returns_only_id(client):
    resp = client.post("/auth/register", json={"email": "a@b.com", "password": "password1"})
    assert resp.status_code == 201 and resp.json() == {"id": 1}


def test_register_errors(client):
    assert client.post("/auth/register", json={"email": "bad", "password": "password1"}).status_code == 400
    assert client.post("/auth/register", json={"email": "a@b.com", "password": "short"}).status_code == 400
    client.post("/auth/register", json={"email": "a@b.com", "password": "password1"})
    assert client.post("/auth/register", json={"email": "a@b.com", "password": "password1"}).status_code == 409


def test_commands_require_authentication(client):
    for method, url in [("post", "/movies"), ("put", "/movies/1"), ("delete", "/movies/1"),
                        ("post", "/movies/1/reports"), ("put", "/reports/1"), ("delete", "/reports/1")]:
        assert getattr(client, method)(url).status_code == 401, url


def test_movie_commands_lifecycle(auth_client):
    created = auth_client.post("/movies", json=MOVIE)
    assert created.status_code == 201 and set(created.json()) == {"id"}
    mid = created.json()["id"]
    updated = auth_client.put(f"/movies/{mid}", json={**MOVIE, "title": "Dune 2"})
    assert updated.status_code == 204 and updated.content == b""
    assert auth_client.get(f"/movies/{mid}").json()["title"] == "Dune 2"
    assert auth_client.delete(f"/movies/{mid}").status_code == 204
    assert auth_client.get(f"/movies/{mid}").status_code == 404


def test_movie_command_errors(auth_client):
    assert auth_client.post("/movies", json={**MOVIE, "budget_usd": 0}).status_code == 400
    assert auth_client.post("/movies", json={"title": "x"}).status_code == 400
    auth_client.post("/movies", json=MOVIE)
    assert auth_client.post("/movies", json=MOVIE).status_code == 409
    assert auth_client.put("/movies/999", json=MOVIE).status_code == 404
    assert auth_client.delete("/movies/999").status_code == 404


def test_report_commands_lifecycle_and_errors(auth_client):
    mid = auth_client.post("/movies", json=MOVIE).json()["id"]
    url = f"/movies/{mid}/reports"
    created = auth_client.post(url, json=REPORT)
    assert created.status_code == 201
    rid = created.json()["id"]
    assert auth_client.post(url, json=REPORT).status_code == 409
    assert auth_client.post(url, json={**REPORT, "report_date": "2024-02-01"}).status_code == 400
    assert auth_client.post(url, json={**REPORT, "report_date": "2999-01-01"}).status_code == 400
    assert auth_client.post("/movies/999/reports", json=REPORT).status_code == 404
    assert auth_client.put(f"/reports/{rid}", json={"revenue_usd": 700, "tickets_sold": 70}).status_code == 204
    assert auth_client.get(url).json()[0]["revenue_usd"] == 700
    assert auth_client.put(f"/reports/{rid}", json={"revenue_usd": -1, "tickets_sold": 1}).status_code == 400
    assert auth_client.delete(f"/reports/{rid}").status_code == 204
    assert auth_client.delete(f"/reports/{rid}").status_code == 404


def test_deleting_movie_removes_its_reports(auth_client):
    mid = auth_client.post("/movies", json=MOVIE).json()["id"]
    auth_client.post(f"/movies/{mid}/reports", json=REPORT)
    auth_client.delete(f"/movies/{mid}")
    assert auth_client.get(f"/movies/{mid}/reports").status_code == 404
