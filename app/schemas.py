from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    barcode: str = Field(min_length=1)
    name: str | None = None
    category: str | None = None
    expiration_date: date | None = None


class ProductSummary(BaseModel):
    id: int
    barcode: str
    name: str
    category: str | None
    status: str
    archived_at: datetime | None
    expiration_date: date | None
    updated_at: datetime


class ProductMutationSummary(BaseModel):
    created: bool
    product: ProductSummary


class ProductLookupResponse(BaseModel):
    found: bool
    product: ProductSummary | None = None


class DashboardResponse(BaseModel):
    reference_date: date
    due_until: date
    due_items: list[ProductSummary]
    unchecked_items: list[ProductSummary]


class DiscardCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class DiscardResponse(BaseModel):
    product: ProductSummary
    discarded_date: date
    quantity: int


class ExpirationUpdate(BaseModel):
    expiration_date: date | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    barcode: str | None = Field(default=None, min_length=1)
    category: str | None = None


class ArchiveResponse(BaseModel):
    product: ProductSummary


class ArchivedProductsResponse(BaseModel):
    query: str | None
    items: list[ProductSummary]


class HealthResponse(BaseModel):
    status: str
