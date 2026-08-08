from app.application.services import AnswerQuestionService, HandleIncomingMessageService
from app.domain.models import Address, IncomingMessage, IntentAction, IntentAnalysis


class FakeLanguageModel:
    def __init__(self, analysis: IntentAnalysis) -> None:
        self.analysis = analysis
        self.composed_with: tuple[str, Address] | None = None

    def analyze(self, _: str) -> IntentAnalysis:
        return self.analysis

    def compose_address_response(self, question: str, address: Address) -> str:
        self.composed_with = (question, address)
        return "Esse CEP fica no Centro de Cascavel, no Paraná."


class FakeAddressLookup:
    def __init__(self, address: Address | None) -> None:
        self.address = address
        self.cep_received: str | None = None

    def find_by_cep(self, cep: str) -> Address | None:
        self.cep_received = cep
        return self.address


class MemoryStore:
    def __init__(self) -> None:
        self.ids: set[str] = set()

    def mark_if_new(self, message_id: str) -> bool:
        if message_id in self.ids:
            return False
        self.ids.add(message_id)
        return True


def test_queries_external_api_and_asks_model_to_compose_answer() -> None:
    address = Address("85801-000", "Rua Paraná", "Centro", "Cascavel", "PR")
    model = FakeLanguageModel(IntentAnalysis(IntentAction.QUERY_CEP, "85801-000"))
    lookup = FakeAddressLookup(address)
    service = AnswerQuestionService(model, lookup)

    answer = service.answer("Onde fica o CEP 85801-000?")

    assert "Cascavel" in answer
    assert lookup.cep_received == "85801000"
    assert model.composed_with == ("Onde fica o CEP 85801-000?", address)


def test_rejects_invalid_cep_before_external_api() -> None:
    model = FakeLanguageModel(IntentAnalysis(IntentAction.QUERY_CEP, "123"))
    lookup = FakeAddressLookup(None)

    answer = AnswerQuestionService(model, lookup).answer("Meu CEP é 123")

    assert "8 números" in answer
    assert lookup.cep_received is None


def test_returns_model_help_reply() -> None:
    model = FakeLanguageModel(
        IntentAnalysis(IntentAction.HELP, direct_reply="Olá! Eu consulto endereços por CEP.")
    )

    answer = AnswerQuestionService(model, FakeAddressLookup(None)).answer("Olá")

    assert answer == "Olá! Eu consulto endereços por CEP."


def test_ignores_duplicate_message_id() -> None:
    model = FakeLanguageModel(
        IntentAnalysis(IntentAction.HELP, direct_reply="Posso ajudar com um CEP.")
    )
    handler = HandleIncomingMessageService(
        AnswerQuestionService(model, FakeAddressLookup(None)), MemoryStore()
    )
    message = IncomingMessage("msg-1", "aluno-1", "Olá")

    first = handler.handle(message)
    duplicate = handler.handle(message)

    assert first.status == "processed"
    assert first.answer == "Posso ajudar com um CEP."
    assert duplicate.status == "duplicate"
    assert duplicate.answer is None
