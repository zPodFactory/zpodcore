"""Add Settings and fixes to components

Revision ID: 5953ffc1f677
Revises: 15e9fd1eef5f
Create Date: 2023-04-28 13:25:56.440530

"""
import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision = "5953ffc1f677"
down_revision = "15e9fd1eef5f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("value", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_settings_name"), "settings", ["name"], unique=True)
    op.add_column(
        "components",
        sa.Column("jsonfile", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    )
    op.drop_index("ix_components_filename", table_name="components")
    op.create_index(
        op.f("ix_components_jsonfile"), "components", ["jsonfile"], unique=True
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_components_jsonfile"), table_name="components")
    op.create_index("ix_components_filename", "components", ["filename"], unique=False)
    op.drop_column("components", "jsonfile")
    op.drop_index(op.f("ix_settings_name"), table_name="settings")
    op.drop_table("settings")
    # ### end Alembic commands ###