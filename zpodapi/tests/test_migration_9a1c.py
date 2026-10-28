"""Migration 9a1c4e7b2d3f removes the duplicate deploy networks before its constraint.

A deploy flow run that ran again (0.8 and earlier) appended a second /24 of four
rows; the (zpod_id, vlan_id) unique constraint then failed the whole upgrade.
"""

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa

MIGRATION = next(
    (Path(__file__).parents[1] / "scripts" / "alembic" / "versions").glob(
        "*9a1c4e7b2d3f*.py"
    )
)


@pytest.fixture(scope="module")
def migration():
    spec = importlib.util.spec_from_file_location("m9a1c", MIGRATION)
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
        c.execute(
            sa.text(
                "CREATE TABLE zpod_networks (id INTEGER PRIMARY KEY, zpod_id INTEGER, cidr TEXT)"
            )
        )
        yield c


def add_zpod(conn, zpod_id, name, status, *slash24s):
    conn.execute(
        sa.text("INSERT INTO zpods VALUES (:i, :n, :s)"),
        {"i": zpod_id, "n": name, "s": status},
    )
    for net in slash24s:
        for octet in (0, 64, 128, 192):
            conn.execute(
                sa.text("INSERT INTO zpod_networks (zpod_id, cidr) VALUES (:z, :c)"),
                {"z": zpod_id, "c": f"{net}.{octet}/26"},
            )


def networks(conn, zpod_id):
    return [
        r.cidr
        for r in conn.execute(
            sa.text("SELECT cidr FROM zpod_networks WHERE zpod_id = :z ORDER BY id"),
            {"z": zpod_id},
        )
    ]


def test_a_clean_database_is_untouched(migration, conn):
    add_zpod(conn, 1, "lab", "ACTIVE", "10.10.1")
    add_zpod(conn, 2, "old", "DELETED", "10.10.2")
    assert migration.remove_duplicate_deploy_networks(conn) == 0
    assert len(networks(conn, 1)) == len(networks(conn, 2)) == 4


def test_a_deleted_zpod_keeps_its_first_slash24(migration, conn):
    add_zpod(conn, 1, "lab", "ACTIVE", "10.10.1")
    add_zpod(conn, 31, "retried", "DELETED", "10.42.132", "10.42.181", "10.42.172")
    assert migration.remove_duplicate_deploy_networks(conn) == 8
    assert networks(conn, 31) == [f"10.42.132.{o}/26" for o in (0, 64, 128, 192)]
    assert len(networks(conn, 1)) == 4


def test_a_single_extra_row_is_removed(migration, conn):
    add_zpod(conn, 5, "odd", "DELETED", "10.10.5")
    conn.execute(
        sa.text(
            "INSERT INTO zpod_networks (zpod_id, cidr) VALUES (5, '10.99.9.128/26')"
        )
    )
    assert migration.remove_duplicate_deploy_networks(conn) == 1
    assert "10.99.9.128/26" not in networks(conn, 5)


def test_a_live_zpod_keeps_its_first_slash24(migration, conn):
    add_zpod(conn, 7, "cloud", "ACTIVE", "10.10.7", "10.10.8")
    assert migration.remove_duplicate_deploy_networks(conn) == 4
    assert networks(conn, 7) == [f"10.10.7.{o}/26" for o in (0, 64, 128, 192)]


def test_downgrade_refuses_user_vlans_on_live_zpods(migration, conn, monkeypatch):
    conn.execute(
        sa.text("ALTER TABLE zpod_networks ADD COLUMN kind TEXT DEFAULT 'zpod'")
    )
    conn.execute(sa.text("ALTER TABLE zpod_networks ADD COLUMN name TEXT DEFAULT ''"))
    add_zpod(conn, 1, "lab", "ACTIVE", "10.10.1")
    add_zpod(conn, 2, "old", "DELETED", "10.10.2")
    for zpod_id in (1, 2):
        conn.execute(
            sa.text(
                "INSERT INTO zpod_networks (zpod_id, cidr, kind, name) "
                "VALUES (:z, '10.42.111.0/24', 'user', 'LOCALNET111')"
            ),
            {"z": zpod_id},
        )
    dropped = []
    monkeypatch.setattr(migration.op, "get_bind", lambda: conn, raising=False)
    monkeypatch.setattr(
        migration.op,
        "drop_constraint",
        lambda *a, **k: dropped.append(a),
        raising=False,
    )
    with pytest.raises(RuntimeError, match="zcli zpod network remove lab LOCALNET111"):
        migration.downgrade()
    assert not dropped

    conn.execute(sa.text("UPDATE zpods SET status = 'DELETED' WHERE id = 1"))
    monkeypatch.setattr(
        migration.op, "drop_column", lambda *a, **k: None, raising=False
    )
    migration.downgrade()
    assert (
        conn.execute(
            sa.text("SELECT count(*) FROM zpod_networks WHERE kind = 'user'")
        ).scalar()
        == 0
    )
