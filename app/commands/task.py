"""/task — cria task no ClickUp All In."""
import re
from config import log, team_name_of
from clickup_adapter import (
    resolve_mentorada, current_sprint_list_id,
    create_task, update_task,
    MENTORADAS, CANONICAL_DISPLAY,
)
from accounts import ask_claude
from task_metadata import extract, format_summary
import state


def _strip_prefix(description: str) -> str:
    low = description.lower().lstrip()
    for p in ("case:", "allin:", "sprint:"):
        if low.startswith(p):
            return description.split(":", 1)[1].strip()
    return description


def _generate_title(desc_hint: str, analysis: str) -> str:
    """Title via Claude com sanitização robusta."""
    prompt = (
        "Você vai gerar APENAS um título (6-12 palavras) pra uma task ClickUp.\n\n"
        "REGRAS ABSOLUTAS:\n"
        "- Máx 80 caracteres\n"
        "- SEM markdown, aspas, emojis, asteriscos, prefixo ('Título:', etc)\n"
        "- SEM copiar literal da análise — SINTETIZE\n"
        "- Imperativo quando fizer sentido (verbo no infinitivo)\n"
        "- Retorne SÓ a frase\n\n"
        f"CONTEXTO (análise):\n{analysis[:800]}\n\n"
        f"HINT DO USUÁRIO: {desc_hint or '(sem hint — use só o contexto)'}\n\n"
        "TÍTULO:"
    )
    raw = ask_claude(prompt, timeout=30)
    raw = raw.strip()
    raw = re.sub(r"^(t[ií]tulo|title)\s*:\s*", "", raw, flags=re.IGNORECASE)
    for line in raw.split("\n"):
        line = line.strip()
        if line:
            raw = line
            break
    raw = re.sub(r"^[#*\-_>\s📝📋✅⏳🔴🟠🟡⚪👤📅⚡💬🎙️]+", "", raw)
    raw = raw.strip("\"' `<>")
    # Rejection
    bad_starts = ("transcrição", "análise", "pontos", "origem", "##", "contexto")
    if raw.lower().startswith(bad_starts) or len(raw) < 5:
        # Fallback: primeira linha útil do desc_hint
        if desc_hint:
            raw = desc_hint.split("\n")[0][:80]
        else:
            raw = "Task sem título"
    return raw[:80]


def _build_description(desc_hint: str, transcript: str, analysis: str,
                      user_name: str) -> str:
    parts = []
    parts.append(f"## Origem\n{user_name} via Maestro")
    if desc_hint:
        parts.append(f"\n## Hint do usuário\n{desc_hint}")
    if analysis:
        parts.append(f"\n## Análise\n{analysis}")
    if transcript:
        parts.append(f"\n## Transcrição\n```\n{transcript[:2000]}\n```")
    return "\n\n".join(parts)


def _show_list() -> str:
    sorted_names = sorted(CANONICAL_DISPLAY.values())
    return (
        "*Formato /task:*\n"
        "• `/task case:<mentorada> <desc>` — task de mentorada\n"
        "• `/task allin:<desc>` — sprint atual All In\n"
        "• `/task` (sem args) — pergunto qual\n\n"
        "*Mentoradas Case:*\n" + "\n".join(f"• {n}" for n in sorted_names)
    )


def handle(args: str, msg: dict) -> str:
    jid = msg["jid"]
    user_name = team_name_of(jid)
    description = args.strip()

    # Pega contexto de áudio analisado recente
    st = state.load(jid)
    transcript = st.get("transcript", "") if st.get("type") == "audio_analysis" else ""
    analysis = st.get("analysis", "") if st.get("type") == "audio_analysis" else ""
    has_ctx = bool(transcript or analysis)

    # Sem args: pergunta prefixo (OU usa ctx se tem análise recente)
    if not description:
        if has_ctx:
            # Sugere título e pergunta prefixo
            suggested = _generate_title("", analysis or transcript)
            state.save(jid, {
                **st,
                "type": "task_pending_prefix",
                "suggested_title": suggested,
            })
            return (
                f"📋 *Sugestão de título:* _{suggested}_\n\n"
                "Qual o destino?\n"
                "• `case:<mentorada>` — ex: `case:jordanna`\n"
                "• `allin` — sprint atual do time"
            )
        else:
            return _show_list()

    # Resolve destino
    low = description.lower().lstrip()
    list_id = None
    list_display = None

    if low.startswith("case:"):
        rest = description.split(":", 1)[1].strip()
        target = rest.split(None, 1)[0].lower().rstrip(",.:;") if rest else ""
        r = resolve_mentorada(target)
        if not r:
            return (f"🧭 Mentorada *{target}* não encontrada.\n\n"
                    "*Mentoradas Case:*\n" +
                    "\n".join(f"• {n}" for n in sorted(CANONICAL_DISPLAY.values())))
        canon, list_id, display = r
        list_display = f"Case / {display}"
        desc_hint = _strip_prefix(description)
        # Remove slug do início do desc_hint
        desc_hint = re.sub(rf"^{re.escape(target)}\s+", "", desc_hint, flags=re.IGNORECASE)

    elif low.startswith("allin:") or low.startswith("sprint:"):
        list_id = current_sprint_list_id()
        list_display = "All In / Sprint atual"
        desc_hint = _strip_prefix(description)

    # Sem prefixo: verifica se user tinha state de task_pending_prefix
    elif st.get("type") == "task_pending_prefix":
        # Re-tenta com prefixo
        return handle(f"{description}", msg)  # noop fallback

    else:
        return ("⚠️ Defina o destino:\n"
                "• `/task case:<mentorada> <desc>`\n"
                "• `/task allin:<desc>`\n\n"
                "Use `/task` (sem args) pra ver lista.")

    # Gera título
    if has_ctx:
        title = _generate_title(desc_hint, analysis or transcript)
    else:
        title = desc_hint.split("\n")[0][:80] if desc_hint else "Task sem título"

    # Monta descrição rica
    rich_desc = _build_description(desc_hint, transcript, analysis, user_name)

    # Cria task
    try:
        task = create_task(list_id=list_id, name=title, description=rich_desc, status="triage")
        task_id = task["id"]
        task_url = task.get("url", "")

        # Extrai metadata + aplica
        meta = extract(title, desc_hint, transcript, analysis)
        update_fields = {}
        if meta.get("assignees"):
            update_fields["assignees"] = {"add": meta["assignees"]}
        if meta.get("due_date"):
            update_fields["due_date"] = meta["due_date"]
        if meta.get("priority"):
            update_fields["priority"] = meta["priority"]
        if update_fields:
            try:
                update_task(task_id, **update_fields)
            except Exception as e:
                log.warning(f"[task meta update err] {e}")

        # Journal
        state.journal({
            "event": "task_created",
            "user": user_name,
            "task_id": task_id,
            "list": list_display,
            "title": title,
            "has_audio_ctx": has_ctx,
        })

        # Limpa state audio_analysis (consumiu)
        if has_ctx:
            state.clear(jid)

        # Response
        summary = format_summary(meta) if meta else ""
        response = (
            f"✅ *Task criada*\n"
            f"*Lista:* {list_display}\n"
            f"*Título:* {title}\n"
        )
        if summary:
            response += f"\n{summary}\n"
        response += f"\n{task_url}"
        return response

    except Exception as e:
        log.exception(f"[task create err] {e}")
        return f"❌ Erro criando task: {e}"
