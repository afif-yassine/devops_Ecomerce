"""API-level tests using FastAPI's TestClient."""
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def setup_function():
    """Reset the in-memory store before each test for isolation."""
    client.post("/reset")


def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_metrics_endpoint_exposes_prometheus_format():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    # Prometheus exposition format is plain text with HELP/TYPE comments
    assert "# HELP" in resp.text
    assert "cod_global_roas" in resp.text


def test_ingest_orders_and_compute_global_metrics():
    orders = [
        {"order_id": "1", "media_buyer": "alice", "product": "watch",
         "status": "delivered", "revenue": 100.0, "cost_of_goods": 30.0},
        {"order_id": "2", "media_buyer": "alice", "product": "watch",
         "status": "confirmed", "revenue": 100.0, "cost_of_goods": 30.0},
    ]
    spends = [{"media_buyer": "alice", "amount": 50.0}]

    assert client.post("/orders", json=orders).status_code == 201
    assert client.post("/adspend", json=spends).status_code == 201

    g = client.get("/metrics/global").json()
    assert g["total_orders"] == 2
    assert g["total_ad_spend"] == 50.0


def test_unknown_endpoint_returns_404():
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
