from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    barcode: str = Field(min_length=1)
    name: str = Field(min_length=1)
    expiration_date: date | None = None


class ProductSummary(BaseModel):
    id: int
    barcode: str
    name: str
    status: str
    archived_at: datetime | None
    expiration_date: date | None
    updated_at: datetime


class DashboardResponse(BaseModel):
    reference_date: date
    due_until: date
    due_items: list[ProductSummary]
    empty_items: list[ProductSummary]


class DiscardCreate(BaseModel):
    product_id: int
    discarded_date: date
    quantity: int = Field(gt=0)
    next_expiration_date: date | None = None


class DiscardResponse(BaseModel):
    product: ProductSummary
    discarded_date: date
    quantity: int


class HealthResponse(BaseModel):
    status: str
