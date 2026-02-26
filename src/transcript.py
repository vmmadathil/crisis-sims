"""Records and exports simulation transcripts."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field, asdict


@dataclass
class Message:
    role: str  # "briefing" | model label ("Claude", "Gemini", "GPT")
    model_id: Optional[str]  # None for briefings
    content: str
    turn: int
    turn_title: str
    thinking: Optional[str] = None  # internal reasoning trace (not shown to other models)


@dataclass
class Transcript:
    scenario_name: str
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    models: List[str] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)

    def add_briefing(self, content: str, turn: int, turn_title: str):
        self.messages.append(Message(
            role="briefing",
            model_id=None,
            content=content,
            turn=turn,
            turn_title=turn_title,
        ))

    def add_response(
        self,
        model_label: str,
        model_id: str,
        content: str,
        turn: int,
        turn_title: str,
        thinking: Optional[str] = None,
    ):
        self.messages.append(Message(
            role=model_label,
            model_id=model_id,
            content=content,
            turn=turn,
            turn_title=turn_title,
            thinking=thinking,
        ))

    def save(self, output_dir: str = "transcripts") -> Path:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = self.scenario_name.lower().replace(" ", "_")
        filename = path / f"{slug}_{timestamp}.json"

        data = {
            "scenario_name": self.scenario_name,
            "started_at": self.started_at,
            "models": self.models,
            "messages": [asdict(m) for m in self.messages],
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        return filename
