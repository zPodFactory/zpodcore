"""A destroy first cancels the runs still working on the zPod and waits for them."""

import pytest

from zpodcommon.lib.zpodengine_client import ACTIVE_STATE_TYPES
from zpodengine.lib import flow_runs as mod

OWN = "own-destroy-run"


class FakeTime:
    def __init__(self):
        self.now = 1000.0
        self.slept = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


class FakeEngine:
    """Runs keyed by id; ``on_cancel`` says what a cancel request does to a run
    (``None``: it ignores it, a zombie). ``appear_at`` adds a run at the n-th listing."""

    def __init__(self, runs, on_cancel=None, appear_at=None):
        self.runs = dict(runs)
        self.on_cancel = on_cancel or {}
        self.appear_at = appear_at or {}
        self.cancelled = []
        self.listings = 0

    def get_zpod_flow_runs(self, zpod_id):
        self.listings += 1
        for run_id, run in self.appear_at.pop(self.listings, {}).items():
            self.runs[run_id] = run
        return [
            {"id": run_id, "name": name, "state": state}
            for run_id, (name, state, rid) in self.runs.items()
            if rid == zpod_id and state in ACTIVE_STATE_TYPES
        ]

    def cancel_flow_run(self, run_id, *, message=None, force=False):
        self.cancelled.append((run_id, force))
        name, _, zid = self.runs[run_id]
        if force:
            self.runs[run_id] = (name, "CANCELLED", zid)
        elif (state := self.on_cancel.get(run_id, "CANCELLED")) is not None:
            self.runs[run_id] = (name, state, zid)


@pytest.fixture
def clock(monkeypatch):
    fake = FakeTime()
    monkeypatch.setattr(mod, "time", fake)
    monkeypatch.setattr(mod.flow_run, "id", OWN, raising=False)
    return fake


def test_nothing_running_returns_at_once(clock):
    engine = FakeEngine({OWN: ("Destroy lab", "RUNNING", 7)})
    assert mod.cancel_zpod_runs(7, reason="r", client=engine) == []
    assert engine.cancelled == []
    assert clock.slept == []


def test_cancels_the_deploy_and_waits_for_it(clock):
    engine = FakeEngine(
        {
            OWN: ("Destroy lab", "RUNNING", 7),
            "dep": ("Deploy lab", "RUNNING", 7),
            "other": ("Deploy other", "RUNNING", 8),
        },
        # The runner acknowledges first, the run is terminal one poll later.
        on_cancel={"dep": "CANCELLING"},
    )
    orig = engine.get_zpod_flow_runs

    def settle(zpod_id):
        if engine.listings == 2:
            engine.runs["dep"] = ("Deploy lab", "CANCELLED", 7)
        return orig(zpod_id)

    engine.get_zpod_flow_runs = settle
    assert mod.cancel_zpod_runs(7, reason="r", client=engine, poll=5) == ["Deploy lab"]
    assert engine.cancelled == [("dep", False)]
    assert clock.slept == [5, 5]


def test_a_run_scheduled_meanwhile_is_cancelled_too(clock):
    engine = FakeEngine(
        {OWN: ("Destroy lab", "RUNNING", 7), "dep": ("Deploy lab", "RUNNING", 7)},
        appear_at={2: {"add": ("lab adding esxi", "SCHEDULED", 7)}},
    )
    names = mod.cancel_zpod_runs(7, reason="r", client=engine, poll=5)
    assert names == ["Deploy lab", "lab adding esxi"]
    assert engine.cancelled == [("dep", False), ("add", False)]


def test_a_zombie_is_forced_cancelled_after_the_timeout(clock):
    engine = FakeEngine(
        {OWN: ("Destroy lab", "RUNNING", 7), "dep": ("Deploy lab", "RUNNING", 7)},
        on_cancel={"dep": None},
    )
    names = mod.cancel_zpod_runs(7, reason="r", client=engine, timeout=20, poll=5)
    assert names == ["Deploy lab"]
    assert engine.cancelled == [("dep", False), ("dep", True)]
    assert sum(clock.slept) == 20


def test_a_run_that_survives_the_force_fails_the_destroy(clock):
    engine = FakeEngine(
        {OWN: ("Destroy lab", "RUNNING", 7), "dep": ("Deploy lab", "RUNNING", 7)},
        on_cancel={"dep": None},
    )
    orig = engine.cancel_flow_run
    engine.cancel_flow_run = lambda run_id, **kw: orig(
        run_id, message=kw.get("message")
    )
    with pytest.raises(RuntimeError, match="Deploy lab"):
        mod.cancel_zpod_runs(7, reason="r", client=engine, timeout=20, poll=5)
