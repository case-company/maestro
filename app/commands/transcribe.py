"""/x, /transcrever + auto-transcribe de áudio encaminhado."""
import re
from config import log, team_name_of
from evolution import download_audio
from transcriber import transcribe as whisper_transcribe
from accounts import ask_claude
import state


def _transcribe_audio_ref(audio_ref: dict) -> str:
    audio_bytes = download_audio(audio_ref["msg_key"], audio_ref["msg_content"])
    if not audio_bytes:
        return ""
    result = whisper_transcribe(audio_bytes)
    return result.get("text", "")


def _analyze(transcript: str, user_name: str) -> str:
    """Analisa transcrição via Claude."""
    if not transcript.strip():
        return ""
    prompt = (
        f"Áudio encaminhado por {user_name} (time Case/All In).\n\n"
        f"Transcrição:\n{transcript}\n\n"
        "Produza análise ESTRUTURADA em markdown com seções:\n"
        "- *Quem fala* (deduza pelo contexto; default: mentorada ou ninguém específico)\n"
        "- *Sobre* (1 frase)\n"
        "- *Pontos* (bullets)\n"
        "- *Ações sugeridas* (o que o time precisa fazer)\n"
        "- *Urgência* (urgente/alta/normal/baixa)\n\n"
        "Seja preciso, sem hype."
    )
    return ask_claude(prompt, timeout=90)


def handle_audio_forward(msg: dict) -> str:
    """Áudio sem comando — auto-transcreve + analisa + pergunta next action."""
    jid = msg["jid"]
    user_name = team_name_of(jid)
    audio_ref = msg["audio_ref"]

    if not audio_ref:
        return "Não achei áudio na mensagem."

    log.info(f"[audio] transcribing for {user_name}")
    transcript = _transcribe_audio_ref(audio_ref)

    if not transcript:
        return "⚠️ Não consegui baixar o áudio. Tenta reenviar."

    analysis = _analyze(transcript, user_name)

    # Salva em state pra /task reusar
    state.save(jid, {
        "type": "audio_analysis",
        "transcript": transcript,
        "analysis": analysis,
        "jid": jid,
        "msg_id": msg["msg_id"],
    })

    state.journal({
        "event": "audio_transcribed",
        "user": user_name,
        "jid": jid,
        "transcript_len": len(transcript),
    })

    response = f"📝 *Transcrição:*\n```\n{transcript}\n```\n\n"
    if analysis:
        response += f"{analysis}\n\n"
    response += (
        "───────\n"
        "Next: `/task` (cria task) · `/anexo #id` (anexa em task existente) · ignora (só arquivou)"
    )

    return response


def handle_transcribe_cmd(args: str, msg: dict) -> str:
    """/x — transcreve áudio atual OR reply-to OR último visto."""
    # Se msg atual tem áudio
    if msg["audio_ref"]:
        return handle_audio_forward(msg)

    # Fallback: último áudio do state
    st = state.load(msg["jid"])
    if st.get("transcript"):
        return (
            f"📝 *Última transcrição:*\n```\n{st['transcript'][:1500]}\n```\n\n"
            f"{st.get('analysis', '')}"
        )

    return "Envia um áudio junto com `/x` OU reply num áudio com `/x`."
