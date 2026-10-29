from ipaddress import IPv4Address

from fastapi import HTTPException, status
from sqlmodel import SQLModel, select

from zpodapi.lib.service_base import ServiceBase
from zpodapi.profiles.profile__utils import check_fqdn_length, compute_zpod_domain
from zpodapi.zpods.zpod_component__schemas import ZpodComponentCreate
from zpodcommon import models as M
from zpodcommon.enums import ComponentStatus, ZpodComponentStatus
from zpodcommon.lib.component_network import (
    ComponentNetworkError,
    resolve_new_component_network,
)
from zpodcommon.lib.component_placement import component_options_error
from zpodcommon.lib.network_utils import (
    get_all_active_addresses,
    get_zpod_reserved_addresses,
)
from zpodcommon.lib.zpodengine_client import ZpodEngineClient


class ZpodComponentService(ServiceBase):
    base_model: SQLModel = M.ZpodComponent

    def add(
        self,
        *,
        zpod: M.Zpod,
        component_in: ZpodComponentCreate,
    ):
        hostname = component_in.hostname
        host_id = component_in.host_id
        network = (
            component_in.network.model_dump(exclude_none=True)
            if component_in.network
            else None
        ) or None

        # An explicit network.ip gives the address: hostname alone is enough then.
        explicit_ip = bool(network and network.get("ip"))
        if not explicit_ip and (
            (hostname and not host_id) or (not hostname and host_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Must provide both hostname and host-id when either is provided.",  # noqa: E501
            )

        component = self.session.exec(
            select(M.Component).where(
                M.Component.component_uid == component_in.component_uid,
                M.Component.status == ComponentStatus.ACTIVE,
            )
        ).one_or_none()
        if component is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No ACTIVE component {component_in.component_uid}",
            )
        # Only deploy options need the component's library JSON.
        options = {
            "nested": component_in.nested,
            "network": network,
            "vnics": component_in.vnics,
            "vlan_id": component_in.vlan_id,
        }
        if any(v is not None for v in options.values()) and (
            error := component_options_error(
                component.component_name, component.component_json, **options
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=error,
            )
        if not hostname:
            if component.component_name == "esxi":
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail="Must provide hostname and host-id when adding esxi.",
                )
            # if hostname is not provided, look up default value
            hostname = component.component_name

        # Same guardrail as POST /zpods: the resulting FQDN must fit the Linux
        # hostname limit. zpod.domain is set by the deploy prep flow; fall back
        # to the same derivation for a zPod that has not been prepped yet.
        check_fqdn_length(
            f"{hostname}.{compute_zpod_domain(zpod_name=zpod.name, domain=zpod.domain)}"
        )

        # if hostname is already found, raise error
        if self.session.exec(
            select(M.ZpodComponent).where(
                M.ZpodComponent.zpod_id == zpod.id,
                M.ZpodComponent.hostname == hostname,
                M.ZpodComponent.status.in_(
                    [
                        ZpodComponentStatus.ACTIVE,
                        ZpodComponentStatus.BUILDING,
                    ]
                ),
            )
        ).one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflicting hostname found",
            )

        try:
            component_ip = IPv4Address(
                resolve_new_component_network(
                    zpod,
                    component,
                    network=network,
                    host_id=host_id,
                    vlan_id=component_in.vlan_id,
                    nested=component_in.nested,
                ).ip
            )
        except ComponentNetworkError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
            ) from e

        if component_ip in get_zpod_reserved_addresses(zpod):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invalid IP: {component_ip}.  Specified IP is a reserved IP.",
            )
        if component_ip in get_all_active_addresses(zpod):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invalid IP: {component_ip}.  Specified IP is already in use.",
            )

        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="zpod_component_add",
            deployment_name="zpod_component_add",
            run_name=(f"{zpod.name} adding {component_in.component_uid}"),
            zpod_id=zpod.id,
            zpod_name=zpod.name,
            component_uid=component_in.component_uid,
            host_id=component_in.host_id,
            hostname=component_in.hostname,
            vcpu=component_in.vcpu,
            vmem=component_in.vmem,
            vnics=component_in.vnics,
            vdisks=component_in.vdisks,
            nested=component_in.nested,
            network=network,
            vlan_id=component_in.vlan_id,
        )

    def remove(
        self,
        *,
        zpod_component,
    ):
        zpod_engine = ZpodEngineClient()
        zpod_engine.create_flow_run_by_name(
            flow_name="zpod_component_remove",
            deployment_name="zpod_component_remove",
            zpod_component_id=zpod_component.id,
        )
