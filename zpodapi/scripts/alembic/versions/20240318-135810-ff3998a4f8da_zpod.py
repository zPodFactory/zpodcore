"""zpod

Revision ID: ff3998a4f8da
Revises: 05a7cece1c44
Create Date: 2024-03-18 13:58:10.804665

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ff3998a4f8da"
down_revision = "05a7cece1c44"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("instance_features", "zpod_features")
    op.execute("ALTER SEQUENCE instance_features_id_seq RENAME TO zpod_features_id_seq")
    op.execute("ALTER INDEX instance_features_pkey RENAME TO zpod_features_pkey")
    op.execute(
        "ALTER TABLE zpod_features "
        "RENAME CONSTRAINT instance_features_instance_id_fkey "
        "TO zpod_features_zpod_id_fkey"
    )
    op.alter_column(
        "zpod_features",
        "instance_id",
        new_column_name="zpod_id",
        existing_type=sa.Integer,
    )

    op.rename_table("instance_networks", "zpod_networks")
    op.execute("ALTER SEQUENCE instance_networks_id_seq RENAME TO zpod_networks_id_seq")
    op.execute("ALTER INDEX instance_networks_pkey RENAME TO zpod_networks_pkey")
    op.execute(
        "ALTER TABLE zpod_networks "
        "RENAME CONSTRAINT instance_networks_instance_id_fkey "
        "TO zpod_networks_zpod_id_fkey"
    )
    op.alter_column(
        "zpod_networks",
        "instance_id",
        new_column_name="zpod_id",
        existing_type=sa.Integer,
    )

    op.rename_table("instance_components", "zpod_components")
    op.execute(
        "ALTER SEQUENCE instance_components_id_seq RENAME TO zpod_components_id_seq"
    )
    op.execute("ALTER INDEX instance_components_pkey RENAME TO zpod_components_pkey")
    op.execute(
        "ALTER TABLE zpod_components "
        "RENAME CONSTRAINT instance_components_instance_id_fkey "
        "TO zpod_components_zpod_id_fkey"
    )
    op.execute(
        "ALTER TABLE zpod_components "
        "RENAME CONSTRAINT instance_components_component_id_fkey "
        "TO zpod_components_component_id_fkey"
    )
    op.alter_column(
        "zpod_components",
        "instance_id",
        new_column_name="zpod_id",
        existing_type=sa.Integer,
    )

    op.rename_table("instance_permission_group_link", "zpod_permission_group_link")
    op.execute(
        "ALTER INDEX instance_permission_group_link_pkey "
        "RENAME TO zpod_permission_group_link_pkey"
    )
    op.execute(
        "ALTER TABLE zpod_permission_group_link "
        "RENAME CONSTRAINT instance_permission_group_link_permission_group_id_fkey "
        "TO zpod_permission_group_link_permission_group_id_fkey"
    )
    op.execute(
        "ALTER TABLE zpod_permission_group_link "
        "RENAME CONSTRAINT instance_permission_group_link_instance_permission_id_fkey "
        "TO zpod_permission_group_link_zpod_permission_id_fkey"
    )
    op.alter_column(
        "zpod_permission_group_link",
        "instance_permission_id",
        new_column_name="zpod_permission_id",
        existing_type=sa.Integer,
    )

    op.rename_table("instance_permission_user_link", "zpod_permission_user_link")
    op.execute(
        "ALTER INDEX instance_permission_user_link_pkey "
        "RENAME TO zpod_permission_user_link_pkey"
    )
    op.execute(
        "ALTER TABLE zpod_permission_user_link "
        "RENAME CONSTRAINT instance_permission_user_link_user_id_fkey "
        "TO zpod_permission_user_link_user_id_fkey"
    )
    op.execute(
        "ALTER TABLE zpod_permission_user_link "
        "RENAME CONSTRAINT instance_permission_user_link_instance_permission_id_fkey "
        "TO zpod_permission_user_link_zpod_permission_id_fkey"
    )
    op.alter_column(
        "zpod_permission_user_link",
        "instance_permission_id",
        new_column_name="zpod_permission_id",
        existing_type=sa.Integer,
    )

    op.rename_table("instance_permissions", "zpod_permissions")
    op.execute(
        "ALTER SEQUENCE instance_permissions_id_seq RENAME TO zpod_permissions_id_seq"
    )
    op.execute("ALTER INDEX instance_permissions_pkey RENAME TO zpod_permissions_pkey")
    op.execute(
        "ALTER TABLE zpod_permissions "
        "RENAME CONSTRAINT instance_permissions_instance_id_fkey "
        "TO zpod_permissions_zpod_id_fkey"
    )
    op.alter_column(
        "zpod_permissions",
        "instance_id",
        new_column_name="zpod_id",
        existing_type=sa.Integer,
    )

    op.rename_table("instances", "zpods")
    op.execute("ALTER SEQUENCE instances_id_seq RENAME TO zpods_id_seq")
    op.execute("ALTER INDEX instances_pkey RENAME TO zpods_pkey")
    op.execute("ALTER INDEX ix_instances_name RENAME TO ix_zpods_name")
    op.execute(
        "ALTER TABLE zpods "
        "RENAME CONSTRAINT instances_endpoint_id_fkey "
        "TO zpods_endpoint_id_fkey"
    )
    op.execute(
        "UPDATE settings "
        "SET name='zpodfactory_default_domain' "
        "WHERE name='zpodfactory_instances_domain'"
    )


def downgrade():
    op.rename_table("zpod_features", "instance_features")
    op.execute("ALTER SEQUENCE zpod_features_id_seq RENAME TO instance_features_id_seq")
    op.execute("ALTER INDEX zpod_features_pkey RENAME TO instance_features_pkey")
    op.execute(
        "ALTER TABLE instance_features "
        "RENAME CONSTRAINT zpod_features_zpod_id_fkey "
        "TO instance_features_instance_id_fkey"
    )
    op.alter_column(
        "instance_features",
        "zpod_id",
        new_column_name="instance_id",
        existing_type=sa.Integer,
    )

    op.rename_table("zpod_networks", "instance_networks")
    op.execute("ALTER SEQUENCE zpod_networks_id_seq RENAME TO instance_networks_id_seq")
    op.execute("ALTER INDEX zpod_networks_pkey RENAME TO instance_networks_pkey")
    op.execute(
        "ALTER TABLE instance_networks "
        "RENAME CONSTRAINT zpod_networks_zpod_id_fkey "
        "TO instance_networks_instance_id_fkey"
    )
    op.alter_column(
        "instance_networks",
        "zpod_id",
        new_column_name="instance_id",
        existing_type=sa.Integer,
    )

    op.rename_table("zpod_components", "instance_components")
    op.execute(
        "ALTER SEQUENCE zpod_components_id_seq RENAME TO instance_components_id_seq"
    )
    op.execute("ALTER INDEX zpod_components_pkey RENAME TO instance_components_pkey")
    op.execute(
        "ALTER TABLE instance_components "
        "RENAME CONSTRAINT zpod_components_zpod_id_fkey "
        "TO instance_components_instance_id_fkey"
    )
    op.execute(
        "ALTER TABLE instance_components "
        "RENAME CONSTRAINT zpod_components_component_id_fkey "
        "TO instance_components_component_id_fkey"
    )
    op.alter_column(
        "instance_components",
        "zpod_id",
        new_column_name="instance_id",
        existing_type=sa.Integer,
    )

    op.rename_table("zpod_permission_group_link", "instance_permission_group_link")
    op.execute(
        "ALTER INDEX zpod_permission_group_link_pkey "
        "RENAME TO instance_permission_group_link_pkey"
    )
    op.execute(
        "ALTER TABLE instance_permission_group_link "
        "RENAME CONSTRAINT zpod_permission_group_link_permission_group_id_fkey "
        "TO instance_permission_group_link_permission_group_id_fkey"
    )
    op.execute(
        "ALTER TABLE instance_permission_group_link "
        "RENAME CONSTRAINT zpod_permission_group_link_zpod_permission_id_fkey "
        "TO instance_permission_group_link_instance_permission_id_fkey"
    )
    op.alter_column(
        "instance_permission_group_link",
        "zpod_permission_id",
        new_column_name="instance_permission_id",
        existing_type=sa.Integer,
    )

    op.rename_table("zpod_permission_user_link", "instance_permission_user_link")
    op.execute(
        "ALTER INDEX zpod_permission_user_link_pkey "
        "RENAME TO instance_permission_user_link_pkey"
    )
    op.execute(
        "ALTER TABLE instance_permission_user_link "
        "RENAME CONSTRAINT zpod_permission_user_link_user_id_fkey "
        "TO instance_permission_user_link_user_id_fkey"
    )
    op.execute(
        "ALTER TABLE instance_permission_user_link "
        "RENAME CONSTRAINT zpod_permission_user_link_zpod_permission_id_fkey "
        "TO instance_permission_user_link_instance_permission_id_fkey"
    )
    op.alter_column(
        "instance_permission_user_link",
        "zpod_permission_id",
        new_column_name="instance_permission_id",
        existing_type=sa.Integer,
    )

    op.rename_table("zpod_permissions", "instance_permissions")
    op.execute(
        "ALTER SEQUENCE zpod_permissions_id_seq RENAME TO instance_permissions_id_seq"
    )
    op.execute("ALTER INDEX zpod_permissions_pkey RENAME TO instance_permissions_pkey")
    op.execute(
        "ALTER TABLE instance_permissions "
        "RENAME CONSTRAINT zpod_permissions_zpod_id_fkey "
        "TO instance_permissions_instance_id_fkey"
    )
    op.alter_column(
        "instance_permissions",
        "zpod_id",
        new_column_name="instance_id",
        existing_type=sa.Integer,
    )

    op.rename_table("zpods", "instances")
    op.execute("ALTER SEQUENCE zpods_id_seq RENAME TO instances_id_seq")
    op.execute("ALTER INDEX zpods_pkey RENAME TO instances_pkey")
    op.execute("ALTER INDEX ix_zpods_name RENAME TO ix_instances_name")
    op.execute(
        "ALTER TABLE instances "
        "RENAME CONSTRAINT zpods_endpoint_id_fkey "
        "TO instances_endpoint_id_fkey"
    )

    op.execute(
        "UPDATE settings "
        "SET name='zpodfactory_instances_domain' "
        "WHERE name='zpodfactory_default_domain'"
    )
