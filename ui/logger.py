import json
import time
from pathlib import Path


class RunLogger:
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.events = []

    def log(self, event_type: str, payload: dict):
        self.events.append(
            {
                "time": time.time(),
                "event_type": event_type,
                "payload": payload,
            }
        )

    def save(self, filename: str = "run_log.json") -> Path:
        path = self.log_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.events, f, indent=2, ensure_ascii=False)
        return path

