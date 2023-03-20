"""init-db

Revision ID: ed3586602581
Revises: 
Create Date: 2023-03-20 18:26:06.273769

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "ed3586602581"
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
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("last_modified_date", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("git_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_libraries_name"), "libraries", ["name"], unique=True)
    op.create_table(
        "users",
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("last_modified_date", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("api_token", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("ssh_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("last_connection_date", sa.DateTime(), nullable=True),
        sa.Column("superadmin", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_api_token"), "users", ["api_token"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_table(
        "components",
        sa.Column("creation_date", sa.DateTime(), nullable=False),
        sa.Column("last_modified_date", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("component_uid", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("component_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "component_version", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("library_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("filename", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(
            ["library_name"],
            ["libraries.name"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("component_uid"),
    )
    op.create_index(
        op.f("ix_components_filename"), "components", ["filename"], unique=True
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_components_filename"), table_name="components")
    op.drop_table("components")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_api_token"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_libraries_name"), table_name="libraries")
    op.drop_table("libraries")
    op.drop_index(op.f("ix_endpoints_name"), table_name="endpoints")
    op.drop_table("endpoints")
    # ### end Alembic commands ###