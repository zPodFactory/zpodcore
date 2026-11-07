"""ZpodEngineClient speaks Prefect's REST API: the run listing and the cancel."""

import json

import httpx

from zpodcommon.lib.zpodengine_client import ACTIVE_STATE_TYPES, ZpodEngineClient


def run(run_id, zpod_id, state="RUNNING"):
    return {
        "id": run_id,
        "name": f"run {run_id}",
        "state": {"type": state, "message": None},
        "parameters": {"zpod_id": zpod_id},
    }


def client_with(handler):
    client = ZpodEngineClient()
    client.client = httpx.Client(
        base_url="http://zpodengineserver:4200/api",
        transport=httpx.MockTransport(handler),
    )
    return client


def test_zpod_flow_runs_are_the_active_top_level_runs_with_that_zpod_id():
    requests = []

    def handler(request):
        requests.append((request.url.path, json.loads(request.content)))
        return httpx.Response(
            200,
            json=[run("a", 7), run("b", 8), run("c", 7), {"id": "d", "state": None}],
        )

    runs = client_with(handler).get_zpod_flow_runs(7)
    assert [r["id"] for r in runs] == ["a", "c"]
    assert runs[0] == {
        "id": "a",
        "name": "run a",
        "state": "RUNNING",
        "message": None,
        "parameters": {"zpod_id": 7},
        "start_time": None,
        "end_time": None,
    }
    path, body = requests[0]
    assert path == "/api/flow_runs/filter"
    assert body["flow_runs"]["state"]["type"]["any_"] == ACTIVE_STATE_TYPES
    assert body["flow_runs"]["parent_task_run_id"] == {"is_null_": True}


def test_cancel_asks_for_cancelling_and_force_writes_cancelled():
    requests = []

    def handler(request):
        requests.append((request.url.path, json.loads(request.content)))
        return httpx.Response(201, json={"status": "ACCEPT"})

    client = client_with(handler)
    assert client.cancel_flow_run("a", message="bye") == {"status": "ACCEPT"}
    client.cancel_flow_run("a", message="bye", force=True)
    assert requests == [
        (
            "/api/flow_runs/a/set_state",
            {"state": {"type": "CANCELLING", "message": "bye"}, "force": False},
        ),
        (
            "/api/flow_runs/a/set_state",
            {"state": {"type": "CANCELLED", "message": "bye"}, "force": True},
        ),
    ]
