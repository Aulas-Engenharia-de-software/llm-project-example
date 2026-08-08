"""Armazenamento simples para ignorar IDs de mensagem repetidos."""

from threading import Lock


class InMemoryProcessedMessageStore:
    def __init__(self) -> None:
        self._message_ids: set[str] = set()
        self._lock = Lock()

    def mark_if_new(self, message_id: str) -> bool:
        with self._lock:
            if message_id in self._message_ids:
                return False
            self._message_ids.add(message_id)
            return True
