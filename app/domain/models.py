"""Objetos que representam os dados importantes para o domínio."""

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Address:
    cep: str
    street: str | None
    neighborhood: str | None
    city: str | None
    state: str | None


class IntentAction(str, Enum):
    QUERY_CEP = "QUERY_CEP"
    HELP = "HELP"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class IntentAnalysis:
    action: IntentAction
    cep: str | None = None
    direct_reply: str | None = None


@dataclass(frozen=True)
class IncomingMessage:
    message_id: str
    sender: str
    text: str


@dataclass(frozen=True)
class MessageResult:
    message_id: str
    recipient: str
    status: str
    answer: str | None
