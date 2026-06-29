"""Core metrics engine for Cash-on-Delivery ecommerce and media buyer KPIs.

This module is intentionally framework-agnostic so it can be unit tested
in isolation from FastAPI.
"""
from collections import defaultdict
from typing import Dict, List

from src.schemas import (
    AdSpend,
    GlobalMetrics,
    MediaBuyerMetrics,
    Order,
    OrderStatus,
)


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Return numerator/denominator rounded to 4 decimals, or 0.0 if denom is 0."""
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def compute_media_buyer_metrics(
    orders: List[Order], ad_spends: List[AdSpend]
) -> List[MediaBuyerMetrics]:
    """Aggregate orders and ad spend into per-media-buyer KPIs."""
    spend_by_buyer: Dict[str, float] = defaultdict(float)
    for spend in ad_spends:
        spend_by_buyer[spend.media_buyer] += spend.amount

    orders_by_buyer: Dict[str, List[Order]] = defaultdict(list)
    for order in orders:
        orders_by_buyer[order.media_buyer].append(order)

    buyers = set(spend_by_buyer) | set(orders_by_buyer)
    results: List[MediaBuyerMetrics] = []

    for buyer in sorted(buyers):
        buyer_orders = orders_by_buyer.get(buyer, [])
        total = len(buyer_orders)
        confirmed = sum(
            1
            for o in buyer_orders
            if o.status in (OrderStatus.CONFIRMED, OrderStatus.DELIVERED)
        )
        delivered = sum(1 for o in buyer_orders if o.status == OrderStatus.DELIVERED)
        returned = sum(1 for o in buyer_orders if o.status == OrderStatus.RETURNED)

        delivered_revenue = sum(
            o.revenue for o in buyer_orders if o.status == OrderStatus.DELIVERED
        )
        revenue = sum(o.revenue for o in buyer_orders)
        cost_of_goods = sum(
            o.cost_of_goods for o in buyer_orders if o.status == OrderStatus.DELIVERED
        )
        ad_spend = spend_by_buyer.get(buyer, 0.0)
        profit = round(delivered_revenue - cost_of_goods - ad_spend, 2)

        results.append(
            MediaBuyerMetrics(
                media_buyer=buyer,
                total_orders=total,
                confirmed_orders=confirmed,
                delivered_orders=delivered,
                returned_orders=returned,
                confirmation_rate=_safe_ratio(confirmed, total),
                delivery_rate=_safe_ratio(delivered, confirmed),
                revenue=round(revenue, 2),
                ad_spend=round(ad_spend, 2),
                cost_of_goods=round(cost_of_goods, 2),
                profit=profit,
                roas=_safe_ratio(delivered_revenue, ad_spend),
                cpa=_safe_ratio(ad_spend, delivered),
            )
        )

    return results


def compute_global_metrics(
    orders: List[Order], ad_spends: List[AdSpend]
) -> GlobalMetrics:
    """Aggregate store-wide KPIs across all media buyers."""
    per_buyer = compute_media_buyer_metrics(orders, ad_spends)

    total_orders = len(orders)
    total_confirmed = sum(
        1
        for o in orders
        if o.status in (OrderStatus.CONFIRMED, OrderStatus.DELIVERED)
    )
    total_delivered = sum(1 for o in orders if o.status == OrderStatus.DELIVERED)
    delivered_revenue = sum(
        o.revenue for o in orders if o.status == OrderStatus.DELIVERED
    )
    total_revenue = sum(o.revenue for o in orders)
    total_ad_spend = sum(s.amount for s in ad_spends)
    total_cost = sum(
        o.cost_of_goods for o in orders if o.status == OrderStatus.DELIVERED
    )
    total_profit = round(delivered_revenue - total_cost - total_ad_spend, 2)

    return GlobalMetrics(
        total_orders=total_orders,
        total_revenue=round(total_revenue, 2),
        total_ad_spend=round(total_ad_spend, 2),
        total_profit=total_profit,
        overall_confirmation_rate=_safe_ratio(total_confirmed, total_orders),
        overall_delivery_rate=_safe_ratio(total_delivered, total_confirmed),
        overall_roas=_safe_ratio(delivered_revenue, total_ad_spend),
        media_buyers=per_buyer,
    )
