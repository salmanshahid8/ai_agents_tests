"""agents.py
Implémentations de base pour un système multi-agent simple utilisé dans le laboratoire
'Design et Validation des Suites de Tests pour un Système Multi-Agent IA'.

Cette version inclut EchoAgent et DecisionAgent pour les tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# --------------------------
# Primitives de Messagerie
# --------------------------

@dataclass
class Message:
    sender: str
    recipient: Optional[str]  # None signifie diffusion générale
    topic: str
    payload: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

class MessageBus:
    """Un bus de messages minimal en mémoire."""
    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}
        self._history: List[Message] = []

    def register(self, agent: "BaseAgent") -> None:
        if agent.name in self._agents:
            raise ValueError(f"Nom de l'agent déjà enregistré : {agent.name}")
        self._agents[agent.name] = agent
        agent._bus = self

    def send(self, msg: Message) -> None:
        self._history.append(msg)
        if msg.recipient:
            agent = self._agents.get(msg.recipient)
            if agent:
                agent.receive(msg)
        else:
            for agent in self._agents.values():
                agent.receive(msg)

    def history(self) -> List[Message]:
        return list(self._history)

# --------------------------
# Agent de Base
# --------------------------

class BaseAgent:
    def __init__(self, name: str) -> None:
        if not name or not name.strip():
            raise ValueError("Le nom de l'agent doit être une chaîne non vide")
        self.name = name
        self._bus: Optional[MessageBus] = None
        self._inbox: List[Message] = []

    def on_start(self) -> None:
        """Hook appelé après la registration (inscription)."""
        pass

    def send(
        self, recipient: Optional[str], topic: str, payload: Dict[str, Any]
    ) -> None:
        if not self._bus:
            raise RuntimeError("L'agent n'est pas enregistré sur un MessageBus")
        msg = Message(
            sender=self.name,
            recipient=recipient,
            topic=topic,
            payload=payload
        )
        self._bus.send(msg)

    def receive(self, msg: Message) -> None:
        """Comportement par défaut : enfile et appelle handle()."""
        self._inbox.append(msg)
        self.handle(msg)

    def handle(self, msg: Message) -> None:
        """Remplacer par une logique spécifique à l'agent."""
        pass

    @property
    def inbox(self) -> List[Message]:
        return list(self._inbox)

# --------------------------
# EchoAgent
# --------------------------

class EchoAgent(BaseAgent):
    """Répond aux messages en renvoyant ceux qui concernent le sujet 'echo' ou commencent par 'echo.'"""
    def handle(self, msg: Message) -> None:
        if msg.topic == "echo" or msg.topic.startswith("echo."):
            self.send(
                recipient=msg.sender,
                topic="echo.reply",
                payload={"echo": msg.payload}
            )

# --------------------------
# DecisionAgent
# --------------------------

class DecisionAgent(BaseAgent):
    """Fait des décisions simples basées sur une note numérique."""
    def handle(self, msg: Message) -> None:
        if msg.topic == "score":
            value = msg.payload.get("value")
            threshold = msg.payload.get("threshold", 0)
            if not isinstance(value, (int, float)):
                self.send(msg.sender, "decision", {"error": "invalid_value"})
                return
            accepted = value >= threshold
            self.send(
                msg.sender,
                "decision",
                {"accepted": accepted, "value": value, "threshold": threshold},
            )

# --------------------------
# RouterAgent
# --------------------------

class RouterAgent(BaseAgent):
    """Route les messages selon des préfixes de sujets."""

    def __init__(self, name: str, mapping: Dict[str, str]) -> None:
        super().__init__(name)
        self.mapping = dict(mapping)

    def handle(self, msg: Message) -> None:
        if msg.sender == self.name:
            return
        if msg.topic.endswith(".reply"):
            return

        target = None
        for key, agent_name in self.mapping.items():
            if key.endswith("."):
                if msg.topic.startswith(key):
                    target = agent_name
                    break
            else:
                if msg.topic == key:
                    target = agent_name
                    break
        if target:
            self.send(recipient=target, topic=msg.topic, payload=msg.payload)

