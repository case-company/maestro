"""
ClickUp adapter — Case/All In schema (team 9011530618).

Schema canônico montado pelo Gobbi:
- 23 mentoradas em folder Mentorados
- 3 sprints ativos em folder Sprint
- Custom fields: trilha, fase_jornada, sub_etapa, estrategista, consultor,
  mentorado_id, BASELINE_*, travado, etc
- Prioridades: 1=urgent, 2=high, 3=normal, 4=low
- Statuses: triage → backlog → ready → in progress → in review → canceled/complete
"""
import requests
from config import CLICKUP_TOKEN, CLICKUP_TEAM_CASE, log

BASE = "https://api.clickup.com/api/v2"


def _h():
    return {"Authorization": CLICKUP_TOKEN, "Content-Type": "application/json"}


# ═══ Mentoradas Case (23) ═══════════════════════════════════════════════════
# canonical_name → list_id (23 listas no folder Mentorados)
MENTORADAS = {
    "amanda-ribeiro":      "901113601831",
    "ana-paula-jordana":   "901113601883",
    "betina-franciosi":    "901113601899",
    "camille-braganca":    "901113600549",
    "caroline-bittencourt":"901113601850",
    "daniela-morais":      "901113601960",
    "danielle-ferreira":   "901113602017",
    "danyella-truiz":      "901113601230",
    "debora-cadore":       "901113601995",
    "elina-rocha":         "901113601309",
    "jessica-crespi":      "901113601481",
    "jordanna-diniz":      "901113601084",
    "lediane-lopes":       "901113601563",
    "leticia-ambrosano":   "901113601863",
    "luciene-tamaki":      "901113601793",
    "miriam-alves":        "901113601689",
    "monica-felici":       "901113601628",
    "rosalie-torrelio":    "901113601168",
    "sidney-claudia":      "901113601727",
    "tatiana-clementino":  "901113601933",
    "tayslara-belarmino":  "901113601771",
    "thiago-kailer":       "901113600818",
    "vania-de-paula":      "901113601747",
}

# aliases comuns (curto → canonical)
MENTORADA_ALIASES = {
    "amanda":    "amanda-ribeiro",
    "ana":       "ana-paula-jordana",
    "ana-paula": "ana-paula-jordana",
    "betina":    "betina-franciosi",
    "camille":   "camille-braganca",
    "caroline":  "caroline-bittencourt",
    "daniela":   "daniela-morais",
    "danielle":  "danielle-ferreira",
    "danyella":  "danyella-truiz",
    "debora":    "debora-cadore",
    "elina":     "elina-rocha",
    "jessica":   "jessica-crespi",
    "jordanna":  "jordanna-diniz",
    "lediane":   "lediane-lopes",
    "leticia":   "leticia-ambrosano",
    "luciene":   "luciene-tamaki",
    "miriam":    "miriam-alves",
    "monica":    "monica-felici",
    "rosalie":   "rosalie-torrelio",
    "sidney":    "sidney-claudia",
    "claudia":   "sidney-claudia",
    "tatiana":   "tatiana-clementino",
    "tayslara":  "tayslara-belarmino",
    "thiago":    "thiago-kailer",
    "vania":     "vania-de-paula",
}

CANONICAL_DISPLAY = {
    "amanda-ribeiro":      "Amanda Ribeiro",
    "ana-paula-jordana":   "Ana Paula Jordana",
    "betina-franciosi":    "Betina Franciosi",
    "camille-braganca":    "Camille Bragança",
    "caroline-bittencourt":"Caroline Bittencourt",
    "daniela-morais":      "Daniela Morais",
    "danielle-ferreira":   "Danielle Ferreira",
    "danyella-truiz":      "Danyella Truiz",
    "debora-cadore":       "Débora Cadore",
    "elina-rocha":         "Elina Rocha",
    "jessica-crespi":      "Jessica Crespi",
    "jordanna-diniz":      "Jordanna Diniz",
    "lediane-lopes":       "Lediane Lopes",
    "leticia-ambrosano":   "Letícia Ambrosano",
    "luciene-tamaki":      "Luciene Tamaki",
    "miriam-alves":        "Miriam Alves",
    "monica-felici":       "Monica Felici",
    "rosalie-torrelio":    "Rosalie Torrelio",
    "sidney-claudia":      "Sidney e Cláudia",
    "tatiana-clementino":  "Tatiana Clementino",
    "tayslara-belarmino":  "Tayslara Belarmino",
    "thiago-kailer":       "Thiago Kailer",
    "vania-de-paula":      "Vânia de Paula",
}


