"""add unique constraint to zpod features

Revision ID: fdc3605928ad
Revises: 73910346a24f
Create Date: 2025-03-23 15:34:32.780272

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fdc3605928ad"
down_revision = "73910346a24f"
branch_labels = None
depends_on = None


def upgrade():
    # Add features column to zpods table
    op.add_column(
        "zpods",
        sa.Column("features", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb"))
    )

    # Drop zpod_features table
    op.drop_table("zpod_features")


def downgrade():
    # Recreate zpod_features table
    op.create_table(
        "zpod_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zpod_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["zpod_id"], ["zpods.id"], name="zpod_features_zpod_id_fkey"),
        sa.PrimaryKeyConstraint("id", name="zpod_features_pkey")
    )

    # Drop features column from zpods
    op.drop_column("zpods", "features")
