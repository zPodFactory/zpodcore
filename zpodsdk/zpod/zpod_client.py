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
    def components_get_all(self):
        from zpod.api.components import components_get_all

        return components_get_all.ComponentsGetAll(self._client)

    @property
    @cache
    def components_update(self):
        from zpod.api.components import components_update

        return components_update.ComponentsUpdate(self._client)

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
