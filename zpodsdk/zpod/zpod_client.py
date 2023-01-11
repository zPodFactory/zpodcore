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
