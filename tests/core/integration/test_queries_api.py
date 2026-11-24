def test_list_movies_returns_read_model_with_revenue(auth_client, seeded):
    items = auth_client.get("/movies").json()
    assert [m["title"] for m in items] == ["Dune", "Barbie", "Upcoming"]
    assert items[0] == {"id": seeded["dune"], "title": "Dune", "genre": "Sci-Fi",
                        "release_date": "2024-03-01", "budget_usd": 1000, "total_revenue_usd": 3000}
    assert items[2]["total_revenue_usd"] == 0


def test_list_movies_filters_and_pagination(auth_client, seeded):
    assert [m["title"] for m in auth_client.get("/movies", params={"genre": "Comedy"}).json()] == ["Barbie"]
    assert [m["title"] for m in auth_client.get("/movies", params={"year": 2024}).json()] == ["Dune", "Upcoming"]
    assert len(auth_client.get("/movies", params={"limit": 1, "offset": 1}).json()) == 1
    assert auth_client.get("/movies", params={"limit": 0}).status_code == 400


def test_get_movie_details(auth_client, seeded):
    body = auth_client.get(f"/movies/{seeded['dune']}").json()
    assert body["total_revenue_usd"] == 3000 and body["total_tickets"] == 220 and body["reports_count"] == 3
    assert auth_client.get("/movies/999").status_code == 404


def test_list_reports_has_calculated_fields_and_filters(auth_client, seeded):
    url = f"/movies/{seeded['dune']}/reports"
    items = auth_client.get(url).json()
    assert len(items) == 3
    assert items[0]["region"] == "UA" and items[0]["avg_ticket_price_usd"] == 10.0
    assert items[1]["avg_ticket_price_usd"] == 15.0
    assert len(auth_client.get(url, params={"region": "ua"}).json()) == 1
    assert len(auth_client.get(url, params={"date_from": "2024-03-06"}).json()) == 1
    assert len(auth_client.get(url, params={"date_to": "2024-03-05"}).json()) == 2
    assert auth_client.get("/movies/999/reports").status_code == 404


def test_queries_require_authentication(client, seeded):
    for url in ["/movies", f"/movies/{seeded['dune']}", f"/movies/{seeded['dune']}/reports"]:
        assert client.get(url).status_code == 401, url


def test_login_query(client):
    creds = {"email": "a@b.com", "password": "password1"}
    assert client.post("/auth/register", json=creds).status_code == 201
    assert client.post("/auth/login", json=creds).json()["access_token"]
    assert client.post("/auth/login", json={**creds, "password": "wrong-pass"}).status_code == 401
    assert client.post("/auth/login", json={"email": "no@b.com", "password": "password1"}).status_code == 401
