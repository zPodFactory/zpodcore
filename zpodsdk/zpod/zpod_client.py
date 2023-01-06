from functools import cache, partial

from zpod import Client


class ZpodClientMethods:
    def __init__(self, mod, client):
        self._mod = mod
        self._client = client

        self.asyncio = self._load_method("asyncio")
        self.asyncio_detailed = self._load_method("asyncio_detailed")
        self.sync = self._load_method("sync")
        self.sync_detailed = self._load_method("sync_detailed")

    def _load_method(self, method):
        if mod_method := getattr(self._mod, method, None):
            return partial(mod_method, client=self._client)
        else:
            return self._not_implemented(method)

    def _not_implemented(self, method):
        def not_implemented(*args, **kwargs):
            raise NotImplementedError(f"{method} not found in {self._mod.__name__}")

        return not_implemented


class ZpodClient:
    def __init__(self, base_url, token):
        self._client = Client(
            base_url=base_url,
            headers=dict(access_token=token),
        )

    @property
    @cache
    def root_root(self) -> ZpodClientMethods:
        from zpod.api.root import root_root

        return ZpodClientMethods(root_root, self._client)

    @property
    @cache
    def users_create(self) -> ZpodClientMethods:
        from zpod.api.users import users_create

        return ZpodClientMethods(users_create, self._client)

    @property
    @cache
    def users_delete(self) -> ZpodClientMethods:
        from zpod.api.users import users_delete

        return ZpodClientMethods(users_delete, self._client)

    @property
    @cache
    def users_get(self) -> ZpodClientMethods:
        from zpod.api.users import users_get

        return ZpodClientMethods(users_get, self._client)

    @property
    @cache
    def users_get_all(self) -> ZpodClientMethods:
        from zpod.api.users import users_get_all

        return ZpodClientMethods(users_get_all, self._client)

    @property
    @cache
    def users_get_me(self) -> ZpodClientMethods:
        from zpod.api.users import users_get_me

        return ZpodClientMethods(users_get_me, self._client)

    @property
    @cache
    def users_update(self) -> ZpodClientMethods:
        from zpod.api.users import users_update

        return ZpodClientMethods(users_update, self._client)
