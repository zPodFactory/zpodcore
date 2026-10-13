"""zpod_networks: name, vlan_id, gateway, kind, masquerade, routing

Revision ID: 9a1c4e7b2d3f
Revises: fdc3605928ad
Create Date: 2026-10-10 09:00:00.000000

User-added VLAN networks on a zPod's zcore (the zcore self-service feature).
The four rows every deploy creates are backfilled from their CIDR: the VLAN id
is the last octet of the network address (0, 64, 128, 192), the gateway is the
first host, all four are routed by the T1 (GLOBAL) and never masqueraded.
"""

import ipaddress

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9a1c4e7b2d3f"
down_revision = "fdc3605928ad"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "zpod_networks",
        sa.Column("name", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "zpod_networks",
        sa.Column("vlan_id", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "zpod_networks",
        sa.Column("gateway", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "zpod_networks",
        sa.Column("kind", sa.String(), nullable=False, server_default="zpod"),
    )
    op.add_column(
        "zpod_networks",
        sa.Column(
            "masquerade", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "zpod_networks",
        sa.Column("routing", sa.String(), nullable=False, server_default="GLOBAL"),
    )

    # Backfill the deploy-time rows from their CIDR (deterministic: the last
    # octet of a /26 inside the zPod's /24 is its VLAN id).
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, cidr FROM zpod_networks")).fetchall()
    for row_id, cidr in rows:
        network = ipaddress.ip_network(cidr, strict=False)
        vlan_id = int(str(network.network_address).split(".")[-1])
        conn.execute(
            sa.text(
                "UPDATE zpod_networks SET name=:name, vlan_id=:vlan_id, "
                "gateway=:gateway, kind='zpod', masquerade=false, routing='GLOBAL' "
                "WHERE id=:id"
            ),
            {
                "id": row_id,
                "name": "mgmt" if vlan_id == 0 else f"vlan{vlan_id}",
                "vlan_id": vlan_id,
                "gateway": f"{network.network_address + 1}/{network.prefixlen}",
            },
        )

    op.create_unique_constraint(
        "zpod_networks_zpod_id_vlan_id_key", "zpod_networks", ["zpod_id", "vlan_id"]
    )


def downgrade():
    op.drop_constraint(
        "zpod_networks_zpod_id_vlan_id_key", "zpod_networks", type_="unique"
    )
    for column in ("routing", "masquerade", "kind", "gateway", "vlan_id", "name"):
        op.drop_column("zpod_networks", column)
