from fastapi import APIRouter, status

from zpodapi.lib.global_dependencies import GlobalAnnotations, GlobalDepends
from zpodapi.lib.route_logger import RouteLogger

from .zpod__dependencies import ZpodAnnotations, ZpodDepends
from .zpod_network__dependencies import ZpodNetworkAnnotations
from .zpod_network__schemas import (
    ZpodNetworkCreate,
    ZpodNetworkMasquerade,
    ZpodNetworkRoutingRunView,
    ZpodNetworkRoutingUpdate,
    ZpodNetworkRoutingView,
    ZpodNetworkView,
)

router = APIRouter(
    prefix="/zpods/{id}/networks",
    tags=["zpods"],
    route_class=RouteLogger,
)


@router.get(
    "",
    summary="zPod Network Get All",
    response_model=list[ZpodNetworkView],
    dependencies=[ZpodDepends.ZpodReader],
)
def networks_get_all(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_network_service: ZpodNetworkAnnotations.ZpodNetworkService,
):
    return zpod_network_service.get_all(zpod)


@router.get(
    "/{name}",
    summary="zPod Network Get",
    response_model=ZpodNetworkView,
    dependencies=[ZpodDepends.ZpodReader],
)
def network_get(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_network: ZpodNetworkAnnotations.GetZpodNetwork,
    zpod_network_service: ZpodNetworkAnnotations.ZpodNetworkService,
):
    return zpod_network_service.get_view(zpod=zpod, network=zpod_network)


@router.post(
    "",
    summary="zPod Network Add",
    response_model=ZpodNetworkView,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def network_add(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_network_service: ZpodNetworkAnnotations.ZpodNetworkService,
    current_user: GlobalAnnotations.GetCurrentUser,
    network_in: ZpodNetworkCreate,
):
    return zpod_network_service.add(
        zpod=zpod, item_in=network_in, current_user=current_user
    )


@router.delete(
    "/{name}",
    summary="zPod Network Remove",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def network_remove(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_network: ZpodNetworkAnnotations.GetZpodNetwork,
    zpod_network_service: ZpodNetworkAnnotations.ZpodNetworkService,
):
    zpod_network_service.remove(zpod=zpod, network=zpod_network)


@router.put(
    "/{name}/masquerade",
    summary="zPod Network Masquerade",
    response_model=ZpodNetworkView,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def network_masquerade(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_network: ZpodNetworkAnnotations.GetZpodNetwork,
    zpod_network_service: ZpodNetworkAnnotations.ZpodNetworkService,
    masquerade_in: ZpodNetworkMasquerade,
):
    return zpod_network_service.masquerade(
        zpod=zpod, network=zpod_network, enabled=masquerade_in.enabled
    )


@router.put(
    "/{name}/enable",
    summary="zPod Network Enable",
    response_model=ZpodNetworkView,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def network_enable(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_network: ZpodNetworkAnnotations.GetZpodNetwork,
    zpod_network_service: ZpodNetworkAnnotations.ZpodNetworkService,
):
    return zpod_network_service.set_enabled(
        zpod=zpod, network=zpod_network, enabled=True
    )


@router.put(
    "/{name}/disable",
    summary="zPod Network Disable",
    response_model=ZpodNetworkView,
    dependencies=[ZpodDepends.ZpodMaintainer],
)
def network_disable(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_network: ZpodNetworkAnnotations.GetZpodNetwork,
    zpod_network_service: ZpodNetworkAnnotations.ZpodNetworkService,
):
    return zpod_network_service.set_enabled(
        zpod=zpod, network=zpod_network, enabled=False
    )


@router.put(
    "/{name}/routing",
    summary="zPod Network Routing",
    response_model=ZpodNetworkRoutingView,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[GlobalDepends.OnlySuperAdmin],
)
def network_routing(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_network: ZpodNetworkAnnotations.GetZpodNetwork,
    zpod_network_service: ZpodNetworkAnnotations.ZpodNetworkService,
    current_user: GlobalAnnotations.GetCurrentUser,
    routing_in: ZpodNetworkRoutingUpdate,
):
    network, flow_run_id = zpod_network_service.routing(
        zpod=zpod,
        network=zpod_network,
        target=routing_in.routing,
        dry_run=routing_in.dry_run,
        current_user=current_user,
    )
    return ZpodNetworkRoutingView(
        network=ZpodNetworkView.model_validate(network),
        flow_run_id=flow_run_id,
    )


@router.get(
    "/{name}/routing/{flow_run_id}",
    summary="zPod Network Routing Run",
    response_model=ZpodNetworkRoutingRunView,
    dependencies=[ZpodDepends.ZpodReader],
)
def network_routing_run(
    *,
    zpod: ZpodAnnotations.GetZpod,
    zpod_network: ZpodNetworkAnnotations.GetZpodNetwork,
    zpod_network_service: ZpodNetworkAnnotations.ZpodNetworkService,
    flow_run_id: str,
):
    """The state of a routing change started with PUT .../routing: the run's state
    and message (the failing check when it failed) and the network as it is now."""
    return zpod_network_service.routing_run(
        zpod=zpod, network=zpod_network, flow_run_id=flow_run_id
    )
