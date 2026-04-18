"""/help — lista comandos."""
from config import team_name_of


def handle(args: str, msg: dict) -> str:
    user = team_name_of(msg["jid"])
    return f"""*🤖 Maestro — comandos*

Oi {user}! Maestro recebe o que você encaminhar e processa.

*Sem comando (auto):*
• 🎙️ *Áudio* → transcreve + analisa + sugere next
• 📸 *Imagem* → salva aguardando /anexo ou /task
• 💬 *Texto* → mostra essa ajuda

*Comandos:*
• `/task` — cria task (pergunta pra qual mentorada)
• `/task case:<mentorada> <desc>` — task direta
• `/task allin:<desc>` — task sprint atual
• `/x` — re-mostra última transcrição
• `/anexo #<task_id>` — anexa último conteúdo em task existente
• `/sot <mentorada>` — contexto/tasks da mentorada
• `/pool` — status das contas Claude
• `/help` — essa ajuda

*Fluxo exemplo:*
1. Encaminha áudio da Jordanna pro Maestro
2. Maestro transcreve + analisa
3. Você: `/task case:jordanna` → cria task com contexto do áudio

*Princípios:*
- Maestro só responde pra time autorizado
- Conteúdo de mentoradas só chega via você (Maestro não entra em grupos)
- Nada se perde: tudo arquiva em journal
"""
