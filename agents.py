"""agents.py
Implémentations de base pour un système multi-agent simple utilisé dans le laboratoire
'Design et Validation des Suites de Tests pour un Système Multi-Agent IA'.

Cette version inclut EchoAgent, DecisionAgent et RouterAgent pour les tests.
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
    recipient: Optional[str] = None  # Explicite "None" pour diffusion générale
    topic: str
    payload: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    """Message encapsulant une communication entre agents.
    Contient :
        - `sender` : Nom de l'agent émetteur (str).
        - `recipient` : Cible spécifique (None pour diffusion générale).
        - `topic` : Sujet de la conversation (ex: "echo", "score").
        - `payload` : Données structurées à transmettre.
        - `meta` : Métadonnées optionnelles (ex: timestamp, priorité).
    """

class MessageBus:
    """Un bus de messages minimal en mémoire, centralisant les échanges entre agents."""

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}
        self._history: List[Message] = []



    def register(self, callback: Callable[..., Any], event_type: str) -> None:
        """Enregistre une fonction de rappel pour un type d'événement spécifique.

        Args:
            callback (Callable[..., Any]): La fonction à appeler lors de la réception de l'événement.
                Doit correspondre à la structure attendue du payload de l'événement.
            event_type (str): Le nom/type de l'événement auquel s'abonner.

        Returns:
            None

        Raises:
            ValueError: Si le callback est invalide ou déjà enregistré.
        """
        if agent.name in self._agents:
            raise ValueError(f"Nom de l'agent déjà enregistré : {agent.name}")
        self._agents[agent.name] = agent
        agent._bus = self

    def send(self, event_type: str, payload: Any) -> None:
        """Envoie un événement avec son payload aux abonnés correspondants.

        Args:
            event_type (str): Le nom/type de l'événement à envoyer.
            payload (Any): Les données associées à l'événement (structure variable).

        Returns:
            None

        Raises:
            KeyError: Si le type d'événement n'est pas enregistré.
            TypeError: Si le payload ne correspond pas aux attentes du callback.
        """
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
            raise ValueError("Le nom de l'agent doit être une chaîne non vide")def register(self, callback: Callable[..., Any], event_type: str) -> None:
    """Enregistre une fonction de rappel pour un type d'événement spécifique.

    Args:
        callback (Callable[..., Any]): La fonction à appeler lors de la réception de l'événement.
            Doit correspondre à la structure attendue du payload de l'événement.
        event_type (str): Le nom/type de l'événement auquel s'abonner.

    Returns:
        None

    Raises:
        ValueError: Si le callback est invalide ou déjà enregistré.
    """

    def send(self, event_type: str, payload: Any) -> None:
        """Envoie un événement avec son payload aux abonnés correspondants.

        Args:
            event_type (str): Le nom/type de l'événement à envoyer.
            payload (Any): Les données associées à l'événement (structure variable).

        Returns:
            None

        Raises:
            KeyError: Si le type d'événement n'est pas enregistré.
            TypeError: Si le payload ne correspond pas aux attentes du callback.
        """
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
        """Traitement des messages correspondant aux sujets 'echo' ou commençant par 'echo.'

        Pour les messages de type écho (exactement "echo" ou commençant par "echo."), ce message est renvoyé au destinataire original sous le sujet "echo.reply".
        Le contenu original du message est encapsulé dans une structure de payload avec la clé "echo".

        Args:
            msg (Message): Objet Message contenant :
                - `msg.topic`: Sujet du message qui doit être exactement "echo" ou commencer par "echo."
                - `msg.sender`: Identifiant du destinataire initial
                - `msg.payload`: Contenu original du message

        Remarques:
            Les messages non de type écho sont ignorés (actuellement loggés à la console)
            Ce traitement est une implémentation basique de fonctionnalité d'écho pour le système de messagerie.
        """
        if msg.topic == "echo" or msg.topic.startswith("echo."):
            self.send(
                recipient=self.get_coordination().player_id,  # Utilise l'ID du joueur via coordination
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
    """Routeur qui redirige les messages vers des agents spécifiques selon leur préfixe.
    Exemple de mapping : {"echo.request": "agent1", "score.update": "decision"}."""
    def __init__(self, name: str, mapping: Dict[str, str]) -> None:
        super().__init__(name)
        self.mapping = dict(mapping)

    def handle(self, msg: Message) -> None:
        """Route le message vers un agent cible si son préfixe correspond à une clé du mapping.
        Exemple : Si `topic="echo.request"` et le mapping contient "echo.request" → redirige vers l'agent spécifié."""
        if msg.sender == self.name or msg.topic.endswith(".reply"):
            return
        target = None
        for key, agent_name in self.mapping.items():
                if msg.topic.startswith(key):
                    target = agent_name
                    break
        if target:
            self.send(recipient=target, topic=msg.topic, payload=msg.payload)

