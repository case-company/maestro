"""/sot <mentorada> — resumo contextual da mentorada (lista de tasks recentes)."""
from clickup_adapter import resolve_mentorada, CANONICAL_DISPLAY
import requests
from config import CLICKUP_TOKEN, log


def handle(args: str, msg: dict) -> str:
    slug = args.strip()
    if not slug:
        return "Uso: `/sot <mentorada>` — ex: `/sot jordanna`"

    r = resolve_mentorada(slug)
    if not r:
        return (f"🧭 *{slug}* não encontrada.\n\n"
                "*Mentoradas:*\n" +
                "\n".join(f"• {n}" for n in sorted(CANONICAL_DISPLAY.values())))

    canon, list_id, display = r

    # Busca tasks ativas da mentorada
    try:
        resp = requests.get(
            f"https://api.clickup.com/api/v2/list/{list_id}/task",
            headers={"Authorization": CLICKUP_TOKEN},
            params={"subtasks": "false", "include_closed": "false"},
            timeout=20,
        )
        tasks = resp.json().get("tasks", [])
    except Exception as e:
        return f"Erro buscando tasks: {e}"

    if not tasks:
        return f"📂 *{display}*: nenhuma task ativa"

    lines = [f"📂 *{display}* — {len(tasks)} tasks ativas\n"]
    for t in tasks[:15]:
        status = (t.get("status") or {}).get("status", "?")
        name = t.get("name", "")[:60]
        short = t.get("custom_id") or t.get("id", "")[:6]
        lines.append(f"▸ *{status}* · {name} _#{short}_")

    if len(tasks) > 15:
        lines.append(f"\n_+ {len(tasks)-15} tasks_")

    return "\n".join(lines)
