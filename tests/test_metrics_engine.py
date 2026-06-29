"""Unit tests for the metrics engine (pure business logic)."""
from src.metrics_engine import compute_global_metrics, compute_media_buyer_metrics
from src.schemas import AdSpend, Order, OrderStatus


def _sample_orders():
    return [
        Order(order_id="1", media_buyer="alice", product="watch",
              status=OrderStatus.DELIVERED, revenue=100.0, cost_of_goods=30.0),
        Order(order_id="2", media_buyer="alice", product="watch",
              status=OrderStatus.CONFIRMED, revenue=100.0, cost_of_goods=30.0),
        Order(order_id="3", media_buyer="alice", product="watch",
              status=OrderStatus.RETURNED, revenue=100.0, cost_of_goods=30.0),
        Order(order_id="4", media_buyer="bob", product="bag",
              status=OrderStatus.DELIVERED, revenue=200.0, cost_of_goods=80.0),
    ]


def _sample_adspend():
    return [
        AdSpend(media_buyer="alice", amount=50.0),
        AdSpend(media_buyer="bob", amount=40.0),
    ]


def test_media_buyer_confirmation_and_delivery_rates():
    """confirmation_rate = (confirmed+delivered)/total ; delivery_rate = delivered/confirmed."""
    metrics = compute_media_buyer_metrics(_sample_orders(), _sample_adspend())
    alice = next(m for m in metrics if m.media_buyer == "alice")

    assert alice.total_orders == 3
    assert alice.confirmed_orders == 2  # 1 confirmed + 1 delivered
    assert alice.delivered_orders == 1
    # confirmation_rate = 2/3
    assert alice.confirmation_rate == round(2 / 3, 4)
    # delivery_rate = 1/2
    assert alice.delivery_rate == 0.5


def test_media_buyer_roas_cpa_and_profit():
    """ROAS = delivered revenue / ad spend ; profit = delivered rev - cogs - spend."""
    metrics = compute_media_buyer_metrics(_sample_orders(), _sample_adspend())
    bob = next(m for m in metrics if m.media_buyer == "bob")

    # bob: 1 delivered order, revenue 200, cogs 80, spend 40
    assert bob.roas == round(200.0 / 40.0, 4)  # 5.0
    assert bob.cpa == round(40.0 / 1, 4)        # 40.0
    assert bob.profit == 200.0 - 80.0 - 40.0    # 80.0


def test_global_metrics_aggregation():
    """Global metrics aggregate across all media buyers correctly."""
    g = compute_global_metrics(_sample_orders(), _sample_adspend())

    assert g.total_orders == 4
    assert g.total_ad_spend == 90.0
    # delivered revenue = 100 (alice) + 200 (bob) = 300 ; cogs = 30 + 80 = 110
    # profit = 300 - 110 - 90 = 100
    assert g.total_profit == 100.0
    assert g.overall_roas == round(300.0 / 90.0, 4)


def test_safe_ratio_handles_zero_division():
    """A media buyer with no orders/spend must not raise ZeroDivisionError."""
    g = compute_global_metrics([], [])
    assert g.overall_roas == 0.0
    assert g.overall_confirmation_rate == 0.0
    assert g.total_profit == 0.0
