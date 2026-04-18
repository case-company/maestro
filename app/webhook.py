"""
Maestro webhook — Flask entry point.

Endpoint: POST /webhook/maestro
Health:   GET /health
"""
import json, sys
from flask import Flask, request, jsonify
from config import log, MAESTRO_PORT, is_allowed, ALLOWED_JIDS, MAESTRO_WA_JID
from router import extract_message, should_process_v2, route
from evolution import send_text

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "maestro",
        "allowlist_count": len(ALLOWED_JIDS),
        "wa_jid": MAESTRO_WA_JID,
    })


@app.route("/webhook/maestro", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception as e:
        log.warning(f"[webhook parse err] {e}")
        return jsonify({"err": "invalid json"}), 400

    event = data.get("event", "?")
    log.info(f"[WEBHOOK] event={event}")

    if event != "messages.upsert":
        return jsonify({"ok": True, "skipped": event})

    raw = data.get("data", {})
    msgs = raw if isinstance(raw, list) else [raw]

    for m in msgs:
        try:
            msg = extract_message(m)
            log.info(f"[MSG] jid={msg['jid'][:25]} fromMe={msg['from_me']} "
                     f"text={msg['text'][:50]!r} audio={bool(msg['audio_ref'])}")

            if not should_process_v2(msg):
                continue

            response = route(msg)
            if response:
                send_text(msg["jid"], response)

        except Exception as e:
            log.exception(f"[process err] {e}")

    return jsonify({"ok": True})


@app.route("/", methods=["GET"])
def root():
    return "Maestro — Case/All In"


if __name__ == "__main__":
    # Startup — init accounts (verifica pool)
    import accounts
    log.info(f"[startup] claude pool: {accounts.status()}")
    log.info(f"[startup] allowlist: {len(ALLOWED_JIDS)} JIDs")
    log.info(f"[startup] serving on 0.0.0.0:{MAESTRO_PORT}")

    app.run(host="0.0.0.0", port=MAESTRO_PORT, threaded=True, debug=False)
