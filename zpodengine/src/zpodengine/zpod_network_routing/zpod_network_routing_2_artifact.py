import re
from datetime import UTC, datetime

from prefect import task
from prefect.artifacts import create_markdown_artifact

from zpodcommon.enums import ZpodNetworkRouting
from zpodengine.lib import database
from zpodengine.zpod_network_routing.common import load_zpod_network, route_facts


def artifact_key(zpod_name: str, network_name: str) -> str:
    """Prefect artifact keys: lowercase letters, digits and dashes only."""
    raw = f"advertisement-{zpod_name}-{network_name}".lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", raw)).strip("-")


def render_markdown(
    *,
    zpod_name: str,
    network_name: str,
    target: str,
    requested_by: str,
    dry_run: bool,
    timestamp: str,
    candidate: str,
    tier1_id: str,
    route_id: str,
    next_hop: str,
    checks: dict[str, dict],
) -> str:
    verb = (
        "Advertise"
        if ZpodNetworkRouting(target) == ZpodNetworkRouting.GLOBAL
        else "Withdraw"
    )
    lines = [
        f"# {verb} {zpod_name}/{network_name}",
        "",
        "| | |",
        "|---|---|",
        f"| Actor | {requested_by} |",
        f"| Target | {target} |",
        f"| Dry run | {dry_run} |",
        f"| Timestamp | {timestamp} |",
        f"| Candidate network | `{candidate}` |",
        f"| T1 | `{tier1_id}` |",
        f"| Route id | `{route_id}` |",
        f"| Next hop | `{next_hop}` |",
        "",
    ]
    if not checks:
        lines.append("No advertisement checks: the route is withdrawn.")
        return "\n".join(lines) + "\n"

    lines += [
        "## Checks",
        "",
        "| Check | Result | Entries | Detail |",
        "|---|---|---|---|",
    ]
    for name, result in checks.items():
        verdict = "ok" if result["ok"] else "FAIL"
        lines.append(f"| {name} | {verdict} | {result['count']} | {result['detail']} |")
    lines.append("")
    for name, result in checks.items():
        inventory = result.get("inventory") or []
        lines += [
            "<details>",
            f"<summary>{name} inventory ({len(inventory)} lines)</summary>",
            "",
            "```",
            *(inventory or ["(empty)"]),
            "```",
            "",
            "</details>",
            "",
        ]
    return "\n".join(lines)


@task
def zpod_network_routing_artifact(
    zpod_id: int,
    network_id: int,
    target: str,
    requested_by: str,
    dry_run: bool,
    checks: dict[str, dict],
) -> str:
    with database.get_session_ctx() as session:
        zpod, network = load_zpod_network(session, zpod_id, network_id)
        facts = route_facts(zpod, network)
        key = artifact_key(zpod.name, network.name)
        markdown = render_markdown(
            zpod_name=zpod.name,
            network_name=network.name,
            target=target,
            requested_by=requested_by,
            dry_run=dry_run,
            timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
            candidate=str(facts.candidate),
            tier1_id=facts.tier1_id,
            route_id=facts.route_id,
            next_hop=facts.next_hop,
            checks=checks,
        )
    create_markdown_artifact(
        key=key,
        markdown=markdown,
        description=f"{target} {zpod.name}/{network.name} by {requested_by}",
    )
    print(f"Artifact {key} written")
    return key
