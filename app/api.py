"""Adaptador de entrada HTTP que simula uma mensagem recebida do WhatsApp."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.domain.models import IncomingMessage


router = APIRouter()


class IncomingMessageRequest(BaseModel):
    message_id: str = Field(min_length=1, max_length=200)
    sender: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=1_000)


class MessageResponse(BaseModel):
    message_id: str
    recipient: str
    status: Literal["processed", "duplicate"]
    answer: str | None


@router.post("/api/messages", response_model=MessageResponse)
def receive_message(payload: IncomingMessageRequest, request: Request) -> MessageResponse:
    """Recebe JSON em vez de um webhook real e executa o fluxo completo."""
    message = IncomingMessage(
        message_id=payload.message_id,
        sender=payload.sender,
        text=payload.text,
    )
    try:
        result = request.app.state.message_handler.handle(message)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return MessageResponse(
        message_id=result.message_id,
        recipient=result.recipient,
        status=result.status,
        answer=result.answer,
    )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
