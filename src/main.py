"""FastAPI application: Ecommerce COD & Media Buyers Metrics API.

Exposes:
- GET  /health   -> liveness probe used by Docker healthcheck and smoke test
- GET  /metrics  -> Prometheus exposition format (scraped by Prometheus)
- POST /orders   -> ingest a batch of COD orders
- POST /adspend  -> ingest a batch of ad-spend records
- GET  /metrics/media-buyers -> per media buyer KPIs (ROAS, CPA, confirmation rate...)
- GET  /metrics/global       -> store-wide KPIs
- POST /reset    -> clear the in-memory store (useful for demos/tests)
"""
from typing import List

from fastapi import FastAPI
from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

from src.metrics_engine import compute_global_metrics, compute_media_buyer_metrics
from src.schemas import AdSpend, GlobalMetrics, MediaBuyerMetrics, Order

app = FastAPI(
    title="Ecommerce COD & Media Buyers Metrics API",
    description=(
        "API de calcul de metriques e-commerce en Cash on Delivery (COD) "
        "et de performance des media buyers (ROAS, CPA, taux de confirmation, "
        "taux de livraison, profit)."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# In-memory data store (sufficient for a demo / CI pipeline; no DB required).
# ---------------------------------------------------------------------------
_ORDERS: List[Order] = []
_AD_SPENDS: List[AdSpend] = []

# ---------------------------------------------------------------------------
# Custom business metrics exposed to Prometheus.
# ---------------------------------------------------------------------------
ORDERS_INGESTED = Counter(
    "cod_orders_ingested_total",
    "Nombre total de commandes COD ingerees",
    ["status"],
)
ADSPEND_INGESTED = Counter(
    "cod_adspend_ingested_total",
    "Nombre total d'enregistrements d'ad spend ingeres",
)
GLOBAL_ROAS = Gauge(
    "cod_global_roas",
    "ROAS global (revenu livre / ad spend)",
)
GLOBAL_CONFIRMATION_RATE = Gauge(
    "cod_global_confirmation_rate",
    "Taux de confirmation global des commandes COD",
)
GLOBAL_PROFIT = Gauge(
    "cod_global_profit",
    "Profit global (revenu livre - cout des biens - ad spend)",
)


def _refresh_global_gauges() -> None:
    """Recompute and publish global gauges after each ingestion."""
    metrics = compute_global_metrics(_ORDERS, _AD_SPENDS)
    GLOBAL_ROAS.set(metrics.overall_roas)
    GLOBAL_CONFIRMATION_RATE.set(metrics.overall_confirmation_rate)
    GLOBAL_PROFIT.set(metrics.total_profit)


@app.get("/health")
def health() -> dict:
    """Liveness probe. Returns 200 with a fixed JSON body."""
    return {"status": "ok"}


@app.post("/orders", status_code=201)
def ingest_orders(orders: List[Order]) -> dict:
    """Ingest a batch of COD orders into the in-memory store."""
    for order in orders:
        _ORDERS.append(order)
        ORDERS_INGESTED.labels(status=order.status.value).inc()
    _refresh_global_gauges()
    return {"ingested": len(orders), "total_orders": len(_ORDERS)}


@app.post("/adspend", status_code=201)
def ingest_adspend(spends: List[AdSpend]) -> dict:
    """Ingest a batch of ad-spend records into the in-memory store."""
    for spend in spends:
        _AD_SPENDS.append(spend)
        ADSPEND_INGESTED.inc()
    _refresh_global_gauges()
    return {"ingested": len(spends), "total_adspend_records": len(_AD_SPENDS)}


@app.get("/metrics/media-buyers", response_model=List[MediaBuyerMetrics])
def media_buyer_metrics() -> List[MediaBuyerMetrics]:
    """Return per-media-buyer KPIs."""
    return compute_media_buyer_metrics(_ORDERS, _AD_SPENDS)


@app.get("/metrics/global", response_model=GlobalMetrics)
def global_metrics() -> GlobalMetrics:
    """Return store-wide KPIs across all media buyers."""
    return compute_global_metrics(_ORDERS, _AD_SPENDS)


@app.post("/reset")
def reset() -> dict:
    """Clear the in-memory store. Useful for demos and tests."""
    _ORDERS.clear()
    _AD_SPENDS.clear()
    _refresh_global_gauges()
    return {"status": "reset"}


# ---------------------------------------------------------------------------
# Prometheus instrumentation: exposes the /metrics endpoint.
# ---------------------------------------------------------------------------
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
