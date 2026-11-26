"""Application events only; a platform adapter will map these to the agreed trace schema."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class AppEvent:
    kind: str
    request_id: str
    details: dict[str, str | bool | int | None]


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
