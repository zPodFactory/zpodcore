"""Real DNS query helper.

Several tests need to confirm a DNS record actually resolves (not just
that the API reports it exists) - e.g. after `zcli zpod dns add`, or after
deleting a zpod and expecting its domain to stop resolving. dnsmasq (the
resolver behind zpodcore) can lag slightly behind an API write, so this
retries briefly rather than querying exactly once.
"""

import time

import dns.exception
import dns.resolver


class DnsQueryError(Exception):
    pass


def query(hostname: str, resolver_ip: str, *, retries: int = 3, retry_interval: float = 2.0) -> str | None:
    """Return the first resolved A-record IP for `hostname`, or None if it doesn't resolve."""
    r = dns.resolver.Resolver(configure=False)
    r.nameservers = [resolver_ip]
    r.timeout = 3
    r.lifetime = 3

    last_exc = None
    for attempt in range(retries):
        try:
            answer = r.resolve(hostname, "A")
            return str(answer[0])
        except dns.resolver.NXDOMAIN:
            return None
        except dns.exception.DNSException as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(retry_interval)
    raise DnsQueryError(f"DNS query for {hostname} against {resolver_ip} failed: {last_exc}")


def _log_dns_result(
    hostname: str, resolver_ip: str, expected: str, actual: str, as_expected: bool, duration: float, attempts: int,
) -> None:
    try:
        from e2e.report import recorder

        recorder.log_dns(hostname, resolver_ip, expected, actual, as_expected, duration, attempts=attempts)
    except Exception:
        pass  # reporting must never break a test


def wait_until_resolves(hostname: str, resolver_ip: str, *, timeout_seconds: int = 60, interval_seconds: int = 3) -> str:
    start = time.monotonic()
    ip = None
    attempts = 0
    try:
        while True:
            attempts += 1
            ip = query(hostname, resolver_ip, retries=1)
            if ip:
                return ip
            if time.monotonic() - start >= timeout_seconds:
                raise DnsQueryError(f"{hostname} did not resolve via {resolver_ip} within {timeout_seconds}s")
            time.sleep(interval_seconds)
    finally:
        _log_dns_result(
            hostname, resolver_ip, "resolves (A record)", ip or "NXDOMAIN",
            as_expected=bool(ip), duration=time.monotonic() - start, attempts=attempts,
        )


def wait_until_nxdomain(hostname: str, resolver_ip: str, *, timeout_seconds: int = 60, interval_seconds: int = 3) -> None:
    start = time.monotonic()
    ip = None
    attempts = 0
    try:
        while True:
            attempts += 1
            ip = query(hostname, resolver_ip, retries=1)
            if ip is None:
                return
            if time.monotonic() - start >= timeout_seconds:
                raise DnsQueryError(
                    f"{hostname} still resolves to {ip} via {resolver_ip} after {timeout_seconds}s (expected NXDOMAIN)"
                )
            time.sleep(interval_seconds)
    finally:
        _log_dns_result(
            hostname, resolver_ip, "NXDOMAIN", ip or "NXDOMAIN",
            as_expected=(ip is None), duration=time.monotonic() - start, attempts=attempts,
        )
