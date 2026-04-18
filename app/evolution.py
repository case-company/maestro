"""Evolution API wrapper + audio download helpers."""
import requests, base64, os, hashlib
from config import EVOLUTION_URL, EVOLUTION_KEY, EVOLUTION_INSTANCE, AUDIO_CACHE, log


def _headers():
    return {"apikey": EVOLUTION_KEY, "Content-Type": "application/json"}


def send_text(jid: str, text: str) -> bool:
    number = jid.replace("@s.whatsapp.net", "").replace("@g.us", "")
    try:
        r = requests.post(
            f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}",
            headers=_headers(),
            json={"number": number, "text": text},
            timeout=30,
        )
        log.info(f"[EVO send] {jid[:25]} → HTTP {r.status_code}")
        return r.ok
    except Exception as e:
        log.error(f"[EVO send err] {e}")
        return False


def get_audio_via_find(msg_id: str, remote_jid: str) -> bytes:
    """Busca áudio via findMessages → mediaUrl (S3 presigned)."""
    cache_key = hashlib.sha1(f"{msg_id}|{remote_jid}".encode()).hexdigest()[:16]
    cache_path = os.path.join(AUDIO_CACHE, f"{cache_key}.ogg")
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return f.read()

    try:
        r = requests.post(
            f"{EVOLUTION_URL}/chat/findMessages/{EVOLUTION_INSTANCE}",
            headers=_headers(),
            json={"where": {"key": {"id": msg_id, "remoteJid": remote_jid}}},
            timeout=20,
        )
        if not r.ok:
            log.warning(f"[EVO find] HTTP {r.status_code}")
            return b""
        records = (r.json().get("messages") or {}).get("records") or []
        if not records:
            log.warning(f"[EVO find] no records for {msg_id[:12]}")
            return b""
        rec = records[0]
        media_url = (rec.get("message") or {}).get("mediaUrl")
        if not media_url:
            return b""
        dl = requests.get(media_url, timeout=60)
        if dl.ok:
            with open(cache_path, "wb") as f:
                f.write(dl.content)
            log.info(f"[EVO audio] downloaded {len(dl.content)} bytes → cache")
            return dl.content
    except Exception as e:
        log.warning(f"[EVO find exc] {e}")
    return b""


def get_audio_b64_fallback(msg_key: dict, msg_content: dict) -> bytes:
    """Fallback: getBase64FromMediaMessage (pra áudios inline no webhook)."""
    try:
        r = requests.post(
            f"{EVOLUTION_URL}/chat/getBase64FromMediaMessage/{EVOLUTION_INSTANCE}",
            headers=_headers(),
            json={"message": {"key": msg_key, "message": msg_content}, "convertToMp4": False},
            timeout=90,
        )
        if r.ok:
            raw = r.json().get("base64", "")
            if "," in raw:
                raw = raw.split(",", 1)[1]
            return base64.b64decode(raw) if raw else b""
    except Exception as e:
        log.error(f"[EVO b64 err] {e}")
    return b""


def download_audio(msg_key: dict, msg_content: dict) -> bytes:
    """Tenta findMessages primeiro (robusto); fallback b64 inline."""
    if msg_key.get("id") and msg_key.get("remoteJid"):
        bytes_ = get_audio_via_find(msg_key["id"], msg_key["remoteJid"])
        if bytes_:
            return bytes_
    return get_audio_b64_fallback(msg_key, msg_content)


def download_image(msg_key: dict, msg_content: dict) -> bytes:
    """Mesmo esquema de áudio, pra imageMessage."""
    return get_audio_b64_fallback(msg_key, msg_content)
