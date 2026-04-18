"""Command dispatcher."""
from config import log


def dispatch_command(text: str, msg: dict):
    """Roteia /comando → handler."""
    parts = text.split(None, 1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    from commands import task, transcribe, attach, sot_cmd, help_cmd, accounts_cmd

    HANDLERS = {
        "/task": task.handle,
        "/x": transcribe.handle_transcribe_cmd,
        "/transcrever": transcribe.handle_transcribe_cmd,
        "/anexo": attach.handle_attach,
        "/anexar": attach.handle_attach,
        "/sot": sot_cmd.handle,
        "/help": help_cmd.handle,
        "/ajuda": help_cmd.handle,
        "/accounts": accounts_cmd.handle,
        "/pool": accounts_cmd.handle,
    }

    handler = HANDLERS.get(cmd)
    if not handler:
        return (f"Comando `{cmd}` não reconhecido.\n\n"
                f"Use `/help` pra ver tudo.")

    try:
        return handler(args, msg)
    except Exception as e:
        log.exception(f"[{cmd} err] {e}")
        return f"⚠️ Erro em `{cmd}`: {e}"
