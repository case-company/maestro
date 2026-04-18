"""Config + constantes do Maestro."""
import os, logging

LOG_LEVEL = os.environ.get("MAESTRO_LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("maestro")

# Evolution
EVOLUTION_URL = os.environ.get("EVOLUTION_URL", "https://evolution.manager01.casein.com.br")
EVOLUTION_KEY = os.environ.get("EVOLUTION_KEY", "")
EVOLUTION_INSTANCE = os.environ.get("EVOLUTION_INSTANCE", "maestro")
MAESTRO_WA_JID = os.environ.get("MAESTRO_WA_JID", "")

# ClickUp
CLICKUP_TOKEN = os.environ.get("CLICKUP_TOKEN", "")
CLICKUP_TEAM_CASE = os.environ.get("CLICKUP_TEAM_CASE", "9011530618")

# Server
MAESTRO_PORT = int(os.environ.get("MAESTRO_PORT", "4300"))

# Allowlist (set de JIDs)
_raw_allowed = os.environ.get("MAESTRO_ALLOWED_JIDS", "")
ALLOWED_JIDS = {j.strip() for j in _raw_allowed.split(",") if j.strip()}

# Whisper
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "medium")
WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")

# Paths (volume-mounted)
DATA_DIR = "/data"
STATE_DIR = f"{DATA_DIR}/state"
AUDIO_CACHE = f"{DATA_DIR}/audio_cache"
JOURNAL_PATH = f"{DATA_DIR}/journal.jsonl"

import os
for d in (DATA_DIR, STATE_DIR, AUDIO_CACHE):
    os.makedirs(d, exist_ok=True)

# Nome humano por JID (quem é quem no time)
TEAM_NAMES = {
    "5511964682447@s.whatsapp.net": "Kaique",
    "5567991076464@s.whatsapp.net": "Queila",
    "5562998614114@s.whatsapp.net": "Mariza",
    "5527999087857@s.whatsapp.net": "Gobbi",
    "5527999739466@s.whatsapp.net": "Hugo",
    "5527999473185@s.whatsapp.net": "Heitor",
    "5524992514909@s.whatsapp.net": "Lara",
}


def is_allowed(jid: str) -> bool:
    return jid in ALLOWED_JIDS


def team_name_of(jid: str) -> str:
    return TEAM_NAMES.get(jid, jid.split("@")[0][:15])
