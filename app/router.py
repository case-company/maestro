"""
Router — decide o que fazer com cada mensagem recebida.

REGRAS DURAS:
1. Só processa mensagens de JIDs na allowlist (DM pessoal ou self-group)
2. Ignora mensagens em grupos com terceiros (mentoradas, externos)
3. fromMe=True em DM do user = user mandou pro Maestro
4. fromMe=False em DM = alguém mandou pro user, Maestro ignora (é só o user que fala com Maestro)

Fluxo:
  msg chega → is_allowed? → extract content → dispatch comando OR smart route
"""
from config import is_allowed, team_name_of, MAESTRO_WA_JID, log
import state


def extract_message(raw_message: dict) -> dict:
    """
    Extrai informação normalizada de uma mensagem Evolution.
    Retorna dict com: jid, msg_id, sender_jid, from_me, text, audio_ref, image_ref,
                      forwarded, quoted, push_name
    """
    key = raw_message.get("key", {})
    message = raw_message.get("message", {})

    jid = key.get("remoteJid", "")
    msg_id = key.get("id", "")
    from_me = key.get("fromMe", False)
    sender_jid = key.get("participant") or jid
    push_name = raw_message.get("pushName", "") or ""
    is_group = "@g.us" in jid

    # Texto (várias fontes possíveis)
    text = (
        message.get("conversation")
        or message.get("extendedTextMessage", {}).get("text")
        or message.get("imageMessage", {}).get("caption")
        or message.get("videoMessage", {}).get("caption")
        or message.get("audioMessage", {}).get("caption")
        or message.get("pttMessage", {}).get("caption")
        or ""
    ).strip()

    # Áudio (atual ou forwarded/quoted)
    audio_ref = None
    audio_msg = message.get("audioMessage") or message.get("pttMessage")
    if audio_msg:
        audio_ref = {"msg_key": key, "msg_content": message, "source": "direct"}
    else:
        # Check quoted message
        ctx = (
            message.get("extendedTextMessage", {}).get("contextInfo")
            or message.get("contextInfo", {})
        )
        if ctx:
            quoted = ctx.get("quotedMessage") or {}
            if quoted.get("audioMessage") or quoted.get("pttMessage"):
                audio_ref = {
                    "msg_key": {
                        "id": ctx.get("stanzaId", ""),
                        "remoteJid": jid,
                        "fromMe": ctx.get("participant") is None,
                    },
                    "msg_content": quoted,
                    "source": "quoted",
                }

    # Imagem
    image_ref = None
    if message.get("imageMessage"):
        image_ref = {"msg_key": key, "msg_content": message}

    # Forwarded flag
    ctx = (
        message.get("extendedTextMessage", {}).get("contextInfo")
        or message.get("contextInfo", {})
    )
    forwarded = bool(ctx.get("isForwarded")) if ctx else False

    return {
        "jid": jid, "msg_id": msg_id,
        "sender_jid": sender_jid, "from_me": from_me,
        "push_name": push_name,
        "text": text,
        "audio_ref": audio_ref,
        "image_ref": image_ref,
        "forwarded": forwarded,
        "is_group": is_group,
        "raw": raw_message,
    }


