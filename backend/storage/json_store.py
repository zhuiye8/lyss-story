import json
from pathlib import Path


class JSONStore:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def _story_dir(self, story_id: str) -> Path:
        d = self.data_dir / story_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_story_bible(self, story_id: str, bible: dict) -> None:
        path = self._story_dir(story_id) / "story_bible.json"
        path.write_text(json.dumps(bible, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_story_bible(self, story_id: str) -> dict | None:
        path = self._story_dir(story_id) / "story_bible.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_event_graph(self, story_id: str, events: list[dict]) -> None:
        path = self._story_dir(story_id) / "event_graph.json"
        path.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_event_graph(self, story_id: str) -> list[dict]:
        path = self._story_dir(story_id) / "event_graph.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def append_events(self, story_id: str, new_events: list[dict]) -> None:
        existing = self.load_event_graph(story_id)
        existing.extend(new_events)
        self.save_event_graph(story_id, existing)

    def save_characters(self, story_id: str, characters: list[dict]) -> None:
        path = self._story_dir(story_id) / "characters.json"
        path.write_text(json.dumps(characters, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_characters(self, story_id: str) -> list[dict]:
        path = self._story_dir(story_id) / "characters.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))
