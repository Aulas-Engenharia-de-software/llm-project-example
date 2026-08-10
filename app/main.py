"""Ponto de entrada e composição das dependências da aplicação."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.adapters.gemini import GeminiAdapter
from app.adapters.memory import InMemoryProcessedMessageStore
from app.adapters.viacep import ViaCepAdapter
from app.api import router
from app.application.service.handle_incoming_message_service import HandleIncomingMessageService
from app.application.service.handle_question_service import (
    AnswerQuestionService
)
from app.config import Settings


def create_app() -> FastAPI:
    settings = Settings.from_env()
    gemini = GeminiAdapter(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.http_timeout_seconds,
    )
    viacep = ViaCepAdapter(timeout_seconds=settings.http_timeout_seconds)
    answer_service = AnswerQuestionService(gemini, viacep)
    message_handler = HandleIncomingMessageService(
        answer_service, InMemoryProcessedMessageStore()
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        gemini.close()
        viacep.close()

    application = FastAPI(
        title="Assistente de CEP",
        description="API didática que simula mensagens, consulta o ViaCEP e usa Gemini.",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.state.message_handler = message_handler
    application.include_router(router)
    return application


app = create_app()
