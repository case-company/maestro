"""Whisper transcriber com modelo warm."""
import os, tempfile, time
from config import WHISPER_MODEL, WHISPER_COMPUTE_TYPE, log

_model = None

def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        t0 = time.time()
        log.info(f"[whisper] loading {WHISPER_MODEL} {WHISPER_COMPUTE_TYPE}...")
        _model = WhisperModel(WHISPER_MODEL, compute_type=WHISPER_COMPUTE_TYPE, device="cpu")
        log.info(f"[whisper] loaded in {time.time()-t0:.1f}s")
    return _model


def transcribe(audio_bytes: bytes, language: str = "pt") -> dict:
    """Retorna {'text': ..., 'language': ..., 'duration': ...}."""
    if not audio_bytes:
        return {"text": "", "error": "empty"}

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = _get_model()
        segments, info = model.transcribe(
            tmp_path, language=language, beam_size=5, vad_filter=True,
        )
        text = " ".join(s.text.strip() for s in segments).strip()
        return {
            "text": text,
            "language": info.language,
            "duration": info.duration,
        }
    except Exception as e:
        log.error(f"[whisper err] {e}")
        return {"text": "", "error": str(e)}
    finally:
        try: os.remove(tmp_path)
        except Exception: pass
