"""/pool — status das contas Claude Max."""
import accounts


def handle(args: str, msg: dict) -> str:
    parts = (args or "").strip().split()
    sub = parts[0].lower() if parts else "status"

    if sub == "reset":
        state = accounts._load_state()
        for slug in state["accounts"]:
            state["accounts"][slug]["cooldown_until"] = 0
        accounts._save_state(state)
        return "✅ Cooldowns limpos"

    if sub == "switch" and len(parts) > 1:
        return str(accounts.switch_to(parts[1]))

    return accounts.status()
