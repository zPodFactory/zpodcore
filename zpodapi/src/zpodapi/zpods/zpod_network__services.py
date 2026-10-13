"""User networks on a zPod's zcore: a VLAN interface with its own subnet.

Add and remove are synchronous zboxapi calls (``/vlan``) plus a row in
``zpod_networks``. The row holds what was asked for (name, VLAN, gateway,
masquerade, routing); ``status`` and the live masquerade flag are read from
zboxapi on every list and never stored. Routing changes (advertising the
subnet to the NSX fabric, or withdrawing it) run as the ``zpod_network_routing``
flow; the row says ``PENDING`` meanwhile and Prefect keeps the record.
"""

import re
from ipaddress import IPv4Network, ip_network

import httpx
from fastapi import HTTPException, status

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.enums import (
    ZpodComponentStatus,
    ZpodNetworkKind,
    ZpodNetworkRouting,
    ZpodNetworkStatus,
    ZpodStatus,
)
from zpodcommon.lib.zboxapi import RequestError, ZboxApiClient
from zpodcommon.lib.zpodengine_client import ZpodEngineClient

from .zpod_network__schemas import ZpodNetworkCreate, ZpodNetworkView

# Reads that only decorate a list: fail fast when zcore is not up (yet).
LIVE_READ_TIMEOUT = httpx.Timeout(5.0, connect=3.0)


def candidate_network(gateway: str) -> IPv4Network:
    return ip_network(gateway, strict=False)


