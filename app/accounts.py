"""
Claude Max rotation — reaproveitado do Zion com ajustes pra Maestro.

State: /root/.claude/maestro_accounts_state.json
Contas salvas em: /root/.claude-accounts/<slug>/{credentials.json, claude.json}
"""
import json, os, shutil, subprocess, time, logging
from pathlib import Path

log = logging.getLogger("maestro.accounts")

ACCOUNTS_DIR = Path("/root/.claude-accounts")
STATE_PATH = Path("/root/.claude/maestro_accounts_state.json")
LIVE_CREDS = Path("/root/.claude/.credentials.json")
LIVE_CLAUDE_JSON = Path("/root/.claude.json")

DEFAULT_COOLDOWN = 5 * 3600

CAP_PATTERNS = [
    "you've hit your limit",
    "credit balance is too low",
    "rate limit",
    "too many requests",
    "quota exceeded",
    "usage limit reached",
]


def _load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {"active": None, "accounts": {}}


def _save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def is_cap_error(output: str) -> bool:
    low = (output or "").lower()
    return any(p in low for p in CAP_PATTERNS)


def switch_to(slug: str) -> dict:
    target_dir = ACCOUNTS_DIR / slug
    if not target_dir.exists():
        return {"err": f"account '{slug}' não existe"}
    creds_src = target_dir / "credentials.json"
    if not creds_src.exists():
        return {"err": f"credentials.json faltando em {target_dir}"}

    LIVE_CREDS.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(creds_src, LIVE_CREDS)
    os.chmod(LIVE_CREDS, 0o600)

    json_src = target_dir / "claude.json"
    if json_src.exists():
        shutil.copy2(json_src, LIVE_CLAUDE_JSON)
        os.chmod(LIVE_CLAUDE_JSON, 0o600)

    state = _load_state()
    state["active"] = slug
    _save_state(state)
    log.info(f"[accounts] switched → {slug}")
    return {"ok": True, "active": slug}


def mark_cooldown(slug: str, seconds: int = DEFAULT_COOLDOWN):
    state = _load_state()
    if slug not in state["accounts"]:
        state["accounts"][slug] = {"email": "?", "cooldown_until": 0}
    state["accounts"][slug]["cooldown_until"] = int(time.time()) + seconds
    _save_state(state)


def next_available() -> str:
    state = _load_state()
    now = int(time.time())
    for slug, info in state["accounts"].items():
        if info.get("cooldown_until", 0) < now:
            return slug
    return None


def status() -> str:
    state = _load_state()
    now = int(time.time())
    lines = ["*Claude Pool*"]
    active = state.get("active")
    if not state["accounts"]:
        return "Nenhuma conta cadastrada. Copiar de /root/.claude-accounts/ manualmente."
    for slug, info in state["accounts"].items():
        cd = info.get("cooldown_until", 0)
        email = info.get("email", "?")
        marker = "▶️" if slug == active else "  "
        if cd > now:
            mins_left = int((cd - now) / 60)
            lines.append(f"{marker} *{slug}* 🔴 {mins_left}min · {email}")
        else:
            lines.append(f"{marker} *{slug}* 🟢 · {email}")
    return "\n".join(lines)


def ask_claude(prompt: str, timeout: int = 120, _depth: int = 0) -> str:
    """Chama Claude CLI, detecta cap, rotaciona, retry."""
    state = _load_state()
    num_accounts = len(state.get("accounts", {})) or 1
    if _depth >= num_accounts:
        return "[todas contas em cooldown]"

    try:
        r = subprocess.run(
            ["/usr/local/bin/claude", "-p", prompt],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "HOME": "/root"},
            stdin=subprocess.DEVNULL,
        )
        out = (r.stdout or "").strip() or (r.stderr or "").strip() or "[sem resposta]"

        if is_cap_error(out):
            active = state.get("active")
            if active:
                mark_cooldown(active)
                log.warning(f"[accounts] {active} cap — cooldown 5h")
            nxt = next_available()
            if nxt and nxt != active:
                switch_to(nxt)
                return ask_claude(prompt, timeout, _depth + 1)
            return out
        return out
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:
        log.error(f"[ask_claude] {e}")
        return f"[erro: {e}]"
