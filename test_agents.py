"""test_agents.py
Unit test template for agents in agents.py.

Run with:
    pytest -q --cov=agents --cov-report=term-missing
"""

import pytest

from agents import DecisionAgent, EchoAgent, Message, MessageBus, RouterAgent


@pytest.fixture()
def bus_and_agents():
    bus = MessageBus()
    echoer = EchoAgent("echoer")
    decider = DecisionAgent("decider")
    router = RouterAgent("router", mapping={"echo.": "echoer", "score": "decider"})
    for a in (echoer, decider, router):
        bus.register(a)
        a.on_start()
    return bus, echoer, decider, router


# ---------- EchoAgent ----------


def test_echo_agent_replies_with_same_payload(bus_and_agents):
    bus, echoer, decider, router = bus_and_agents
    msg = Message(sender="tester", recipient="echoer", topic="echo", payload={"x": 1})
    bus.send(msg)
    history = bus.history()
    assert any(m.topic == "echo.reply" and m.recipient == "tester" for m in history)


def test_echo_agent_ignores_non_echo_topics(bus_and_agents):
    bus, echoer, *_ = bus_and_agents
    before = len(bus.history())
    bus.send(Message(sender="tester", recipient="echoer", topic="not-echo", payload={}))
    after = len(bus.history())
    assert (after - before) == 1


# ---------- DecisionAgent ----------


@pytest.mark.parametrize(
    "value,threshold,accepted",
    [
        (0.9, 0.5, True),
        (0.1, 0.5, False),
        (5, 5, True),
    ],
)
def test_decision_agent_threshold_logic(bus_and_agents, value, threshold, accepted):
    bus, _, decider, _ = bus_and_agents
    bus.send(
        Message(
            sender="tester",
            recipient="decider",
            topic="score",
            payload={"value": value, "threshold": threshold},
        )
    )
    decision_msgs = [
        m for m in bus.history() if m.topic == "decision" and m.recipient == "tester"
    ]
    assert decision_msgs, "Expected a decision reply"
    assert decision_msgs[-1].payload["accepted"] is accepted


def test_decision_agent_handles_invalid_value(bus_and_agents):
    bus, _, decider, _ = bus_and_agents
    bus.send(
        Message(
            sender="tester",
            recipient="decider",
            topic="score",
            payload={"value": "NaN"},
        )
    )
    replies = [
        m for m in bus.history() if m.topic == "decision" and m.recipient == "tester"
    ]
    assert replies[-1].payload.get("error") == "invalid_value"


# ---------- RouterAgent ----------


def test_router_forwards_by_topic_prefix(bus_and_agents):
    bus, echoer, decider, router = bus_and_agents
    router.send(recipient=None, topic="echo.hello", payload={"txt": "hi"})
    assert any(m.topic == "echo.reply" for m in bus.history())


def test_router_exact_match_for_score(bus_and_agents):
    bus, echoer, decider, router = bus_and_agents
    router.send(recipient=None, topic="score", payload={"value": 1.0, "threshold": 2.0})
    assert any(m.topic == "decision" for m in bus.history())


# ---------- Edge cases & utilities ----------


def test_agent_requires_nonempty_name():
    with pytest.raises(ValueError):
        EchoAgent("")


def test_message_bus_register_duplicate_name():
    bus = MessageBus()
    a1 = EchoAgent("dup")
    a2 = EchoAgent("dup")
    bus.register(a1)
    with pytest.raises(ValueError):
        bus.register(a2)
