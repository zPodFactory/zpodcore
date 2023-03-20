"""instance

Revision ID: 377b99272e35
Revises: 1c10dbfe6448
Create Date: 2023-03-15 19:51:53.691320

"""
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "377b99272e35"
down_revision = "1c10dbfe6448"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "endpoints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "permission_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "instances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("domain", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("profile", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("last_modified_date", sa.DateTime(), nullable=False),
        sa.Column("endpoint_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["endpoint_id"],
            ["endpoints.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_instances_name"), "instances", ["name"], unique=True)
    op.create_table(
        "permission_group_user_link",
        sa.Column("permission_group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_group_id"],
            ["permission_groups.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("permission_group_id", "user_id"),
    )
    op.create_table(
        "instance_components",
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("component_uid", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["component_uid"],
            ["components.component_uid"],
        ),
        sa.ForeignKeyConstraint(
            ["instance_id"],
            ["instances.id"],
        ),
        sa.PrimaryKeyConstraint("instance_id", "component_uid"),
    )
    op.create_table(
        "instance_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["instance_id"],
            ["instances.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "instance_networks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("cidr", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(
            ["instance_id"],
            ["instances.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "instance_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("permission", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(
            ["instance_id"],
            ["instances.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "instance_permission_group_link",
        sa.Column("instance_permission_id", sa.Integer(), nullable=False),
        sa.Column("permission_group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["instance_permission_id"],
            ["instance_permissions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["permission_group_id"],
            ["permission_groups.id"],
        ),
        sa.PrimaryKeyConstraint("instance_permission_id", "permission_group_id"),
    )
    op.create_table(
        "instance_permission_user_link",
        sa.Column("instance_permission_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["instance_permission_id"],
            ["instance_permissions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("instance_permission_id", "user_id"),
    )
    op.drop_column("users", "last_connection_date")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "users",
        sa.Column(
            "last_connection_date",
            postgresql.TIMESTAMP(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.drop_table("instance_permission_user_link")
    op.drop_table("instance_permission_group_link")
    op.drop_table("instance_permissions")
    op.drop_table("instance_networks")
    op.drop_table("instance_features")
    op.drop_table("instance_components")
    op.drop_table("permission_group_user_link")
    op.drop_index(op.f("ix_instances_name"), table_name="instances")
    op.drop_table("instances")
    op.drop_table("permission_groups")
    op.drop_table("endpoints")
    # ### end Alembic commands ###