# ═══ Sprint folder (ops gerais do time) ═════════════════════════════════════
# Atualizar semanalmente se Gobbi criar Sprint 7/8/etc
SPRINTS = {
    "sprint-4": "901113495507",   # 4/6 - 4/12
    "sprint-5": "901113526336",   # 4/13 - 4/19
    "sprint-6": "901113527558",   # 4/20 - 4/26
}

def current_sprint_list_id() -> str:
    """Retorna sprint ativa baseado na data atual (semanal)."""
    from datetime import datetime
    today = datetime.now().date()
    base_start = datetime(2026, 4, 6).date()
    days_since = (today - base_start).days
    if days_since < 0:
        return SPRINTS["sprint-4"]
    sprint_num = 4 + (days_since // 7)
    key = f"sprint-{sprint_num}"
    # Fallback pra última conhecida se passou do range
    return SPRINTS.get(key, SPRINTS["sprint-6"])


# ═══ Members ALL IN (assignee resolution) ═══════════════════════════════════
MEMBERS_ALLIN = {
    "queila": 49138186, "queila trizotti": 49138186,
    "felipe": 230491216, "gobbi": 230491216, "felipe gobbi": 230491216,
    "hugo": 3052145, "hugo nicchio": 3052145,
    "heitor": 3055979, "heitor marim": 3055979,
    "lara": 55097238, "lara santos": 55097238,
    "mariza": 55020965, "mariza ribeiro": 55020965,
    "kaique": 3119587, "kaique rodrigues": 3119587,
}


# ═══ Resolve ═══════════════════════════════════════════════════════════════
def resolve_mentorada(slug_or_name: str):
    """Retorna (canonical_slug, list_id, display_name) ou None."""
    if not slug_or_name:
        return None
    key = slug_or_name.strip().lower()
    # exato
    if key in MENTORADAS:
        return (key, MENTORADAS[key], CANONICAL_DISPLAY[key])
    # alias
    canonical = MENTORADA_ALIASES.get(key)
    if canonical:
        return (canonical, MENTORADAS[canonical], CANONICAL_DISPLAY[canonical])
    # fuzzy: substring
    for alias, canon in MENTORADA_ALIASES.items():
        if key in alias or alias in key:
            return (canon, MENTORADAS[canon], CANONICAL_DISPLAY[canon])
    return None


def resolve_assignee(name: str):
    """Name → user_id. None se não achar."""
    if not name:
        return None
    k = name.strip().lower()
    if k in MEMBERS_ALLIN:
        return MEMBERS_ALLIN[k]
    first = k.split()[0]
    return MEMBERS_ALLIN.get(first)


# ═══ Task operations ═══════════════════════════════════════════════════════
def create_task(list_id: str, name: str, description: str = "",
                tags: list = None, status: str = None,
                assignees: list = None, due_date_ts: int = None,
                priority: int = None) -> dict:
    payload = {"name": name}
    if description: payload["description"] = description
    if tags: payload["tags"] = tags
    if status: payload["status"] = status
    if assignees: payload["assignees"] = assignees
    if due_date_ts: payload["due_date"] = due_date_ts
    if priority: payload["priority"] = priority
    r = requests.post(f"{BASE}/list/{list_id}/task", headers=_h(), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def update_task(task_id: str, **fields) -> dict:
    r = requests.put(f"{BASE}/task/{task_id}", headers=_h(), json=fields, timeout=30)
    r.raise_for_status()
    return r.json()


def post_comment(task_id: str, text: str) -> dict:
    r = requests.post(
        f"{BASE}/task/{task_id}/comment",
        headers=_h(),
        json={"comment_text": text},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def upload_attachment(task_id: str, file_bytes: bytes, filename: str,
                     content_type: str = "application/octet-stream") -> dict:
    """Upload attachment direto na task."""
    headers = {"Authorization": CLICKUP_TOKEN}
    files = {"attachment": (filename, file_bytes, content_type)}
    r = requests.post(
        f"{BASE}/task/{task_id}/attachment",
        headers=headers, files=files, timeout=60,
    )
    r.raise_for_status()
    return r.json()


def get_task(task_id: str) -> dict:
    r = requests.get(f"{BASE}/task/{task_id}", headers=_h(), timeout=20)
    r.raise_for_status()
    return r.json()


def set_custom_field(task_id: str, field_id: str, value) -> bool:
    try:
        r = requests.post(
            f"{BASE}/task/{task_id}/field/{field_id}",
            headers=_h(),
            json={"value": value}, timeout=15,
        )
        return r.ok
    except Exception as e:
        log.warning(f"[CF {field_id}] {e}")
        return False
