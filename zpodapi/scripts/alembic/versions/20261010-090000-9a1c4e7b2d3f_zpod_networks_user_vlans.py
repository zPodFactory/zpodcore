"""zpod_networks: name, vlan_id, gateway, kind, masquerade, routing

Revision ID: 9a1c4e7b2d3f
Revises: fdc3605928ad
Create Date: 2026-10-10 09:00:00.000000

User-added VLAN networks on a zPod's zcore (the zcore self-service feature).
The four rows every deploy creates are backfilled from their CIDR: the VLAN id
is the last octet of the network address (0, 64, 128, 192), the gateway is the
first host, all four are routed by the T1 (GLOBAL) and never masqueraded.

Before the (zpod_id, vlan_id) unique constraint, extra deploy rows are removed:
a deploy flow run that ran again (0.8 and earlier) allocated another /24 and
appended 4 more rows each time, so some zPods own 8 or 12 rows that fold into
the same 4 VLAN ids. Each zPod keeps its first /24 (lowest row ids): before
0.9.0 zpodcore read a zPod's network from its first row (zpod.networks[0]), so
its segment, DNS and component IPs are all there and the later /24s were never
used.
"""

import ipaddress
import logging
from collections import defaultdict

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9a1c4e7b2d3f"
down_revision = "fdc3605928ad"
branch_labels = None
depends_on = None

log = logging.getLogger("alembic.runtime.migration")


def _vlan_id(network: ipaddress.IPv4Network) -> int:
    return int(str(network.network_address).split(".")[-1])


def _slash24(network: ipaddress.IPv4Network) -> ipaddress.IPv4Network:
    return network.supernet(new_prefix=24) if network.prefixlen > 24 else network


def remove_duplicate_deploy_networks(conn) -> int:
    """Keep each zPod's first /24, delete its other deploy rows; answer how many."""
    rows = conn.execute(
        sa.text(
            "SELECT n.id, n.zpod_id, n.cidr, z.name, z.status "
            "FROM zpod_networks n JOIN zpods z ON z.id = n.zpod_id "
            "ORDER BY n.zpod_id, n.id"
        )
    ).fetchall()
    by_zpod = defaultdict(list)
    for row in rows:
        by_zpod[row.zpod_id].append(row)

    extra_ids: list[int] = []
    for zpod_id, zpod_rows in by_zpod.items():
        networks = [ipaddress.ip_network(r.cidr, strict=False) for r in zpod_rows]
        vlans = [_vlan_id(n) for n in networks]
        if len(set(vlans)) == len(vlans):
            continue
        keep = _slash24(networks[0])
        kept_vlans: set[int] = set()
        for row, network, vlan in zip(zpod_rows, networks, vlans, strict=True):
            if _slash24(network) == keep and vlan not in kept_vlans:
                kept_vlans.add(vlan)
            else:
                extra_ids.append(row.id)
        log.info(
            "zPod %s (id %s, %s): keeping %s, removing %s duplicate rows",
            zpod_rows[0].name,
            zpod_id,
            zpod_rows[0].status,
            keep,
            len(zpod_rows) - len(kept_vlans),
        )

    if extra_ids:
        conn.execute(
            sa.text("DELETE FROM zpod_networks WHERE id IN :ids").bindparams(
                sa.bindparam("ids", expanding=True)
            ),
            {"ids": extra_ids},
        )
        log.info("Removed %s duplicate deploy network rows", len(extra_ids))
    return len(extra_ids)


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

    conn = op.get_bind()
    remove_duplicate_deploy_networks(conn)

    # Backfill the deploy-time rows from their CIDR (deterministic: the last
    # octet of a /26 inside the zPod's /24 is its VLAN id).
    rows = conn.execute(sa.text("SELECT id, cidr FROM zpod_networks")).fetchall()
    for row_id, cidr in rows:
        network = ipaddress.ip_network(cidr, strict=False)
        vlan_id = _vlan_id(network)
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
    # User VLANs have no place in the 0.8 schema. On a live zPod they also hold
    # NSX routes and zcore interfaces that only removing them with zcli cleans
    # up, so the downgrade refuses until that's done. A DELETED zPod's T1 and
    # zcore are gone: its rows are dropped.
    conn = op.get_bind()
    live = conn.execute(
        sa.text(
            "SELECT z.name, n.name FROM zpod_networks n JOIN zpods z ON z.id = n.zpod_id "
            "WHERE n.kind = 'user' AND z.status <> 'DELETED' ORDER BY z.name, n.name"
        )
    ).fetchall()
    if live:
        raise RuntimeError(
            "User VLANs exist on live zPods, and 0.8 cannot hold them. Remove them first:\n"
            + "\n".join(f"  zcli zpod network remove {z} {n}" for z, n in live)
        )
    conn.execute(sa.text("DELETE FROM zpod_networks WHERE kind = 'user'"))
    op.drop_constraint(
        "zpod_networks_zpod_id_vlan_id_key", "zpod_networks", type_="unique"
    )
    for column in ("routing", "masquerade", "kind", "gateway", "vlan_id", "name"):
        op.drop_column("zpod_networks", column)
