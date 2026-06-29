"""Pydantic schemas for the Ecommerce COD & Media Buyers Metrics API."""
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Lifecycle of a Cash-on-Delivery (COD) order."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    DELIVERED = "delivered"
    RETURNED = "returned"
    CANCELLED = "cancelled"


class Order(BaseModel):
    """A single Cash-on-Delivery order attributed to a media buyer."""

    order_id: str = Field(..., min_length=1, description="Unique order identifier")
    media_buyer: str = Field(..., min_length=1, description="Media buyer who generated the order")
    product: str = Field(..., min_length=1, description="Product name")
    status: OrderStatus = Field(..., description="Current status of the order")
    revenue: float = Field(..., ge=0, description="Order revenue (collected on delivery)")
    cost_of_goods: float = Field(0.0, ge=0, description="Cost of goods sold for the order")


class AdSpend(BaseModel):
    """Advertising spend booked by a media buyer."""

    media_buyer: str = Field(..., min_length=1, description="Media buyer who spent the budget")
    amount: float = Field(..., ge=0, description="Ad spend amount in the account currency")


class MediaBuyerMetrics(BaseModel):
    """Aggregated KPIs for a single media buyer."""

    media_buyer: str
    total_orders: int
    confirmed_orders: int
    delivered_orders: int
    returned_orders: int
    confirmation_rate: float = Field(..., description="confirmed+delivered / total orders")
    delivery_rate: float = Field(..., description="delivered / confirmed orders")
    revenue: float
    ad_spend: float
    cost_of_goods: float
    profit: float = Field(..., description="delivered revenue - cost of goods - ad spend")
    roas: float = Field(..., description="delivered revenue / ad spend")
    cpa: float = Field(..., description="ad spend / delivered orders")


class GlobalMetrics(BaseModel):
    """Store-wide aggregated KPIs across all media buyers."""

    total_orders: int
    total_revenue: float
    total_ad_spend: float
    total_profit: float
    overall_confirmation_rate: float
    overall_delivery_rate: float
    overall_roas: float
    media_buyers: List[MediaBuyerMetrics]
