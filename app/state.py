"""
State per-user + journal log.

Cada membro do time tem seu próprio arquivo state em /data/state/<jid>.json.
Journal global em /data/journal.jsonl (append-only, fingerprint Pedro).
"""
import json, os, time
from config import STATE_DIR, JOURNAL_PATH, log


def _path(jid: str) -> str:
    safe = jid.replace("@", "_").replace(":", "_")
    return f"{STATE_DIR}/{safe}.json"


def load(jid: str) -> dict:
    try:
        with open(_path(jid)) as f:
            return json.load(f)
    except Exception:
        return {}


def save(jid: str, data: dict):
    data["updated_at"] = int(time.time())
    try:
        with open(_path(jid), "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"[state save err {jid[:20]}] {e}")


def clear(jid: str):
    try:
        os.remove(_path(jid))
    except Exception:
        pass


def journal(event: dict):
    """Append entry in journal (irremediável — Pedro)."""
    event["ts"] = int(time.time())
    try:
        with open(JOURNAL_PATH, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning(f"[journal err] {e}")
