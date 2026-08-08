import asyncio

from fastapi import FastAPI
import httpx

from app.api import router
from app.domain.models import IncomingMessage, MessageResult


class FakeMessageHandler:
    def __init__(self) -> None:
        self.received: IncomingMessage | None = None

    def handle(self, message: IncomingMessage) -> MessageResult:
        self.received = message
        return MessageResult(
            message_id=message.message_id,
            recipient=message.sender,
            status="processed",
            answer="Resposta simulada.",
        )


def test_http_endpoint_simulates_incoming_message() -> None:
    handler = FakeMessageHandler()
    app = FastAPI()
    app.state.message_handler = handler
    app.include_router(router)

    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.post(
                "/api/messages",
                json={
                    "message_id": "msg-001",
                    "sender": "aluno-01",
                    "text": "Onde fica o CEP 85801-000?",
                },
            )

    response = asyncio.run(send_request())

    assert response.status_code == 200
    assert response.json() == {
        "message_id": "msg-001",
        "recipient": "aluno-01",
        "status": "processed",
        "answer": "Resposta simulada.",
    }
    assert handler.received == IncomingMessage(
        "msg-001", "aluno-01", "Onde fica o CEP 85801-000?"
    )
