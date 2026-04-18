"""Extrator de metadata pra tasks — usa Claude pra inferir assignee/due/priority."""
import json, re
from datetime import datetime, timedelta, timezone
from accounts import ask_claude
from clickup_adapter import resolve_assignee, MEMBERS_ALLIN


def _build_prompt(title: str, raw_desc: str, transcript: str, analysis: str) -> str:
    executores = sorted({k for k in MEMBERS_ALLIN.keys() if " " not in k})
    now = datetime.now(timezone(timedelta(hours=-3)))
    today = now.strftime("%Y-%m-%d %H:%M")
    weekday = now.strftime("%A")

    return f"""Analise o contexto e extraia metadata pra task ClickUp da ALL IN / Case.

CONTEXTO:
- Hoje: {today} ({weekday}) BRT
- Team: ALL IN / Case (empresa Queila)
- Executores: {", ".join(executores)}

TASK:
Título: {title}
Descrição direta: {raw_desc[:500]}

TRANSCRIÇÃO: {transcript[:1500]}
ANÁLISE: {analysis[:800]}

EXTRAIA (responda SÓ JSON válido):
{{
  "due_date": "YYYY-MM-DD" ou null,
  "start_date": "YYYY-MM-DD" ou null,
  "assignee": "nome" ou null,
  "priority": 1-4 ou null,
  "confidence": {{"due_date": 0-1, "assignee": 0-1, "priority": 0-1}},
  "reasoning": "1 frase"
}}

REGRAS DURAS:
1. "assignee" SÓ da lista de executores acima. Nome não bate exato → null.
2. Datas ABSOLUTAS (resolva "sexta", "amanhã").
3. Priority: 1=urgente, 2=alta, 3=normal, 4=baixa. null se não der pra inferir.
4. Confidence < 0.6 → null (melhor vazio que errado).
"""


def _parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {"err": "no_json"}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return {"err": str(e)}


def _date_to_ts_ms(date_str: str, end_of_day: bool = False) -> int:
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59)
        dt = dt.replace(tzinfo=timezone(timedelta(hours=-3)))
        return int(dt.timestamp() * 1000)
    except Exception:
        return None


def extract(title: str, raw_desc: str = "", transcript: str = "",
            analysis: str = "") -> dict:
    """Retorna dict com campos prontos pra ClickUp update_task."""
    prompt = _build_prompt(title, raw_desc, transcript, analysis)
    response = ask_claude(prompt, timeout=60)
    parsed = _parse_json(response)

    if "err" in parsed:
        return {"assignees": [], "due_date": None, "start_date": None,
                "priority": None, "_err": parsed["err"]}

    assignee_id = resolve_assignee(parsed.get("assignee") or "")
    due_ts = _date_to_ts_ms(parsed.get("due_date"), end_of_day=True)
    start_ts = _date_to_ts_ms(parsed.get("start_date"), end_of_day=False)
    priority = parsed.get("priority") if parsed.get("priority") in (1,2,3,4) else None

    return {
        "assignees": [assignee_id] if assignee_id else [],
        "due_date": due_ts,
        "start_date": start_ts,
        "priority": priority,
        "_raw": parsed,
    }


def format_summary(metadata: dict) -> str:
    raw = metadata.get("_raw", {})
    lines = []
    lines.append(f"👤 *Responsável:* {raw.get('assignee') or '—'}")
    lines.append(f"📅 *Prazo:* {raw.get('due_date') or '—'}")
    p_map = {1: "🔴 urgente", 2: "🟠 alta", 3: "🟡 normal", 4: "⚪ baixa"}
    lines.append(f"⚡ *Prioridade:* {p_map.get(raw.get('priority'), '—')}")
    if raw.get("reasoning"):
        lines.append(f"\n_{raw['reasoning']}_")
    return "\n".join(lines)
