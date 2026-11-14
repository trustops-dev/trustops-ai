"""Local application events; canonical trace serialization is a separate adapter."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class AppEvent:
    kind: str
    query_id: str
    details: dict[str, str | int | None]


class EventSink(Protocol):
    def emit(self, event: AppEvent) -> None: ...


class NullSink:
    def emit(self, event: AppEvent) -> None:
        pass


@dataclass
class RecordingSink:
    events: list[AppEvent] = field(default_factory=list)

    def emit(self, event: AppEvent) -> None:
        self.events.append(event)
