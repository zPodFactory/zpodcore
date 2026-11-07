"""Migration 7c3f9a2e5b1d allows one live zPod per name, and refuses a database
that already breaks that rather than guessing which duplicate to keep."""

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa

MIGRATION = next(
    (Path(__file__).parents[1] / "scripts" / "alembic" / "versions").glob(
        "*7c3f9a2e5b1d*.py"
    )
)


@pytest.fixture(scope="module")
def migration():
    spec = importlib.util.spec_from_file_location("m7c3f", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def conn():
    engine = sa.create_engine("sqlite://")
    with engine.begin() as c:
        c.execute(
            sa.text(
                "CREATE TABLE zpods (id INTEGER PRIMARY KEY, name TEXT, status TEXT)"
            )
        )
        yield c


def add(conn, zpod_id, name, status):
    conn.execute(
        sa.text("INSERT INTO zpods VALUES (:i, :n, :s)"),
        {"i": zpod_id, "n": name, "s": status},
    )


def test_deleted_rows_are_not_duplicates(migration, conn):
    add(conn, 1, "lab", "DELETED")
    add(conn, 2, "lab", "DELETED")
    add(conn, 3, "lab", "ACTIVE")
    add(conn, 4, "other", "DESTROY_FAILED")
    assert migration.live_duplicates(conn) == []


def test_live_duplicates_are_named(migration, conn):
    add(conn, 1, "lab", "DELETED")
    add(conn, 2, "lab", "ACTIVE")
    add(conn, 3, "lab", "DEPLOY_FAILED")
    add(conn, 4, "other", "ACTIVE")
    assert migration.live_duplicates(conn) == [
        (2, "lab", "ACTIVE"),
        (3, "lab", "DEPLOY_FAILED"),
    ]


def test_upgrade_refuses_live_duplicates(migration, conn, monkeypatch):
    add(conn, 2, "lab", "ACTIVE")
    add(conn, 3, "lab", "DEPLOY_FAILED")
    monkeypatch.setattr(migration.op, "get_bind", lambda: conn)
    monkeypatch.setattr(migration.context, "is_offline_mode", lambda: False)
    with pytest.raises(RuntimeError) as exc:
        migration.upgrade()
    assert "id 2: lab (ACTIVE)" in str(exc.value)
    assert "id 3: lab (DEPLOY_FAILED)" in str(exc.value)


def test_index_lets_a_name_live_once(migration, conn):
    conn.execute(
        sa.text(
            f"CREATE UNIQUE INDEX {migration.INDEX} ON zpods (name) WHERE {migration.LIVE}"
        )
    )
    add(conn, 1, "lab", "DELETED")
    add(conn, 2, "lab", "DELETED")
    add(conn, 3, "lab", "DELETING")
    with pytest.raises(sa.exc.IntegrityError):
        add(conn, 4, "lab", "PENDING")
    # The resurrection write: a deploy finishing on a destroyed zPod.
    with pytest.raises(sa.exc.IntegrityError):
        conn.execute(sa.text("UPDATE zpods SET status='ACTIVE' WHERE id=1"))
