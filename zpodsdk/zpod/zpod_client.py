from functools import cache

from zpod import Client


class ZpodClient:
    def __init__(self, base_url, token):
        self._client = Client(
            base_url=base_url,
            headers=dict(access_token=token),
        )

    @property
    @cache
    def components_disable(self):
        from zpod.api.components import components_disable

        return components_disable.ComponentsDisable(self._client)

    @property
    @cache
    def components_enable(self):
        from zpod.api.components import components_enable

        return components_enable.ComponentsEnable(self._client)

    @property
    @cache
    def components_get(self):
        from zpod.api.components import components_get

        return components_get.ComponentsGet(self._client)

    @property
    @cache
    def components_get_all(self):
        from zpod.api.components import components_get_all

        return components_get_all.ComponentsGetAll(self._client)

    @property
    @cache
    def endpoints_create(self):
        from zpod.api.endpoints import endpoints_create

        return endpoints_create.EndpointsCreate(self._client)

    @property
    @cache
    def endpoints_delete(self):
        from zpod.api.endpoints import endpoints_delete

        return endpoints_delete.EndpointsDelete(self._client)

    @property
    @cache
    def endpoints_get(self):
        from zpod.api.endpoints import endpoints_get

        return endpoints_get.EndpointsGet(self._client)

    @property
    @cache
    def endpoints_get_all(self):
        from zpod.api.endpoints import endpoints_get_all

        return endpoints_get_all.EndpointsGetAll(self._client)

    @property
    @cache
    def endpoints_update(self):
        from zpod.api.endpoints import endpoints_update

        return endpoints_update.EndpointsUpdate(self._client)

    @property
    @cache
    def endpoints_verify(self):
        from zpod.api.endpoints import endpoints_verify

        return endpoints_verify.EndpointsVerify(self._client)

    @property
    @cache
    def instances_components_add(self):
        from zpod.api.instances import instances_components_add

        return instances_components_add.InstancesComponentsAdd(self._client)

    @property
    @cache
    def instances_components_get_all(self):
        from zpod.api.instances import instances_components_get_all

        return instances_components_get_all.InstancesComponentsGetAll(self._client)

    @property
    @cache
    def instances_create(self):
        from zpod.api.instances import instances_create

        return instances_create.InstancesCreate(self._client)

    @property
    @cache
    def instances_delete(self):
        from zpod.api.instances import instances_delete

        return instances_delete.InstancesDelete(self._client)

    @property
    @cache
    def instances_features_get_all(self):
        from zpod.api.instances import instances_features_get_all

        return instances_features_get_all.InstancesFeaturesGetAll(self._client)

    @property
    @cache
    def instances_get(self):
        from zpod.api.instances import instances_get

        return instances_get.InstancesGet(self._client)

    @property
    @cache
    def instances_get_all(self):
        from zpod.api.instances import instances_get_all

        return instances_get_all.InstancesGetAll(self._client)

    @property
    @cache
    def instances_networks_get_all(self):
        from zpod.api.instances import instances_networks_get_all

        return instances_networks_get_all.InstancesNetworksGetAll(self._client)

    @property
    @cache
    def instances_update(self):
        from zpod.api.instances import instances_update

        return instances_update.InstancesUpdate(self._client)

    @property
    @cache
    def libraries_create(self):
        from zpod.api.libraries import libraries_create

        return libraries_create.LibrariesCreate(self._client)

    @property
    @cache
    def libraries_delete(self):
        from zpod.api.libraries import libraries_delete

        return libraries_delete.LibrariesDelete(self._client)

    @property
    @cache
    def libraries_get(self):
        from zpod.api.libraries import libraries_get

        return libraries_get.LibrariesGet(self._client)

    @property
    @cache
    def libraries_get_all(self):
        from zpod.api.libraries import libraries_get_all

        return libraries_get_all.LibrariesGetAll(self._client)

    @property
    @cache
    def libraries_update(self):
        from zpod.api.libraries import libraries_update

        return libraries_update.LibrariesUpdate(self._client)

    @property
    @cache
    def root_root(self):
        from zpod.api.root import root_root

        return root_root.RootRoot(self._client)

    @property
    @cache
    def settings_create(self):
        from zpod.api.settings import settings_create

        return settings_create.SettingsCreate(self._client)

    @property
    @cache
    def settings_delete(self):
        from zpod.api.settings import settings_delete

        return settings_delete.SettingsDelete(self._client)

    @property
    @cache
    def settings_get(self):
        from zpod.api.settings import settings_get

        return settings_get.SettingsGet(self._client)

    @property
    @cache
    def settings_get_all(self):
        from zpod.api.settings import settings_get_all

        return settings_get_all.SettingsGetAll(self._client)

    @property
    @cache
    def settings_update(self):
        from zpod.api.settings import settings_update

        return settings_update.SettingsUpdate(self._client)

    @property
    @cache
    def users_create(self):
        from zpod.api.users import users_create

        return users_create.UsersCreate(self._client)

    @property
    @cache
    def users_delete(self):
        from zpod.api.users import users_delete

        return users_delete.UsersDelete(self._client)

    @property
    @cache
    def users_get(self):
        from zpod.api.users import users_get

        return users_get.UsersGet(self._client)

    @property
    @cache
    def users_get_all(self):
        from zpod.api.users import users_get_all

        return users_get_all.UsersGetAll(self._client)

    @property
    @cache
    def users_get_me(self):
        from zpod.api.users import users_get_me

        return users_get_me.UsersGetMe(self._client)

    @property
    @cache
    def users_update(self):
        from zpod.api.users import users_update

        return users_update.UsersUpdate(self._client)
