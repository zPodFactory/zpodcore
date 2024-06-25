from functools import cache

from zpodsdk import Client


class ZpodClient:
    def __init__(
        self,
        base_url,
        headers,
        raise_on_unexpected_status=True,
    ):
        self._client = Client(
            base_url=base_url,
            headers=headers,
            raise_on_unexpected_status=raise_on_unexpected_status,
        )

    @property
    @cache  # noqa: B019
    def components_disable(self):
        from zpodsdk.api.components import components_disable

        return components_disable.ComponentsDisable(self._client)

    @property
    @cache  # noqa: B019
    def components_enable(self):
        from zpodsdk.api.components import components_enable

        return components_enable.ComponentsEnable(self._client)

    @property
    @cache  # noqa: B019
    def components_get(self):
        from zpodsdk.api.components import components_get

        return components_get.ComponentsGet(self._client)

    @property
    @cache  # noqa: B019
    def components_get_all(self):
        from zpodsdk.api.components import components_get_all

        return components_get_all.ComponentsGetAll(self._client)

    @property
    @cache  # noqa: B019
    def components_upload(self):
        from zpodsdk.api.components import components_upload

        return components_upload.ComponentsUpload(self._client)

    @property
    @cache  # noqa: B019
    def components_upload_filesize(self):
        from zpodsdk.api.components import components_upload_filesize

        return components_upload_filesize.ComponentsUploadFilesize(self._client)

    @property
    @cache  # noqa: B019
    def endpoints_create(self):
        from zpodsdk.api.endpoints import endpoints_create

        return endpoints_create.EndpointsCreate(self._client)

    @property
    @cache  # noqa: B019
    def endpoints_delete(self):
        from zpodsdk.api.endpoints import endpoints_delete

        return endpoints_delete.EndpointsDelete(self._client)

    @property
    @cache  # noqa: B019
    def endpoints_enet_create(self):
        from zpodsdk.api.endpoints import endpoints_enet_create

        return endpoints_enet_create.EndpointsEnetCreate(self._client)

    @property
    @cache  # noqa: B019
    def endpoints_enet_delete(self):
        from zpodsdk.api.endpoints import endpoints_enet_delete

        return endpoints_enet_delete.EndpointsEnetDelete(self._client)

    @property
    @cache  # noqa: B019
    def endpoints_enet_get(self):
        from zpodsdk.api.endpoints import endpoints_enet_get

        return endpoints_enet_get.EndpointsEnetGet(self._client)

    @property
    @cache  # noqa: B019
    def endpoints_enet_get_all(self):
        from zpodsdk.api.endpoints import endpoints_enet_get_all

        return endpoints_enet_get_all.EndpointsEnetGetAll(self._client)

    @property
    @cache  # noqa: B019
    def endpoints_get(self):
        from zpodsdk.api.endpoints import endpoints_get

        return endpoints_get.EndpointsGet(self._client)

    @property
    @cache  # noqa: B019
    def endpoints_get_all(self):
        from zpodsdk.api.endpoints import endpoints_get_all

        return endpoints_get_all.EndpointsGetAll(self._client)

    @property
    @cache  # noqa: B019
    def endpoints_permissions_get_all(self):
        from zpodsdk.api.endpoints import endpoints_permissions_get_all

        return endpoints_permissions_get_all.EndpointsPermissionsGetAll(self._client)

    @property
    @cache  # noqa: B019
    def endpoints_permissions_groups_add(self):
        from zpodsdk.api.endpoints import endpoints_permissions_groups_add

        return endpoints_permissions_groups_add.EndpointsPermissionsGroupsAdd(
            self._client
        )

    @property
    @cache  # noqa: B019
    def endpoints_permissions_groups_remove(self):
        from zpodsdk.api.endpoints import endpoints_permissions_groups_remove

        return endpoints_permissions_groups_remove.EndpointsPermissionsGroupsRemove(
            self._client
        )

    @property
    @cache  # noqa: B019
    def endpoints_permissions_users_add(self):
        from zpodsdk.api.endpoints import endpoints_permissions_users_add

        return endpoints_permissions_users_add.EndpointsPermissionsUsersAdd(
            self._client
        )

    @property
    @cache  # noqa: B019
    def endpoints_permissions_users_remove(self):
        from zpodsdk.api.endpoints import endpoints_permissions_users_remove

        return endpoints_permissions_users_remove.EndpointsPermissionsUsersRemove(
            self._client
        )

    @property
    @cache  # noqa: B019
    def endpoints_update(self):
        from zpodsdk.api.endpoints import endpoints_update

        return endpoints_update.EndpointsUpdate(self._client)

    @property
    @cache  # noqa: B019
    def endpoints_verify(self):
        from zpodsdk.api.endpoints import endpoints_verify

        return endpoints_verify.EndpointsVerify(self._client)

    @property
    @cache  # noqa: B019
    def libraries_create(self):
        from zpodsdk.api.libraries import libraries_create

        return libraries_create.LibrariesCreate(self._client)

    @property
    @cache  # noqa: B019
    def libraries_delete(self):
        from zpodsdk.api.libraries import libraries_delete

        return libraries_delete.LibrariesDelete(self._client)

    @property
    @cache  # noqa: B019
    def libraries_get(self):
        from zpodsdk.api.libraries import libraries_get

        return libraries_get.LibrariesGet(self._client)

    @property
    @cache  # noqa: B019
    def libraries_get_all(self):
        from zpodsdk.api.libraries import libraries_get_all

        return libraries_get_all.LibrariesGetAll(self._client)

    @property
    @cache  # noqa: B019
    def libraries_resync(self):
        from zpodsdk.api.libraries import libraries_resync

        return libraries_resync.LibrariesResync(self._client)

    @property
    @cache  # noqa: B019
    def libraries_update(self):
        from zpodsdk.api.libraries import libraries_update

        return libraries_update.LibrariesUpdate(self._client)

    @property
    @cache  # noqa: B019
    def permission_groups_create(self):
        from zpodsdk.api.permission_groups import permission_groups_create

        return permission_groups_create.PermissionGroupsCreate(self._client)

    @property
    @cache  # noqa: B019
    def permission_groups_delete(self):
        from zpodsdk.api.permission_groups import permission_groups_delete

        return permission_groups_delete.PermissionGroupsDelete(self._client)

    @property
    @cache  # noqa: B019
    def permission_groups_get(self):
        from zpodsdk.api.permission_groups import permission_groups_get

        return permission_groups_get.PermissionGroupsGet(self._client)

    @property
    @cache  # noqa: B019
    def permission_groups_get_all(self):
        from zpodsdk.api.permission_groups import permission_groups_get_all

        return permission_groups_get_all.PermissionGroupsGetAll(self._client)

    @property
    @cache  # noqa: B019
    def permission_groups_update(self):
        from zpodsdk.api.permission_groups import permission_groups_update

        return permission_groups_update.PermissionGroupsUpdate(self._client)

    @property
    @cache  # noqa: B019
    def permission_groups_users_add(self):
        from zpodsdk.api.permission_groups import permission_groups_users_add

        return permission_groups_users_add.PermissionGroupsUsersAdd(self._client)

    @property
    @cache  # noqa: B019
    def permission_groups_users_delete(self):
        from zpodsdk.api.permission_groups import permission_groups_users_delete

        return permission_groups_users_delete.PermissionGroupsUsersDelete(self._client)

    @property
    @cache  # noqa: B019
    def permission_groups_users_get_all(self):
        from zpodsdk.api.permission_groups import permission_groups_users_get_all

        return permission_groups_users_get_all.PermissionGroupsUsersGetAll(self._client)

    @property
    @cache  # noqa: B019
    def profiles_create(self):
        from zpodsdk.api.profiles import profiles_create

        return profiles_create.ProfilesCreate(self._client)

    @property
    @cache  # noqa: B019
    def profiles_delete(self):
        from zpodsdk.api.profiles import profiles_delete

        return profiles_delete.ProfilesDelete(self._client)

    @property
    @cache  # noqa: B019
    def profiles_get(self):
        from zpodsdk.api.profiles import profiles_get

        return profiles_get.ProfilesGet(self._client)

    @property
    @cache  # noqa: B019
    def profiles_get_all(self):
        from zpodsdk.api.profiles import profiles_get_all

        return profiles_get_all.ProfilesGetAll(self._client)

    @property
    @cache  # noqa: B019
    def profiles_update(self):
        from zpodsdk.api.profiles import profiles_update

        return profiles_update.ProfilesUpdate(self._client)

    @property
    @cache  # noqa: B019
    def root_root(self):
        from zpodsdk.api.root import root_root

        return root_root.RootRoot(self._client)

    @property
    @cache  # noqa: B019
    def settings_create(self):
        from zpodsdk.api.settings import settings_create

        return settings_create.SettingsCreate(self._client)

    @property
    @cache  # noqa: B019
    def settings_delete(self):
        from zpodsdk.api.settings import settings_delete

        return settings_delete.SettingsDelete(self._client)

    @property
    @cache  # noqa: B019
    def settings_get(self):
        from zpodsdk.api.settings import settings_get

        return settings_get.SettingsGet(self._client)

    @property
    @cache  # noqa: B019
    def settings_get_all(self):
        from zpodsdk.api.settings import settings_get_all

        return settings_get_all.SettingsGetAll(self._client)

    @property
    @cache  # noqa: B019
    def settings_update(self):
        from zpodsdk.api.settings import settings_update

        return settings_update.SettingsUpdate(self._client)

    @property
    @cache  # noqa: B019
    def users_create(self):
        from zpodsdk.api.users import users_create

        return users_create.UsersCreate(self._client)

    @property
    @cache  # noqa: B019
    def users_disable(self):
        from zpodsdk.api.users import users_disable

        return users_disable.UsersDisable(self._client)

    @property
    @cache  # noqa: B019
    def users_enable(self):
        from zpodsdk.api.users import users_enable

        return users_enable.UsersEnable(self._client)

    @property
    @cache  # noqa: B019
    def users_get(self):
        from zpodsdk.api.users import users_get

        return users_get.UsersGet(self._client)

    @property
    @cache  # noqa: B019
    def users_get_all(self):
        from zpodsdk.api.users import users_get_all

        return users_get_all.UsersGetAll(self._client)

    @property
    @cache  # noqa: B019
    def users_get_me(self):
        from zpodsdk.api.users import users_get_me

        return users_get_me.UsersGetMe(self._client)

    @property
    @cache  # noqa: B019
    def users_reset_api_token(self):
        from zpodsdk.api.users import users_reset_api_token

        return users_reset_api_token.UsersResetApiToken(self._client)

    @property
    @cache  # noqa: B019
    def users_update(self):
        from zpodsdk.api.users import users_update

        return users_update.UsersUpdate(self._client)

    @property
    @cache  # noqa: B019
    def zpods_components_add(self):
        from zpodsdk.api.zpods import zpods_components_add

        return zpods_components_add.ZpodsComponentsAdd(self._client)

    @property
    @cache  # noqa: B019
    def zpods_components_get(self):
        from zpodsdk.api.zpods import zpods_components_get

        return zpods_components_get.ZpodsComponentsGet(self._client)

    @property
    @cache  # noqa: B019
    def zpods_components_get_all(self):
        from zpodsdk.api.zpods import zpods_components_get_all

        return zpods_components_get_all.ZpodsComponentsGetAll(self._client)

    @property
    @cache  # noqa: B019
    def zpods_components_remove(self):
        from zpodsdk.api.zpods import zpods_components_remove

        return zpods_components_remove.ZpodsComponentsRemove(self._client)

    @property
    @cache  # noqa: B019
    def zpods_create(self):
        from zpodsdk.api.zpods import zpods_create

        return zpods_create.ZpodsCreate(self._client)

    @property
    @cache  # noqa: B019
    def zpods_delete(self):
        from zpodsdk.api.zpods import zpods_delete

        return zpods_delete.ZpodsDelete(self._client)

    @property
    @cache  # noqa: B019
    def zpods_dns_add(self):
        from zpodsdk.api.zpods import zpods_dns_add

        return zpods_dns_add.ZpodsDnsAdd(self._client)

    @property
    @cache  # noqa: B019
    def zpods_dns_get(self):
        from zpodsdk.api.zpods import zpods_dns_get

        return zpods_dns_get.ZpodsDnsGet(self._client)

    @property
    @cache  # noqa: B019
    def zpods_dns_get_all(self):
        from zpodsdk.api.zpods import zpods_dns_get_all

        return zpods_dns_get_all.ZpodsDnsGetAll(self._client)

    @property
    @cache  # noqa: B019
    def zpods_dns_remove(self):
        from zpodsdk.api.zpods import zpods_dns_remove

        return zpods_dns_remove.ZpodsDnsRemove(self._client)

    @property
    @cache  # noqa: B019
    def zpods_dns_update(self):
        from zpodsdk.api.zpods import zpods_dns_update

        return zpods_dns_update.ZpodsDnsUpdate(self._client)

    @property
    @cache  # noqa: B019
    def zpods_features_get_all(self):
        from zpodsdk.api.zpods import zpods_features_get_all

        return zpods_features_get_all.ZpodsFeaturesGetAll(self._client)

    @property
    @cache  # noqa: B019
    def zpods_get(self):
        from zpodsdk.api.zpods import zpods_get

        return zpods_get.ZpodsGet(self._client)

    @property
    @cache  # noqa: B019
    def zpods_get_all(self):
        from zpodsdk.api.zpods import zpods_get_all

        return zpods_get_all.ZpodsGetAll(self._client)

    @property
    @cache  # noqa: B019
    def zpods_networks_get_all(self):
        from zpodsdk.api.zpods import zpods_networks_get_all

        return zpods_networks_get_all.ZpodsNetworksGetAll(self._client)

    @property
    @cache  # noqa: B019
    def zpods_permissions_get_all(self):
        from zpodsdk.api.zpods import zpods_permissions_get_all

        return zpods_permissions_get_all.ZpodsPermissionsGetAll(self._client)

    @property
    @cache  # noqa: B019
    def zpods_permissions_groups_add(self):
        from zpodsdk.api.zpods import zpods_permissions_groups_add

        return zpods_permissions_groups_add.ZpodsPermissionsGroupsAdd(self._client)

    @property
    @cache  # noqa: B019
    def zpods_permissions_groups_remove(self):
        from zpodsdk.api.zpods import zpods_permissions_groups_remove

        return zpods_permissions_groups_remove.ZpodsPermissionsGroupsRemove(
            self._client
        )

    @property
    @cache  # noqa: B019
    def zpods_permissions_users_add(self):
        from zpodsdk.api.zpods import zpods_permissions_users_add

        return zpods_permissions_users_add.ZpodsPermissionsUsersAdd(self._client)

    @property
    @cache  # noqa: B019
    def zpods_permissions_users_remove(self):
        from zpodsdk.api.zpods import zpods_permissions_users_remove

        return zpods_permissions_users_remove.ZpodsPermissionsUsersRemove(self._client)

    @property
    @cache  # noqa: B019
    def zpods_update(self):
        from zpodsdk.api.zpods import zpods_update

        return zpods_update.ZpodsUpdate(self._client)
