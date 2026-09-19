"""Authorized access-log tail helpers (file-position based).

Requires explicit user authorization in GUI before use. Does not open
network sockets or contribute data.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class LogTailConfig:
    path: Path
    poll_interval_s: float = 0.25
    start_at_end: bool = True
    encoding: str = "utf-8"

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        if self.poll_interval_s <= 0:
            raise ValueError("poll_interval_s must be positive")


def tail_new_lines(config: LogTailConfig, *, stop_after: float | None = None) -> Iterator[str]:
    """Yield newly appended lines from an authorized log file.

    ``stop_after`` is seconds of wall time (useful for tests). When None,
    the iterator runs until the caller stops iterating.
    """
    path = config.path
    if not path.exists():
        raise FileNotFoundError(f"Log path does not exist: {path}")

    deadline = None if stop_after is None else (time.monotonic() + stop_after)
    with path.open("r", encoding=config.encoding, errors="replace") as handle:
        if config.start_at_end:
            handle.seek(0, 2)
        buffer = ""
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                return
            chunk = handle.read()
            if chunk:
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    yield line.rstrip("\r")
            else:
                time.sleep(config.poll_interval_s)
