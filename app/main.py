from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.db import get_connection, init_db
from app.schemas import (
    ArchiveResponse,
    ArchivedProductsResponse,
    DashboardResponse,
    DiscardCreate,
    DiscardResponse,
    ExpirationUpdate,
    HealthResponse,
    ProductCreate,
    ProductLookupResponse,
    ProductMutationSummary,
    ProductSummary,
    ProductUpdate,
)

DEFAULT_CATEGORY = "미선택"
ALLOWED_CATEGORIES = {DEFAULT_CATEGORY, "유제품"}


def _map_product(row) -> ProductSummary:
    return ProductSummary.model_validate(dict(row))


def _fetch_product(connection, product_id: int) -> ProductSummary | None:
    row = connection.execute(
        """
        SELECT
            p.id,
            p.barcode,
            p.name,
            p.category,
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


def _fetch_product_by_barcode(
    connection,
    barcode: str,
) -> ProductSummary | None:
    row = connection.execute(
        """
        SELECT
            p.id,
            p.barcode,
            p.name,
            p.category,
            p.status,
            p.archived_at,
            es.expiration_date,
            es.updated_at
        FROM products AS p
        JOIN expiration_states AS es
            ON es.product_id = p.id
        WHERE p.barcode = ?
        """,
        (barcode,),
    ).fetchone()

    return _map_product(row) if row else None


def _normalized_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def _normalized_category(value: str | None) -> str:
    normalized = _normalized_optional_text(value)
    if normalized is None:
        return DEFAULT_CATEGORY

    if normalized not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category must be one of: 미선택, 유제품",
        )

    return normalized


def _normalized_required_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must not be blank",
        )

    return normalized


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Store Expiry Manager API",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post(
    "/products",
    response_model=ProductMutationSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    payload: ProductCreate,
    response: Response,
) -> ProductMutationSummary:
    barcode = _normalized_required_text(payload.barcode, "barcode")
    category = _normalized_category(payload.category)

    with get_connection() as connection:
        existing_product = _fetch_product_by_barcode(connection, barcode)

        if existing_product is not None:
            response.status_code = status.HTTP_200_OK
            return ProductMutationSummary(created=False, product=existing_product)

        name = _normalized_optional_text(payload.name)
        if name is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="name is required for a new product",
            )

        cursor = connection.execute(
            """
            INSERT INTO products (barcode, name, category)
            VALUES (?, ?, ?)
            """,
            (barcode, name, category),
        )

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

    return ProductMutationSummary(created=True, product=product)


@app.get("/products/by-barcode", response_model=ProductLookupResponse)
def get_product_by_barcode(barcode: str = Query(min_length=1)) -> ProductLookupResponse:
    normalized_barcode = _normalized_required_text(barcode, "barcode")

    with get_connection() as connection:
        product = _fetch_product_by_barcode(connection, normalized_barcode)

    return ProductLookupResponse(
        found=product is not None,
        product=product,
    )


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
                p.category,
                p.status,
                p.archived_at,
                es.expiration_date,
                es.updated_at
            FROM products AS p
            JOIN expiration_states AS es
                ON es.product_id = p.id
            WHERE p.status = 'active'
              AND es.expiration_date IS NOT NULL
            ORDER BY
              CASE
                WHEN date(es.expiration_date) < date(?) THEN 0
                WHEN date(es.expiration_date) = date(?) THEN 1
                WHEN date(es.expiration_date) = date(?, '+1 day') THEN 2
                ELSE 3
              END ASC,
              date(es.expiration_date) ASC,
              p.id ASC
            """,
            (
                reference_date.isoformat(),
                reference_date.isoformat(),
                reference_date.isoformat(),
            ),
        ).fetchall()

        unchecked_rows = connection.execute(
            """
            SELECT
                p.id,
                p.barcode,
                p.name,
                p.category,
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
        unchecked_items=[_map_product(row) for row in unchecked_rows],
    )


@app.patch("/products/{product_id}", response_model=ProductSummary)
def update_product(
    product_id: int,
    payload: ProductUpdate,
) -> ProductSummary:
    with get_connection() as connection:
        product = _fetch_product(connection, product_id)

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="product not found",
            )

        updates: dict[str, str | None] = {}

        provided_fields = payload.model_fields_set

        if "name" in provided_fields:
            if payload.name is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="name must not be blank",
                )
            updates["name"] = _normalized_required_text(payload.name, "name")

        if "barcode" in provided_fields:
            if payload.barcode is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="barcode must not be blank",
                )
            next_barcode = _normalized_required_text(payload.barcode, "barcode")
            existing_product = _fetch_product_by_barcode(connection, next_barcode)

            if existing_product is not None and existing_product.id != product_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="barcode already exists",
                )

            updates["barcode"] = next_barcode

        if "category" in provided_fields:
            updates["category"] = _normalized_category(payload.category)

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="at least one product field is required",
            )

        assignments = ", ".join(f"{column} = ?" for column in updates)

        connection.execute(
            f"""
            UPDATE products
            SET {assignments}
            WHERE id = ?
            """,
            (*updates.values(), product_id),
        )

        updated_product = _fetch_product(connection, product_id)

    if updated_product is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to update product",
        )

    return updated_product


@app.patch("/products/{product_id}/expiration", response_model=ProductSummary)
def update_expiration(
    product_id: int,
    payload: ExpirationUpdate,
) -> ProductSummary:
    with get_connection() as connection:
        product = _fetch_product(connection, product_id)

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="product not found",
            )

        if product.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="expiration update is allowed only for active products",
            )

        connection.execute(
            """
            UPDATE expiration_states
            SET expiration_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE product_id = ?
            """,
            (
                payload.expiration_date.isoformat()
                if payload.expiration_date is not None
                else None,
                product_id,
            ),
        )

        updated_product = _fetch_product(connection, product_id)

    if updated_product is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to update expiration",
        )

    return updated_product


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
            SET expiration_date = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE product_id = ?
            """,
            (payload.product_id,),
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


@app.patch("/products/{product_id}/archive", response_model=ArchiveResponse)
def archive_product(product_id: int) -> ArchiveResponse:
    with get_connection() as connection:
        product = _fetch_product(connection, product_id)

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="product not found",
            )

        if product.status == "archived":
            return ArchiveResponse(product=product)

        connection.execute(
            """
            UPDATE products
            SET status = 'archived',
                archived_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (product_id,),
        )

        archived_product = _fetch_product(connection, product_id)

    if archived_product is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to archive product",
        )

    return ArchiveResponse(product=archived_product)


@app.patch("/products/{product_id}/restore", response_model=ArchiveResponse)
def restore_product(product_id: int) -> ArchiveResponse:
    with get_connection() as connection:
        product = _fetch_product(connection, product_id)

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="product not found",
            )

        if product.status == "active":
            return ArchiveResponse(product=product)

        connection.execute(
            """
            UPDATE products
            SET status = 'active',
                archived_at = NULL
            WHERE id = ?
            """,
            (product_id,),
        )
        connection.execute(
            """
            UPDATE expiration_states
            SET expiration_date = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE product_id = ?
            """,
            (product_id,),
        )

        restored_product = _fetch_product(connection, product_id)

    if restored_product is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to restore product",
        )

    return ArchiveResponse(product=restored_product)


@app.get("/archived-products", response_model=ArchivedProductsResponse)
def get_archived_products(
    query: str | None = Query(default=None),
) -> ArchivedProductsResponse:
    normalized_query = _normalized_optional_text(query)

    with get_connection() as connection:
        if normalized_query is None:
            rows = connection.execute(
                """
                SELECT
                    p.id,
                    p.barcode,
                    p.name,
                    p.category,
                    p.status,
                    p.archived_at,
                    es.expiration_date,
                    es.updated_at
                FROM products AS p
                JOIN expiration_states AS es
                    ON es.product_id = p.id
                WHERE p.status = 'archived'
                ORDER BY p.archived_at DESC, p.id DESC
                """
            ).fetchall()
        else:
            like_query = f"%{normalized_query}%"
            rows = connection.execute(
                """
                SELECT
                    p.id,
                    p.barcode,
                    p.name,
                    p.category,
                    p.status,
                    p.archived_at,
                    es.expiration_date,
                    es.updated_at
                FROM products AS p
                JOIN expiration_states AS es
                    ON es.product_id = p.id
                WHERE p.status = 'archived'
                  AND (
                    p.barcode LIKE ?
                    OR p.name LIKE ?
                    OR COALESCE(p.category, '') LIKE ?
                  )
                ORDER BY p.archived_at DESC, p.id DESC
                """,
                (like_query, like_query, like_query),
            ).fetchall()

    return ArchivedProductsResponse(
        query=normalized_query,
        items=[_map_product(row) for row in rows],
    )
