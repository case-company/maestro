"""/anexo — anexa último conteúdo em task existente via short_id ou task_id."""
import re
from config import log, team_name_of
from evolution import download_image, download_audio
from clickup_adapter import get_task, upload_attachment, post_comment
import state


def handle_image_forward(msg: dict) -> str:
    """Imagem sem comando — salva em state aguardando /anexo #id ou /task."""
    jid = msg["jid"]
    user_name = team_name_of(jid)
    image_ref = msg["image_ref"]

    # Download da imagem
    image_bytes = download_image(image_ref["msg_key"], image_ref["msg_content"])
    if not image_bytes:
        return "⚠️ Não consegui baixar a imagem."

    # Salva em /tmp por hora (volume /data em produção)
    import os, time
    fname = f"/data/audio_cache/img_{msg['msg_id'][:12]}_{int(time.time())}.jpg"
    with open(fname, "wb") as f:
        f.write(image_bytes)

    state.save(jid, {
        "type": "pending_image",
        "image_path": fname,
        "jid": jid,
        "msg_id": msg["msg_id"],
    })

    return (
        f"📸 *Imagem recebida* ({len(image_bytes)//1024} KB)\n\n"
        "Next:\n"
        "• `/anexo #<task_id>` — anexa em task existente\n"
        "• `/task case:<nome> <desc>` — cria task nova com imagem anexa\n"
        "• ignora (só arquivei)"
    )


def handle_attach(args: str, msg: dict) -> str:
    """
    /anexo #abc123 [comentário] — anexa última imagem/áudio em task existente.
    """
    jid = msg["jid"]
    user_name = team_name_of(jid)

    # Parse #task_id
    m = re.match(r"#?([a-zA-Z0-9]+)(?:\s+(.*))?", args.strip())
    if not m:
        return "Uso: `/anexo #<task_id> [comentário opcional]`"

    task_id = m.group(1)
    comment = m.group(2) or ""

    # Verifica task existe
    try:
        task = get_task(task_id)
    except Exception as e:
        return f"❌ Task `#{task_id}` não encontrada: {e}"

    # Anexa pending image OR audio
    st = state.load(jid)
    if st.get("type") == "pending_image":
        import os
        image_path = st["image_path"]
        if not os.path.exists(image_path):
            return "⚠️ Imagem temporária expirou."
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        try:
            upload_attachment(task_id, image_bytes, f"img_{task_id[:8]}.jpg", "image/jpeg")
        except Exception as e:
            return f"❌ Upload falhou: {e}"
        if comment:
            try: post_comment(task_id, f"_{user_name} via Maestro:_\n{comment}")
            except Exception: pass

        state.clear(jid)
        state.journal({"event": "attach_image", "user": user_name, "task_id": task_id})
        return f"✅ Imagem anexada em *{task.get('name', task_id)}*\n{task.get('url', '')}"

    elif st.get("type") == "audio_analysis":
        # Anexa transcrição + análise como comentário
        transcript = st.get("transcript", "")
        analysis = st.get("analysis", "")
        comment_body = (
            f"_{user_name} encaminhou áudio via Maestro:_\n\n"
            f"**Transcrição:**\n```\n{transcript}\n```\n\n"
            f"**Análise:**\n{analysis}"
        )
        if comment:
            comment_body += f"\n\n**Nota adicional:**\n{comment}"
        try:
            post_comment(task_id, comment_body)
        except Exception as e:
            return f"❌ Comment falhou: {e}"

        state.clear(jid)
        state.journal({"event": "attach_audio", "user": user_name, "task_id": task_id})
        return f"✅ Áudio/análise anexada em *{task.get('name', task_id)}*\n{task.get('url', '')}"

    else:
        return ("Não tem conteúdo pendente pra anexar.\n"
                "Envia áudio/imagem primeiro, depois `/anexo #<task_id>`.")