def should_process(msg: dict) -> bool:
    """
    Maestro processa SE:
    - É DM (não grupo com terceiros)
    - fromMe=True (user mandou pro Maestro)
    - sender está na allowlist
    """
    # Grupos com terceiros = ignorar (decisão do Kaique — Maestro só em DMs)
    if msg["is_group"]:
        # Exceção: self-note-to-self (grupo consigo mesmo) — tratar como DM
        # Padrão: jid do tipo `5511XXX-YYY@g.us` onde XXX é o próprio número
        jid = msg["jid"]
        if "-" in jid.split("@")[0] and jid.split("-")[0] in [j.split("@")[0] for j in __import__("config").ALLOWED_JIDS]:
            pass  # allowed self-group
        else:
            return False

    # fromMe=True em DM = user escrevendo pro Maestro
    if not msg["from_me"]:
        return False

    # O JID DE ORIGEM é o chat. Pro DM, jid é o outro lado — aqui o "outro lado" é o Maestro.
    # O sender do comando é o próprio user, cujo JID tá na allowlist.
    # Nossa allowlist tem os JIDs DOS USUÁRIOS. Então precisamos confirmar que este DM
    # pertence a um dos users autorizados.
    # Em DM, o jid remoteJid é o OUTRO LADO. Se o user mandou pro Maestro,
    # remoteJid = MAESTRO_WA_JID. Isso significa que QUALQUER msg pro Maestro
    # via DM é considerada autorizada se vier de um JID na allowlist.
    # Mas aqui o JID é do CHAT (Maestro), não do user. Então precisamos identificar
    # quem é o "user" por outro meio — via WA client do próprio user.

    # HEURÍSTICA: em DMs fromMe=True, o "user" é o dono da sessão WA do Maestro — que é
    # "Suporte" (número 5511913529334). Mas Maestro tem que ser controlado pelo TIME,
    # não por uma única pessoa. Então cada user precisa ter SEU PRÓPRIO instance Evolution
    # — OU Maestro precisa de um canal por user.
    # Por ora, Maestro é 1 instance WA; QUEM controla = quem tem o celular ligado no número
    # do Maestro (suporte). O time encaminha pro Maestro → Maestro recebe (fromMe=false
    # do ponto de vista do Maestro).
    # INVERTEMOS a lógica: fromMe=False no Maestro = user mandou pro Maestro. E o sender
    # deve estar na allowlist.

    return True


def should_process_v2(msg: dict) -> bool:
    """
    Lógica correta: Maestro é um bot WA que recebe DMs de users.
    - remoteJid = JID do user que mandou pro Maestro (em DM)
    - fromMe = False (user enviou PRO Maestro)
    - sender precisa estar na allowlist
    """
    if msg["is_group"]:
        return False  # Maestro nunca processa grupos

    if msg["from_me"]:
        # Maestro mandou mensagem (típico após responder) — não processar auto
        return False

    # jid é o user que iniciou o DM. Deve estar na allowlist.
    return is_allowed(msg["jid"])


def route(msg: dict) -> str:
    """
    Roteia uma msg já filtrada.
    Retorna texto de resposta (Maestro → user) ou None pra silêncio.
    """
    jid = msg["jid"]  # este é o JID do user que mandou (remoteJid em DM = outro lado)
    user_name = team_name_of(jid)
    text = msg["text"].strip()

    log.info(f"[ROUTE] {user_name} ({jid[:20]}) text={text[:60]!r} audio={bool(msg['audio_ref'])} img={bool(msg['image_ref'])}")

    # ═══ Comandos com / prefix ═══
    if text.startswith("/"):
        from commands import dispatch_command
        return dispatch_command(text, msg)

    # ═══ Conteúdo encaminhado SEM comando — smart route ═══
    # Áudio sozinho ou com texto → auto-transcreve + mostra análise
    if msg["audio_ref"]:
        from commands.transcribe import handle_audio_forward
        return handle_audio_forward(msg)

    # Imagem sozinha → aguarda contexto, salva temporariamente
    if msg["image_ref"]:
        from commands.attach import handle_image_forward
        return handle_image_forward(msg)

    # Texto livre sem áudio/imagem → responde com ajuda
    if text:
        return (
            f"Oi {user_name}! Sou o Maestro.\n\n"
            "Encaminha pra mim:\n"
            "• 🎙️ áudios (transcrevo + analiso)\n"
            "• 📸 prints/imagens (OCR + anexo em task)\n"
            "• mensagens de mentoradas (arquivo + contexto)\n\n"
            "Comandos:\n"
            "• `/task` — cria task (pergunto pra qual mentorada)\n"
            "• `/task case:<nome> <desc>` — task direta\n"
            "• `/task allin:<desc>` — sprint atual\n"
            "• `/anexo #<id>` — anexa último conteúdo em task existente\n"
            "• `/sot <nome>` — contexto da mentorada\n"
            "• `/help` — mais comandos"
        )

    return None
