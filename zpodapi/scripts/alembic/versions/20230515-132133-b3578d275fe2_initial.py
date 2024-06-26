"""initial

Revision ID: b3578d275fe2
Revises:
Create Date: 2023-05-15 13:21:32.129204

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "b3578d275fe2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "endpoints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("endpoints", sa.JSON(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_endpoints_name"), "endpoints", ["name"], unique=True)
    op.create_table(
        "libraries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("git_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("last_modified_date", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_libraries_name"), "libraries", ["name"], unique=True)
    op.create_table(
        "permission_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("value", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_settings_name"), "settings", ["name"], unique=True)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("api_token", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("ssh_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("last_connection_date", sa.DateTime(), nullable=True),
        sa.Column("superadmin", sa.Boolean(), nullable=False),
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("last_modified_date", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_api_token"), "users", ["api_token"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_table(
        "components",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("component_uid", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("component_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "component_version", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column(
            "component_description", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("library_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("filename", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("jsonfile", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("last_modified_date", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["library_name"],
            ["libraries.name"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("component_uid"),
    )
    op.create_index(
        op.f("ix_components_jsonfile"), "components", ["jsonfile"], unique=True
    )
    op.create_table(
        "instances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("domain", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("profile", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("endpoint_id", sa.Integer(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("last_modified_date", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["endpoint_id"],
            ["endpoints.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_instances_name"), "instances", ["name"], unique=False)
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
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("component_id", sa.Integer(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("last_modified_date", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["component_id"],
            ["components.id"],
        ),
        sa.ForeignKeyConstraint(
            ["instance_id"],
            ["instances.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "instance_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
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
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("instance_permission_user_link")
    op.drop_table("instance_permission_group_link")
    op.drop_table("instance_permissions")
    op.drop_table("instance_networks")
    op.drop_table("instance_features")
    op.drop_table("instance_components")
    op.drop_table("permission_group_user_link")
    op.drop_index(op.f("ix_instances_name"), table_name="instances")
    op.drop_table("instances")
    op.drop_index(op.f("ix_components_jsonfile"), table_name="components")
    op.drop_table("components")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_api_token"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_settings_name"), table_name="settings")
    op.drop_table("settings")
    op.drop_table("permission_groups")
    op.drop_index(op.f("ix_libraries_name"), table_name="libraries")
    op.drop_table("libraries")
    op.drop_index(op.f("ix_endpoints_name"), table_name="endpoints")
    op.drop_table("endpoints")
    # ### end Alembic commands ###
