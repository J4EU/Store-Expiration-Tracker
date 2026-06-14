from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException, Query, status

from app.db import get_connection, init_db
from app.schemas import (
    DashboardResponse,
    DiscardCreate,
    DiscardResponse,
    HealthResponse,
    ProductCreate,
    ProductSummary,
)


def _map_product(row) -> ProductSummary:
    return ProductSummary.model_validate(dict(row))


def _fetch_product(connection, product_id: int) -> ProductSummary | None:
    row = connection.execute(
        """
        SELECT
            p.id,
            p.barcode,
            p.name,
            p.status,
            p.archived_at,
            es.expiration_date,
            es.updated_at
        FROM products AS p
        JOIN expiration_states AS es
            ON es.product_id = p.id
        WHERE p.id = ?
        """,
        (product_id,),
    ).fetchone()

    return _map_product(row) if row else None


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Store Expiry Manager API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post(
    "/products",
    response_model=ProductSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_product(payload: ProductCreate) -> ProductSummary:
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO products (barcode, name)
                VALUES (?, ?)
                """,
                (payload.barcode.strip(), payload.name.strip()),
            )
        except Exception as exc:
            if "UNIQUE constraint failed: products.barcode" in str(exc):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="barcode already exists",
                ) from exc
            raise

        if payload.expiration_date is not None:
            connection.execute(
                """
                UPDATE expiration_states
                SET expiration_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE product_id = ?
                """,
                (payload.expiration_date.isoformat(), cursor.lastrowid),
            )

        product = _fetch_product(connection, cursor.lastrowid)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to create product",
        )

    return product


@app.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    reference_date: date = Query(default_factory=date.today),
) -> DashboardResponse:
    due_until = reference_date + timedelta(days=1)

    with get_connection() as connection:
        due_rows = connection.execute(
            """
            SELECT
                p.id,
                p.barcode,
                p.name,
                p.status,
                p.archived_at,
                es.expiration_date,
                es.updated_at
            FROM products AS p
            JOIN expiration_states AS es
                ON es.product_id = p.id
            WHERE p.status = 'active'
              AND es.expiration_date IS NOT NULL
              AND date(es.expiration_date) <= date(?)
            ORDER BY date(es.expiration_date) ASC, p.id ASC
            """,
            (due_until.isoformat(),),
        ).fetchall()

        empty_rows = connection.execute(
            """
            SELECT
                p.id,
                p.barcode,
                p.name,
                p.status,
                p.archived_at,
                es.expiration_date,
                es.updated_at
            FROM products AS p
            JOIN expiration_states AS es
                ON es.product_id = p.id
            WHERE p.status = 'active'
              AND es.expiration_date IS NULL
            ORDER BY es.updated_at ASC, p.id ASC
            """
        ).fetchall()

    return DashboardResponse(
        reference_date=reference_date,
        due_until=due_until,
        due_items=[_map_product(row) for row in due_rows],
        empty_items=[_map_product(row) for row in empty_rows],
    )


@app.post(
    "/discards",
    response_model=DiscardResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_discard(payload: DiscardCreate) -> DiscardResponse:
    with get_connection() as connection:
        product = _fetch_product(connection, payload.product_id)

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="product not found",
            )

        if product.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="discard is allowed only for active products",
            )

        connection.execute(
            """
            INSERT INTO discard_histories (product_id, discarded_date, quantity)
            VALUES (?, ?, ?)
            """,
            (
                payload.product_id,
                payload.discarded_date.isoformat(),
                payload.quantity,
            ),
        )

        connection.execute(
            """
            UPDATE expiration_states
            SET expiration_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE product_id = ?
            """,
            (
                payload.next_expiration_date.isoformat()
                if payload.next_expiration_date is not None
                else None,
                payload.product_id,
            ),
        )

        updated_product = _fetch_product(connection, payload.product_id)

    if updated_product is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to update product state",
        )

    return DiscardResponse(
        product=updated_product,
        discarded_date=payload.discarded_date,
        quantity=payload.quantity,
    )
