"""Adaptador para a API pública ViaCEP."""

import httpx

from app.domain.models import Address


class ViaCepAdapter:
    def __init__(
        self,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url="https://viacep.com.br", timeout=timeout_seconds
        )

    def find_by_cep(self, cep: str) -> Address | None:
        try:
            response = self._client.get(f"/ws/{cep}/json/")
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("Falha ao consultar o ViaCEP") from exc

        if data.get("erro") is True:
            return None

        return Address(
            cep=data.get("cep", cep),
            street=data.get("logradouro"),
            neighborhood=data.get("bairro"),
            city=data.get("localidade"),
            state=data.get("uf"),
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
