"""endpoint_status

Revision ID: dd8eb1dea37f
Revises: ff3998a4f8da
Create Date: 2024-04-10 14:14:58.473415

"""

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.sql import text
from sqlalchemy.sql.expression import false

# revision identifiers, used by Alembic.
revision = "dd8eb1dea37f"
down_revision = "ff3998a4f8da"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("ix_endpoints_name", table_name="endpoints")
    op.add_column(
        "endpoints",
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    endpoints_table = sa.sql.table(
        "endpoints",
        sa.Column("id", sa.INTEGER()),
        sa.Column("enabled", sa.VARCHAR()),
        sa.Column("status", sa.VARCHAR()),
        sa.Column("endpoints", sa.JSON()),
    )
    op.execute(
        endpoints_table.update()
        .where(endpoints_table.c.enabled)
        .values(status="ACTIVE")
    )
    op.execute(
        endpoints_table.update()
        .where(endpoints_table.c.enabled == false())
        .values(status="DELETED")
    )
    op.alter_column("endpoints", "status", existing_type=sa.VARCHAR(), nullable=False)
    op.drop_column("endpoints", "enabled")

    conn = op.get_bind()
    results = conn.execute(text("select id, endpoints from endpoints")).fetchall()
    for id_, endpoints in results:
        if "name" in endpoints["compute"]:
            endpoints["compute"].pop("name")
        if "name" in endpoints["network"]:
            endpoints["network"].pop("name")
        if "macdiscoveryprofile" in endpoints["network"]:
            endpoints["network"].pop("macdiscoveryprofile")
        if (
            "driver" in endpoints["network"]
            and endpoints["network"]["driver"] == "nsxt-projects"
        ):
            endpoints["network"]["driver"] = "nsxt_projects"

        op.execute(
            endpoints_table.update()
            .where(endpoints_table.c.id == id_)
            .values(endpoints=endpoints)
        )



def downgrade():
    op.create_index("ix_endpoints_name", "endpoints", ["name"], unique=True)
    op.add_column(
        "endpoints",
        sa.Column("enabled", sa.BOOLEAN(), autoincrement=False, nullable=True),
    )

    endpoints_table = sa.sql.table(
        "endpoints",
        sa.Column("id", sa.INTEGER()),
        sa.Column("enabled", sa.VARCHAR()),
        sa.Column("status", sa.VARCHAR()),
        sa.Column("endpoints", sa.JSON()),
    )

    op.execute(
        endpoints_table.update()
        .where(endpoints_table.c.status == "ACTIVE")
        .values(enabled=True)
    )
    op.execute(
        endpoints_table.update()
        .where(endpoints_table.c.status == "DELETED")
        .values(enabled=False)
    )

    op.alter_column("endpoints", "enabled", existing_type=sa.VARCHAR(), nullable=False)

    op.drop_column("endpoints", "status")

    conn = op.get_bind()
    res = conn.execute(text("select id, endpoints from endpoints"))
    results = res.fetchall()
    for id_, endpoints in results:
        endpoints["compute"]["name"] = endpoints["compute"]["hostname"]
        endpoints["network"]["name"] = endpoints["network"]["hostname"]
        endpoints["network"]["macdiscoveryprofile"] = ""
        if (
            "driver" in endpoints["network"]
            and endpoints["network"]["driver"] == "nsxt_projects"
        ):
            endpoints["network"]["driver"] = "nsxt-projects"
        op.execute(
            endpoints_table.update()
            .where(endpoints_table.c.id == id_)
            .values(endpoints=endpoints)
        )
