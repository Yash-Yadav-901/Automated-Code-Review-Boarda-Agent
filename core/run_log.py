import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "audit_run_log.jsonl"


class RunLogger:
    """
    Append-only persistent run logger that records every multi-agent interaction,
    tool call, state transition, and final decision for auditability.
    """
    def __init__(self, log_path: Path = LOG_FILE):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append_entry(
        self,
        event_type: str,
        diff_id: str,
        agent_name: str,
        data: Dict[str, Any],
        level: str = "INFO"
    ) -> None:
        """Write an append-only timestamped JSON entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event_type": event_type,
            "diff_id": diff_id,
            "agent": agent_name,
            "data": data,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read_all_entries(self) -> list[Dict[str, Any]]:
        """Read all historical entries from the log."""
        if not self.log_path.exists():
            return []
        entries = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        return entries


# Default global logger instance
audit_logger = RunLogger()
