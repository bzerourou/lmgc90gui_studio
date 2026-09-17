"""Application journal — in-memory ring buffer + optional file sink."""
from __future__ import annotations

import logging
import threading
import traceback
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Deque, List, Optional


@dataclass
class JournalEntry:
    level: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S.%f")[:-3])
    detail: str = ""

    def format(self) -> str:
        base = f"[{self.timestamp}] {self.level:7} {self.message}"
        if self.detail:
            return base + "\n" + self.detail
        return base


class AppJournal:
    """Singleton-ish journal shared by controller and dialogs."""

    def __init__(self, maxlen: int = 2000):
        self._entries: Deque[JournalEntry] = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._listeners: List[Callable[[JournalEntry], None]] = []
        self._file: Optional[Path] = None

    def set_file(self, path: Optional[Path]) -> None:
        self._file = Path(path) if path else None

    def subscribe(self, callback: Callable[[JournalEntry], None]) -> None:
        self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[JournalEntry], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def log(self, level: str, message: str, detail: str = "") -> JournalEntry:
        entry = JournalEntry(level=level.upper(), message=str(message), detail=detail or "")
        with self._lock:
            self._entries.append(entry)
            if self._file is not None:
                try:
                    with open(self._file, "a", encoding="utf-8") as fh:
                        fh.write(entry.format() + "\n")
                except OSError:
                    pass
        for cb in list(self._listeners):
            try:
                cb(entry)
            except Exception:
                pass
        return entry

    def info(self, msg: str, detail: str = "") -> None:
        self.log("INFO", msg, detail)

    def warning(self, msg: str, detail: str = "") -> None:
        self.log("WARNING", msg, detail)

    def error(self, msg: str, detail: str = "") -> None:
        self.log("ERROR", msg, detail)

    def exception(self, msg: str, exc: BaseException | None = None) -> None:
        detail = ""
        if exc is not None:
            detail = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self.log("ERROR", msg, detail)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def entries(self) -> list[JournalEntry]:
        with self._lock:
            return list(self._entries)

    def text(self) -> str:
        return "\n".join(e.format() for e in self.entries())


_JOURNAL: Optional[AppJournal] = None


def get_journal() -> AppJournal:
    global _JOURNAL
    if _JOURNAL is None:
        _JOURNAL = AppJournal()
    return _JOURNAL
