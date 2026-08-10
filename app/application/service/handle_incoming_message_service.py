from app.application.service.handle_question_service import AnswerQuestionService
from app.domain.models import IncomingMessage, MessageResult
from app.domain.ports import ProcessedMessageStore


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
