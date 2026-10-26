"""zpod_disks: virtual disks of a zPod's zcore VM

Revision ID: 4d2e8b1c9f6a
Revises: 9a1c4e7b2d3f
Create Date: 2026-10-23 16:00:00.000000

The zcore storage capabilities: one row per virtual disk of the zcore VM, with
the vSphere handles (device key, SCSI unit, disk UUID). No backfill: the rows of
an existing zPod's two deploy disks are written by the first disk change on it,
which reads them from vCenter.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4d2e8b1c9f6a"
down_revision = "9a1c4e7b2d3f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "zpod_disks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zpod_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("size_gb", sa.Integer(), nullable=False),
        sa.Column("scsi_unit", sa.Integer(), nullable=True),
        sa.Column("vm_disk_key", sa.Integer(), nullable=True),
        sa.Column("disk_uuid", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["zpod_id"], ["zpods.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "zpod_id", "scsi_unit", name="zpod_disks_zpod_id_scsi_unit_key"
        ),
        sa.UniqueConstraint(
            "zpod_id", "disk_uuid", name="zpod_disks_zpod_id_disk_uuid_key"
        ),
    )


def downgrade():
    op.drop_table("zpod_disks")
