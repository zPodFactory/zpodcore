"""zpods: one live row per name

Revision ID: 7c3f9a2e5b1d
Revises: 4d2e8b1c9f6a
Create Date: 2026-11-07 12:00:00.000000

A zPod is soft-deleted (status DELETED) and its name may then be used again, so
the name alone cannot be unique. The API refused a name already live, but a
deploy flow still running after a destroy of its zPod wrote ACTIVE back over
DELETED, next to the new zPod of the same name. This partial unique index makes
that write fail instead.

An existing database may already hold such duplicates. They cannot be told apart
here (both may own VMs), so the upgrade refuses and names them: destroy one, or
set its status to DELETED, then run the upgrade again.
"""

from collections import Counter

import sqlalchemy as sa
from alembic import context, op

# revision identifiers, used by Alembic.
revision = "7c3f9a2e5b1d"
down_revision = "4d2e8b1c9f6a"
branch_labels = None
depends_on = None

INDEX = "zpods_name_live_key"
LIVE = "status <> 'DELETED'"


def live_duplicates(conn) -> list[tuple[int, str, str]]:
    """(id, name, status) of every live zPod whose name another live zPod has."""
    rows = conn.execute(
        sa.text(f"SELECT id, name, status FROM zpods WHERE {LIVE} ORDER BY name, id")
    ).fetchall()
    counts = Counter(row.name for row in rows)
    return [tuple(row) for row in rows if counts[row.name] > 1]


def upgrade():
    # `alembic upgrade --sql` has no connection to look at the rows with.
    duplicates = [] if context.is_offline_mode() else live_duplicates(op.get_bind())
    if duplicates:
        raise RuntimeError(
            "Several zPods that are not DELETED share a name; only one may stay. "
            "Destroy the others (or set their status to DELETED) and upgrade again:\n"
            + "\n".join(
                f"  id {zpod_id}: {name} ({status})"
                for zpod_id, name, status in duplicates
            )
        )
    op.create_index(
        INDEX,
        "zpods",
        ["name"],
        unique=True,
        postgresql_where=sa.text(LIVE),
        sqlite_where=sa.text(LIVE),
    )


def downgrade():
    op.drop_index(INDEX, table_name="zpods")
