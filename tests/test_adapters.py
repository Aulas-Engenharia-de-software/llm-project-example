import httpx
import pytest

from app.adapters.gemini import GeminiAdapter
from app.adapters.viacep import ViaCepAdapter
from app.domain.models import Address, IntentAction


def test_viacep_maps_external_fields() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/ws/85801000/json/"
        return httpx.Response(
            200,
            json={
                "cep": "85801-000",
                "logradouro": "Rua Paraná",
                "bairro": "Centro",
                "localidade": "Cascavel",
                "uf": "PR",
            },
        )

    client = httpx.Client(
        base_url="https://viacep.com.br", transport=httpx.MockTransport(handler)
    )
    adapter = ViaCepAdapter(client=client)

    assert adapter.find_by_cep("85801000") == Address(
        "85801-000", "Rua Paraná", "Centro", "Cascavel", "PR"
    )


def test_gemini_parses_structured_intent() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "test-key"
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": (
                                        '{"action":"QUERY_CEP","cep":"85801000",'
                                        '"directReply":null}'
                                    )
                                }
                            ]
                        }
                    }
                ]
            },
        )

    client = httpx.Client(
        base_url="https://generativelanguage.googleapis.com",
        transport=httpx.MockTransport(handler),
    )
    adapter = GeminiAdapter("test-key", "test-model", client=client)

    analysis = adapter.analyze("Onde fica o CEP 85801-000?")

    assert analysis.action is IntentAction.QUERY_CEP
    assert analysis.cep == "85801000"


def test_gemini_exposes_safe_upstream_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error": {
                    "message": "API key not valid. Please pass a valid API key."
                }
            },
        )

    client = httpx.Client(
        base_url="https://generativelanguage.googleapis.com",
        transport=httpx.MockTransport(handler),
    )
    adapter = GeminiAdapter("secret-test-key", "test-model", client=client)

    with pytest.raises(RuntimeError, match=r"HTTP 403.*API key not valid"):
        adapter.analyze("Onde fica o CEP 85801-000?")


def test_gemini_never_echoes_key_in_error() -> None:
    api_key = "secret-test-key"

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"message": f"Invalid credential: {api_key}"}},
        )

    client = httpx.Client(
        base_url="https://generativelanguage.googleapis.com",
        transport=httpx.MockTransport(handler),
    )
    adapter = GeminiAdapter(api_key, "test-model", client=client)

    with pytest.raises(RuntimeError) as error:
        adapter.analyze("Olá")

    assert api_key not in str(error.value)
    assert "[chave omitida]" in str(error.value)
