from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(frozen=True)
class AuditEvent:
    ts_utc: str
    level: str
    run_id: str
    stage: str
    event: str
    message: str
    elapsed_ms: int | None = None
    record_id: str | None = None
    rule_id: str | None = None
    reason: str | None = None
    extra: dict[str, Any] | None = None


class AuditLogger:
    def __init__(self, out_path: Path) -> None:
        self.out_path = out_path
        self.out_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, ev: AuditEvent) -> None:
        line = json.dumps(asdict(ev), ensure_ascii=False)
        with self.out_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


class StageTimer:
    def __init__(self) -> None:
        self._t0 = time.perf_counter()

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._t0) * 1000)
