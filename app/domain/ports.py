"""Portas que isolam a regra de negócio dos detalhes de infraestrutura."""

from typing import Protocol

from app.domain.models import Address, IntentAnalysis


class AddressLookupPort(Protocol):
    def find_by_cep(self, cep: str) -> Address | None: ...


class LanguageModelPort(Protocol):
    def analyze(self, user_message: str) -> IntentAnalysis: ...

    def compose_address_response(
        self, original_message: str, address: Address
    ) -> str: ...


class ProcessedMessageStore(Protocol):
    def mark_if_new(self, message_id: str) -> bool: ...
