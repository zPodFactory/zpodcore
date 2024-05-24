from ipaddress import IPv4Address, IPv4Network

from fastapi import HTTPException, status

from zpodapi.lib.service_base import ServiceBase
from zpodcommon import models as M
from zpodcommon.lib.zboxapi import ZboxApiClient


class ZpodDnsService(ServiceBase):
    def get_all(
        self,
        zpod: M.Zpod,
    ):
        zb = ZboxApiClient.by_zpod(zpod)
        response = zb.get(url="/dns")
        return response.safejson()

    def get(
        self,
        zpod: M.Zpod,
        ip: IPv4Address,
        hostname: str,
    ):
        zb = ZboxApiClient.by_zpod(zpod)
        response = zb.get(url=f"/dns/{ip}/{hostname}")
        if dns := response.safejson():
            return dns
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DNS record not found",
        )

    def get_ip(
        self,
        zpod: M.Zpod,
        ip: IPv4Address | None,
        host_id: int | None,
    ):
        if host_id:
            return IPv4Network(zpod.networks[0].cidr).network_address + host_id
        return ip

    def add(
        self,
        *,
        zpod: M.Zpod,
        hostname: str,
        ip: IPv4Address | None = None,
        host_id: int | None = None,
    ):
        ip = self.get_ip(zpod, ip, host_id)
        zb = ZboxApiClient.by_zpod(zpod)
        response = zb.post(
            url="/dns",
            json={"ip": str(ip), "hostname": hostname},
        )
        return response.safejson()

    def update(
        self,
        *,
        zpod: M.Zpod,
        hostname: str,
        ip: IPv4Address,
        newhostname: str,
        newip: IPv4Address | None = None,
        newhost_id: int | None = None,
    ):
        newip = self.get_ip(zpod, newip, newhost_id)
        zb = ZboxApiClient.by_zpod(zpod)
        response = zb.put(
            url=f"/dns/{ip}/{hostname}",
            json={"ip": str(newip), "hostname": newhostname},
        )
        return response.safejson()

    def remove(
        self,
        *,
        zpod: M.Zpod,
        hostname: str,
        ip: str,
    ):
        zb = ZboxApiClient.by_zpod(zpod)
        response = zb.delete(url=f"/dns/{ip}/{hostname}")
        return response.safejson()