class ZpodNetworkService(ServiceBase):
    base_model: M.ZpodNetwork = M.ZpodNetwork

    # ── reads ────────────────────────────────────────────────────────────────

    @staticmethod
    def zcore_ready(zpod: M.Zpod) -> bool:
        """zcore is the first component of every zPod; once it is ACTIVE, zboxapi
        answers, whatever the zPod's own status (still BUILDING, say)."""
        if zpod.status in (ZpodStatus.DELETING, ZpodStatus.DELETED):
            return False
        return any(
            c.component.component_name == "zcore"
            and c.status == ZpodComponentStatus.ACTIVE
            for c in zpod.components
        )

    def refuse_without_zcore(self, zpod: M.Zpod, what: str):
        if not self.zcore_ready(zpod):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"zcore of zPod {zpod.name} is not ACTIVE (zPod {zpod.status}); "
                    f"{what} needs a running zcore."
                ),
            )

    def live_state(self, zpod: M.Zpod) -> dict[int, dict] | None:
        """What zboxapi reports per VLAN id, or None when zcore is not there.

        Asked as soon as the zcore component is ACTIVE, whatever the zPod status.
        A zcore that stopped answering costs the short read timeout, not the
        client's 60 s connect timeout.
        """
        if not self.zcore_ready(zpod):
            return None
        try:
            zb = ZboxApiClient.by_zpod(zpod)
            zb.timeout = LIVE_READ_TIMEOUT  # the client sets its own; override after
            vlans = zb.get(url="/vlan").safejson()
        except (RequestError, HTTPException):
            return None
        return {int(v["vlan"]): v for v in vlans}

    @staticmethod
    def masquerade_supported(live: dict[int, dict] | None) -> bool | None:
        """zboxapi 0.2.0 reports ``masquerade`` on every VLAN it lists (the system
        ones included); 0.1.1 (zcore 13.5) does not have the feature at all.
        None when zcore could not be asked."""
        if live is None:
            return None
        return any("masquerade" in state for state in live.values())

    def refuse_without_masquerade(self, zpod: M.Zpod, live: dict[int, dict] | None):
        if self.masquerade_supported(live) is False:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=(
                    f"zboxapi on zcore.{zpod.domain} has no masquerade support; "
                    "it needs zboxapi 0.2.0 (zcore 13.7)."
                ),
            )

    def view(
        self, network: M.ZpodNetwork, live: dict[int, dict] | None
    ) -> ZpodNetworkView:
        view = ZpodNetworkView.model_validate(network)
        if live is None:
            view.status = ZpodNetworkStatus.UNKNOWN
        elif network.vlan_id == 0:
            # The management network is eth0 itself, not a VLAN interface, so
            # zboxapi does not list it; it answered, so it is up.
            view.status = ZpodNetworkStatus.ACTIVE
        elif (state := live.get(network.vlan_id)) is None:
            view.status = ZpodNetworkStatus.MISSING
        else:
            view.status = (
                ZpodNetworkStatus.ACTIVE
                if state.get("status") == "up"
                else ZpodNetworkStatus.DISABLED
            )
            view.masquerade = bool(state.get("masquerade", network.masquerade))
        return view

    @staticmethod
    def zcore_rows(live: dict[int, dict] | None) -> list[ZpodNetworkView]:
        """zcore's own VLANs (owner system-default on zboxapi: 10, 20, 30 for the nested
        VCF), shown live so the list is the whole box; they have no row and no name of
        their own, so they are named like the deploy rows."""
        rows = []
        for vlan_id, state in sorted((live or {}).items()):
            if state.get("owner") != "system-default":
                continue
            gateway = state.get("gateway", "")
            try:
                cidr = str(ip_network(gateway, strict=False))
            except ValueError:
                cidr = gateway
            rows.append(
                ZpodNetworkView(
                    id=None,
                    name=f"vlan{vlan_id}",
                    cidr=cidr,
                    vlan_id=vlan_id,
                    gateway=gateway,
                    kind=ZpodNetworkKind.ZCORE,
                    masquerade=bool(state.get("masquerade", False)),
                    routing=ZpodNetworkRouting.LOCAL,
                    status=(
                        ZpodNetworkStatus.ACTIVE
                        if state.get("status") == "up"
                        else ZpodNetworkStatus.DISABLED
                    ),
                )
            )
        return rows

    def get_all(self, zpod: M.Zpod) -> list[ZpodNetworkView]:
        live = self.live_state(zpod)
        rows = [self.view(network, live) for network in zpod.networks]
        # Fixed order: management, zcore's own VLANs, the routed /26s, then user networks.
        zpod_rows = [r for r in rows if r.kind == ZpodNetworkKind.ZPOD]
        user_rows = [r for r in rows if r.kind == ZpodNetworkKind.USER]
        return zpod_rows[:1] + self.zcore_rows(live) + zpod_rows[1:] + user_rows

    def get(self, *, zpod: M.Zpod, name: str) -> M.ZpodNetwork:
        for network in zpod.networks:
            if network.name.lower() == name.lower():
                return network
        live = self.live_state(zpod)
        if any(r.name.lower() == name.lower() for r in self.zcore_rows(live)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"{name} is a zcore network (kind zcore), configured by the zcore "
                    "image for the nested VCF; it cannot be changed through zPodFactory."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Network {name} not found on zPod {zpod.name}",
        )

    def get_view(self, *, zpod: M.Zpod, network: M.ZpodNetwork) -> ZpodNetworkView:
        return self.view(network, self.live_state(zpod))

    # ── guards ───────────────────────────────────────────────────────────────

    @staticmethod
    def refuse_zpod_kind(network: M.ZpodNetwork, action: str):
        if network.kind == ZpodNetworkKind.ZPOD:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"{network.name} is a zPodFactory network (kind zpod); {action}"
                ),
            )

    @staticmethod
    def zbox(zpod: M.Zpod) -> ZboxApiClient:
        return ZboxApiClient.by_zpod(zpod)

    def dns_records_inside(self, zpod: M.Zpod, network: IPv4Network) -> list[str]:
        try:
            records = self.zbox(zpod).get(url="/dns").safejson()
        except (RequestError, HTTPException):
            return []
        inside = []
        for record in records:
            try:
                if ip_network(f"{record['ip']}/32").subnet_of(network):
                    inside.append(record["hostname"])
            except (KeyError, ValueError):
                continue
        return sorted(inside)

    # ── add / remove ─────────────────────────────────────────────────────────

    def add(
        self,
        *,
        zpod: M.Zpod,
        item_in: ZpodNetworkCreate,
        current_user: M.User,
    ) -> ZpodNetworkView:
        if item_in.routing == ZpodNetworkRouting.GLOBAL and not current_user.superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "A global network (routed by the NSX fabric) requires superadmin "
                    "privileges. Re-run without routing global, or ask a superadmin to "
                    f"run: zcli zpod network routing {zpod.name} {item_in.name} global"
                ),
            )
        self.refuse_without_zcore(zpod, "adding a network")

        # The reserved VLAN ids (10, 20, 30 and 64, 128, 192) are zboxapi's own
        # system VLANs: it refuses them with a 403 that is passed through below.
        for network in zpod.networks:
            if network.vlan_id == item_in.vlan:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"VLAN {item_in.vlan} is already used on this zPod by network "
                        f"{network.name}."
                    ),
                )
            if network.name.lower() == item_in.name.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Network name {item_in.name} is already used on this zPod.",
                )

        candidate = candidate_network(item_in.gateway)
        for network in zpod.networks:
            existing = IPv4Network(network.cidr)
            if candidate.overlaps(existing):
                who = (
                    "a zPodFactory network of this zPod"
                    if network.kind == ZpodNetworkKind.ZPOD
                    else "a network of this zPod"
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"{candidate} overlaps with {network.name} ({existing}), {who}.",
                )
        pool = (zpod.endpoint.endpoints or {}).get("network", {}).get("networks")
        if pool:
            try:
                pool_network = ip_network(pool, strict=False)
            except ValueError:
                pool_network = None
            if pool_network and candidate.overlaps(pool_network):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"{candidate} overlaps with the endpoint's zPod pool "
                        f"({pool_network}); pick a subnet outside it."
                    ),
                )

        if item_in.masquerade:
            live = self.live_state(zpod)
            if live is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"zcore of zPod {zpod.name} is not reachable",
                )
            self.refuse_without_masquerade(zpod, live)

        try:
            created = (
                self.zbox(zpod)
                .post(
                    url="/vlan",
                    json={
                        "vlan": item_in.vlan,
                        "gateway": item_in.gateway,
                        "masquerade": item_in.masquerade,
                    },
                )
                .safejson()
            )
        except RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"zcore of zPod {zpod.name} is not reachable: {e}",
            ) from e

        network = M.ZpodNetwork(
            zpod_id=zpod.id,
            cidr=str(candidate),
            name=item_in.name,
            vlan_id=item_in.vlan,
            gateway=item_in.gateway,
            kind=ZpodNetworkKind.USER.value,
            # What zboxapi did, not what was asked (an old zboxapi ignores the field).
            masquerade=bool((created or {}).get("masquerade", False)),
            routing=ZpodNetworkRouting.LOCAL.value,
        )
        self.session.add(network)
        self.session.flush()

        if item_in.routing == ZpodNetworkRouting.GLOBAL:
            network.routing = ZpodNetworkRouting.PENDING.value
            self.schedule_routing(
                zpod=zpod,
                network=network,
                target=ZpodNetworkRouting.GLOBAL,
                previous=ZpodNetworkRouting.LOCAL.value,
                requested_by=current_user.username,
                dry_run=False,
            )

        self.session.commit()
        self.session.refresh(zpod)
        view = ZpodNetworkView.model_validate(network)
        view.status = (
            ZpodNetworkStatus.ACTIVE
            if (created or {}).get("status", "up") == "up"
            else ZpodNetworkStatus.DISABLED
        )
        return view

    def remove(self, *, zpod: M.Zpod, network: M.ZpodNetwork) -> None:
        self.refuse_zpod_kind(network, "it is created and removed with the zPod only.")
        self.refuse_without_zcore(zpod, "removing a network")
        if network.routing == ZpodNetworkRouting.GLOBAL:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"{network.name} is routing global; set it local first "
                    f"(zcli zpod network routing {zpod.name} {network.name} local), "
                    "then remove it."
                ),
            )
        if network.routing == ZpodNetworkRouting.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{network.name} has a routing change running; wait for it to finish.",
            )
        if hostnames := self.dns_records_inside(zpod, IPv4Network(network.cidr)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"{len(hostnames)} DNS record(s) of {zpod.name} point into "
                    f"{network.cidr} ({', '.join(hostnames)}); delete them first."
                ),
            )
        try:
            self.zbox(zpod).delete(url=f"/vlan/{network.vlan_id}").safejson()
        except RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"zcore of zPod {zpod.name} is not reachable: {e}",
            ) from e
        except HTTPException as e:
            # Already gone on the box (MISSING): the row goes anyway.
            if e.status_code != status.HTTP_404_NOT_FOUND:
                raise
        self.session.delete(network)
        self.session.commit()

    # ── toggles ──────────────────────────────────────────────────────────────

    def masquerade(
        self, *, zpod: M.Zpod, network: M.ZpodNetwork, enabled: bool
    ) -> ZpodNetworkView:
        self.refuse_zpod_kind(network, "masquerading cannot be changed on it.")
        self.refuse_without_zcore(zpod, "changing masquerade")
        self.refuse_without_masquerade(zpod, self.live_state(zpod))
        if enabled and network.routing != ZpodNetworkRouting.LOCAL:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"{network.name} is routing {str(network.routing).lower()}: a global "
                    "network is reachable without translation. Set routing local first."
                ),
            )
        try:
            result = (
                self.zbox(zpod)
                .put(
                    url=f"/vlan/{network.vlan_id}/masquerade", json={"enabled": enabled}
                )
                .safejson()
            )
        except RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"zcore of zPod {zpod.name} is not reachable: {e}",
            ) from e
        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND and "Not Found" in str(
                e.detail
            ):
                # zboxapi < 0.2.0 has no /masquerade route (zcore 13.5 appliances).
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail=(
                        f"zboxapi on zcore.{zpod.domain} has no masquerade support; "
                        "it needs zboxapi 0.2.0 (zcore 13.7)."
                    ),
                ) from e
            raise
        network.masquerade = bool((result or {}).get("masquerade", enabled))
        self.session.add(network)
        self.session.commit()
        return self.view(network, self.live_state(zpod))

    def set_enabled(
        self, *, zpod: M.Zpod, network: M.ZpodNetwork, enabled: bool
    ) -> ZpodNetworkView:
        self.refuse_zpod_kind(
            network,
            "it cannot be disabled (nested ESXi vmk and the trunk depend on it)."
            if not enabled
            else "it is always enabled.",
        )
        self.refuse_without_zcore(zpod, "enabling or disabling a network")
        action = "enable" if enabled else "disable"
        try:
            self.zbox(zpod).put(url=f"/vlan/{network.vlan_id}/{action}").safejson()
        except RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"zcore of zPod {zpod.name} is not reachable: {e}",
            ) from e
        return self.view(network, self.live_state(zpod))

    # ── routing (advertisement) ──────────────────────────────────────────────

    def schedule_routing(
        self,
        *,
        zpod: M.Zpod,
        network: M.ZpodNetwork,
        target: ZpodNetworkRouting,
        previous: str,
        requested_by: str,
        dry_run: bool,
    ) -> str | None:
        verb = "advertise" if target == ZpodNetworkRouting.GLOBAL else "withdraw"
        if dry_run:
            verb = f"{verb} (dry run)"
        zpod_engine = ZpodEngineClient()
        run = zpod_engine.create_flow_run_by_name(
            flow_name="zpod_network_routing",
            deployment_name="zpod_network_routing",
            run_name=f"{verb} {zpod.name}/{network.name} by {requested_by}",
            zpod_id=zpod.id,
            network_id=network.id,
            zpod_name=zpod.name,
            network_name=network.name,
            target=target.value,
            previous=previous,  # restored on a dry run or a failure
            requested_by=requested_by,
            dry_run=dry_run,
            verb=verb,
        )
        return (run or {}).get("id")

    # Prefect prefixes a failed run's message with the exception; the user wants the
    # check verdict ("FAIL: ... overlaps ...") as the flow raised it.
    RUN_MESSAGE_PREFIX = re.compile(
        r"^Flow run encountered an exception: (?:[A-Za-z_.]*Error: )?"
    )

    def routing_run(
        self,
        *,
        zpod: M.Zpod,
        network: M.ZpodNetwork,
        flow_run_id: str,
    ) -> dict:
        """The routing run with that id, if it is this network's; 404 otherwise."""
        run = ZpodEngineClient().get_flow_run(flow_run_id)
        params = (run or {}).get("parameters", {})
        if (
            run is None
            or params.get("zpod_id") != zpod.id
            or params.get("network_id") != network.id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No routing run {flow_run_id} for network {network.name}.",
            )
        message = run.get("message")
        if message:
            message = self.RUN_MESSAGE_PREFIX.sub("", message, count=1)
        self.session.refresh(network)
        return {
            "network": self.get_view(zpod=zpod, network=network),
            "flow_run_id": flow_run_id,
            "name": run.get("name"),
            "state": run.get("state") or "UNKNOWN",
            "message": message,
        }

    def routing(
        self,
        *,
        zpod: M.Zpod,
        network: M.ZpodNetwork,
        target: ZpodNetworkRouting,
        dry_run: bool,
        current_user: M.User,
    ) -> tuple[M.ZpodNetwork, str | None]:
        self.refuse_zpod_kind(
            network, "its routing is fixed to global and managed by the zPod deploy."
        )
        if network.routing == ZpodNetworkRouting.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{network.name} already has a routing change running.",
            )
        if network.routing == target and not dry_run:
            return network, None
        self.refuse_without_zcore(zpod, "a routing change")
        previous = network.routing
        network.routing = ZpodNetworkRouting.PENDING.value
        self.session.add(network)
        self.session.flush()
        flow_run_id = self.schedule_routing(
            zpod=zpod,
            network=network,
            target=target,
            previous=previous,
            requested_by=current_user.username,
            dry_run=dry_run,
        )
        self.session.commit()
        return network, flow_run_id
