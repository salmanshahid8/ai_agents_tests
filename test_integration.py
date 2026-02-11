"""test_integration.py
Integration test template for end-to-end multi-agent interactions.

Focus:
  * message routing through RouterAgent
  * collaboration between EchoAgent and DecisionAgent
  * ensuring bus history records expected flows
"""

import pytest

from agents import DecisionAgent, EchoAgent, MessageBus, RouterAgent


@pytest.fixture()
def system():
    bus = MessageBus()
    echoer = EchoAgent("echoer")
    decider = DecisionAgent("decider")
    router = RouterAgent("router", mapping={"echo.": "echoer", "score": "decider"})
    for a in (echoer, decider, router):
        bus.register(a)
        a.on_start()
    return bus, echoer, decider, router


def test_end_to_end_workflow_echo_and_decision(system):
    bus, echoer, decider, router = system

    # Step 1: client sends an echo via router (broadcast)
    router.send(recipient=None, topic="echo.request", payload={"text": "ping"})
    # Step 2: client sends a scoring request
    router.send(
        recipient=None, topic="score", payload={"value": 0.75, "threshold": 0.5}
    )

    history = bus.history()

    # Verify at least one echo reply was produced
    assert any(m.topic == "echo.reply" for m in history)
    # Verify a decision message exists and is accepted
    decisions = [m for m in history if m.topic == "decision"]
    assert decisions, "Expected a decision message"
    assert decisions[-1].payload.get("accepted") is True


def test_unroutable_message_is_dropped(system):
    bus, echoer, decider, router = system
    before = len(bus.history())
    router.send(recipient=None, topic="unknown.topic", payload={})
    after = len(bus.history())
    # Only the original send should be recorded; no new forwards
    assert (after - before) == 1
