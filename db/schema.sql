PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    barcode TEXT NOT NULL UNIQUE
        CHECK (length(trim(barcode)) > 0),
    name TEXT NOT NULL
        CHECK (length(trim(name)) > 0),
    category TEXT
        CHECK (category IS NULL OR length(trim(category)) > 0),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'archived')),
    archived_at TEXT
        CHECK (archived_at IS NULL OR datetime(archived_at) IS NOT NULL),
    CHECK (
        (status = 'active' AND archived_at IS NULL) OR
        (status = 'archived' AND archived_at IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS expiration_states (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL UNIQUE,
    expiration_date TEXT
        CHECK (
            expiration_date IS NULL OR (
                expiration_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                AND date(expiration_date) IS NOT NULL
            )
        ),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS discard_histories (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    discarded_date TEXT NOT NULL
        CHECK (
            discarded_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
            AND date(discarded_date) IS NOT NULL
        ),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    FOREIGN KEY (product_id) REFERENCES products (id)
        ON DELETE RESTRICT
);

CREATE TRIGGER IF NOT EXISTS trg_products_insert_create_expiration_state
AFTER INSERT ON products
BEGIN
    INSERT INTO expiration_states (product_id, expiration_date)
    VALUES (NEW.id, NULL);
END;

CREATE TRIGGER IF NOT EXISTS trg_products_archive_clear_expiration
AFTER UPDATE OF status ON products
FOR EACH ROW
WHEN NEW.status = 'archived'
BEGIN
    UPDATE expiration_states
    SET expiration_date = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE product_id = NEW.id;
END;

CREATE INDEX IF NOT EXISTS idx_products_status
    ON products (status);

CREATE INDEX IF NOT EXISTS idx_products_barcode
    ON products (barcode);

CREATE INDEX IF NOT EXISTS idx_expiration_states_expiration_date
    ON expiration_states (expiration_date);

CREATE INDEX IF NOT EXISTS idx_discard_histories_product_date
    ON discard_histories (product_id, discarded_date);
