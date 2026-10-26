"""Deterministic, explicit-label baseline; no model or network calls."""
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def tokens(text):
    # Latin words and individual CJK characters: intentionally simple baseline.
    return set(re.findall(r"[a-z0-9_]+|[\u3400-\u9fff]", text.lower()))


class Memory:
    def __init__(self, path="mewmory.db"):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY, occurred_at TEXT NOT NULL,
            actor TEXT NOT NULL, place TEXT NOT NULL, cue TEXT NOT NULL,
            outcome TEXT NOT NULL, text TEXT NOT NULL)""")
        self.db.commit()

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def add(self, *, actor, place, cue, outcome, text, occurred_at=None):
        values = [actor, place, cue, outcome, text]
        if any(not isinstance(v, str) or not v.strip() for v in values):
            raise ValueError("actor, place, cue, outcome and text must be nonempty strings")
        if occurred_at is None:
            occurred_at = datetime.now(timezone.utc).isoformat()
        else:
            timestamp = datetime.fromisoformat(occurred_at)
            if timestamp.tzinfo is None:
                raise ValueError("occurred_at must include a timezone")
            occurred_at = timestamp.astimezone(timezone.utc).isoformat()
        with self.db:
            cursor = self.db.execute(
                "INSERT INTO events (occurred_at,actor,place,cue,outcome,text) VALUES (?,?,?,?,?,?)",
                [occurred_at] + [v.strip() for v in values],
            )
        return cursor.lastrowid

    def events(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM events ORDER BY id")]

    def trace(self, event_ids):
        result = []
        for event_id in dict.fromkeys(event_ids):
            row = self.db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
            if row is None:
                raise KeyError(f"Unknown event ID: {event_id}")
            result.append(dict(row))
        return result

    def rules(self, min_support=2):
        if min_support < 1:
            raise ValueError("min_support must be positive")
        groups = {}
        for event in self.events():
            key = (event["actor"], event["place"], event["cue"])
            groups.setdefault(key, {}).setdefault(event["outcome"], []).append(event["id"])
        result = []
        for (actor, place, cue), outcomes in sorted(groups.items()):
            total = sum(len(ids) for ids in outcomes.values())
            for outcome, ids in sorted(outcomes.items()):
                if len(ids) >= min_support:
                    result.append(dict(actor=actor, place=place, cue=cue, outcome=outcome,
                                       support=len(ids), total=total, frequency=len(ids) / total,
                                       source_ids=ids))
        return result

    def recall(self, query, limit=3, max_chars=2000):
        """Bound serialized context by characters (not a tokenizer-specific token count)."""
        if limit < 1 or max_chars < 2:
            raise ValueError("limit must be positive and max_chars must be at least 2")
        query_tokens = tokens(query)
        candidates = []
        for rule in self.rules():
            searchable = " ".join(rule[key] for key in ("actor", "place", "cue", "outcome"))
            score = len(query_tokens & tokens(searchable))
            if score:
                # Keep full provenance outside the bounded context; resolve via rules/trace.
                item = {key: value for key, value in rule.items() if key != "source_ids"}
                item.update(kind="rule", score=score, source_ids=rule["source_ids"][:3],
                            sources_truncated=len(rule["source_ids"]) > 3)
                candidates.append(item)
        for event in self.events():
            score = len(query_tokens & tokens(" ".join(str(v) for v in event.values())))
            if score:
                candidates.append(dict(kind="event", score=score, source_ids=[event["id"]],
                                       text=event["text"]))
        candidates.sort(key=lambda item: (-item["score"], item["kind"] != "rule", item["source_ids"][0]))
        selected = []
        covered = set()
        for item in candidates:
            if item["kind"] == "event" and item["source_ids"][0] in covered:
                continue
            if len(json.dumps(selected + [item], ensure_ascii=False)) > max_chars:
                continue
            selected.append(item)
            covered.update(item["source_ids"])
            if len(selected) == limit:
                break
        return selected
