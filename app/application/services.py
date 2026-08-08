"""Casos de uso: responder uma pergunta e tratar uma mensagem recebida."""

import re

from app.domain.models import IncomingMessage, IntentAction, MessageResult
from app.domain.ports import AddressLookupPort, LanguageModelPort, ProcessedMessageStore


class AnswerQuestionService:
    MAX_INPUT_LENGTH = 1_000
    MAX_OUTPUT_LENGTH = 3_500

    def __init__(
        self,
        language_model: LanguageModelPort,
        address_lookup: AddressLookupPort,
    ) -> None:
        self._language_model = language_model
        self._address_lookup = address_lookup

    def answer(self, question: str | None) -> str:
        safe_question = self._normalize(question)
        analysis = self._language_model.analyze(safe_question)

        if analysis.action is IntentAction.QUERY_CEP:
            return self._answer_cep(safe_question, analysis.cep)
        if analysis.action is IntentAction.HELP:
            return self._fallback(
                analysis.direct_reply,
                "Posso consultar um CEP brasileiro. Por exemplo: onde fica o CEP 85801-000?",
            )
        return self._fallback(
            analysis.direct_reply,
            "Neste exemplo eu consigo apenas consultar endereços a partir de um CEP brasileiro.",
        )

    def _answer_cep(self, original_question: str, raw_cep: str | None) -> str:
        cep = re.sub(r"\D", "", raw_cep or "")
        if not re.fullmatch(r"\d{8}", cep):
            return (
                "Não consegui identificar um CEP válido. "
                "Envie exatamente 8 números, com ou sem hífen."
            )

        address = self._address_lookup.find_by_cep(cep)
        if address is None:
            return (
                "Não encontrei um endereço para o CEP informado. "
                "Confira os números e tente novamente."
            )

        response = self._language_model.compose_address_response(
            original_question, address
        )
        return self._limit_output(response)

    def _normalize(self, question: str | None) -> str:
        normalized = (question or "").strip() or "ajuda"
        return normalized[: self.MAX_INPUT_LENGTH]

    def _fallback(self, model_reply: str | None, default_reply: str) -> str:
        if not model_reply or not model_reply.strip():
            return default_reply
        return self._limit_output(model_reply)

    def _limit_output(self, text: str | None) -> str:
        if not text or not text.strip():
            return "Não consegui montar a resposta agora. Tente novamente em instantes."
        return text.strip()[: self.MAX_OUTPUT_LENGTH]


class HandleIncomingMessageService:
    def __init__(
        self,
        answer_question: AnswerQuestionService,
        processed_messages: ProcessedMessageStore,
    ) -> None:
        self._answer_question = answer_question
        self._processed_messages = processed_messages

    def handle(self, message: IncomingMessage) -> MessageResult:
        if not self._processed_messages.mark_if_new(message.message_id):
            return MessageResult(
                message_id=message.message_id,
                recipient=message.sender,
                status="duplicate",
                answer=None,
            )

        answer = self._answer_question.answer(message.text)
        return MessageResult(
            message_id=message.message_id,
            recipient=message.sender,
            status="processed",
            answer=answer,
        )
