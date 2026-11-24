import time

MOVIE = {"title": "Dune", "genre": "Sci-Fi", "release_date": "2024-03-01", "budget_usd": 1000}


def report(day, region, revenue, tickets):
    return {"report_date": day, "region": region, "revenue_usd": revenue, "tickets_sold": tickets}


def test_core_is_strongly_consistent_analytics_lags_then_catches_up(tmp_path):
    from fastapi.testclient import TestClient
    from boxoffice.bootstrap import build_app

    app = build_app(f"sqlite:///{tmp_path / 'lag.db'}", analytics_lag_s=0.3)
    c = TestClient(app)
    creds = {"email": "t@example.com", "password": "secret123"}
    c.post("/auth/register", json=creds)
    c.headers["Authorization"] = "Bearer " + c.post("/auth/login", json=creds).json()["access_token"]

    mid = c.post("/movies", json=MOVIE).json()["id"]
    c.post(f"/movies/{mid}/reports", json=report("2024-03-05", "US", 1500, 100))

    assert c.get(f"/movies/{mid}").json()["total_revenue_usd"] == 1500
    assert c.get(f"/movies/{mid}/summary").status_code == 404
    assert c.get("/analytics/top").json() == []

    assert app.state.bus.wait_idle(10)
    summary = c.get(f"/movies/{mid}/summary").json()
    assert summary["total_revenue_usd"] == 1500 and summary["title"] == "Dune"
    assert c.get("/analytics/top").json()[0]["title"] == "Dune"


def test_analytics_projection_follows_core_changes(auth_client, settle):
    c = auth_client
    a = c.post("/movies", json=MOVIE).json()["id"]
    b = c.post("/movies", json={**MOVIE, "title": "Barbie", "release_date": "2024-01-01", "budget_usd": 200}).json()["id"]
    c.post(f"/movies/{a}/reports", json=report("2024-03-05", "US", 1500, 100))
    c.post(f"/movies/{a}/reports", json=report("2024-03-05", "UA", 500, 50))
    rid_b = c.post(f"/movies/{b}/reports", json=report("2024-02-01", "US", 300, 30)).json()["id"]
    settle()

    s = c.get(f"/movies/{a}/summary").json()
    assert (s["total_revenue_usd"], s["total_tickets"], s["avg_ticket_price_usd"], s["roi"]) == (2000, 150, 13.33, 1.0)
    assert s["revenue_by_region"] == [{"region": "US", "revenue_usd": 1500}, {"region": "UA", "revenue_usd": 500}]
    assert [t["title"] for t in c.get("/analytics/top").json()] == ["Dune", "Barbie"]
    assert c.get("/analytics/regions").json() == [{"region": "US", "revenue_usd": 1800}, {"region": "UA", "revenue_usd": 500}]

    c.put(f"/reports/{rid_b}", json={"revenue_usd": 100, "tickets_sold": 10})
    c.put(f"/movies/{a}", json={**MOVIE, "title": "Dune: Part Two", "budget_usd": 500})
    settle()
    assert c.get(f"/movies/{b}/summary").json()["total_revenue_usd"] == 100
    s = c.get(f"/movies/{a}/summary").json()
    assert s["title"] == "Dune: Part Two" and s["roi"] == 3.0

    c.delete(f"/reports/{rid_b}")
    c.delete(f"/movies/{a}")
    settle()
    assert c.get(f"/movies/{a}/summary").status_code == 404
    assert c.get("/analytics/regions").json() == []
    assert c.get(f"/movies/{b}/summary").json()["total_revenue_usd"] == 0


def test_audit_module_receives_the_same_events(auth_client, settle):
    c = auth_client
    mid = c.post("/movies", json=MOVIE).json()["id"]
    c.post(f"/movies/{mid}/reports", json=report("2024-03-05", "US", 500, 50))
    settle()
    entries = c.get("/audit").json()
    assert [e["action"] for e in entries] == ["user.registered", "movie.created", "report.added"]


def test_core_keeps_working_when_analytics_is_broken(app, auth_client, settle):
    import boxoffice.modules.analytics.application.handlers as h
    original = h.ProjectionHandler.handle

    def broken(self, cmd):
        raise RuntimeError("analytics down")

    h.ProjectionHandler.handle = broken
    try:
        resp = auth_client.post("/movies", json=MOVIE)
        settle()
    finally:
        h.ProjectionHandler.handle = original
    assert resp.status_code == 201 and auth_client.get(f"/movies/{resp.json()['id']}").status_code == 200
    assert len(app.state.bus.dead_letters) >= 1
    assert [e["action"] for e in auth_client.get("/audit").json()][-1] == "movie.created"


def test_analytics_endpoints_require_authentication(client):
    for url in ["/analytics/top", "/analytics/regions", "/movies/1/summary", "/audit"]:
        assert client.get(url).status_code == 401, url
