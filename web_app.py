from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import quote

from flask import Flask, jsonify, request, send_from_directory  # type: ignore[import]

from nlp_gloss import english_to_isl_gloss


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "web_static"

# Default: use the dataset folder inside this repo
DEFAULT_VIDEO_DIR = APP_DIR / "INDIAN SIGN LANGUAGE ANIMATED VIDEOS "
VIDEO_DIR = Path(os.getenv("ISL_VIDEO_DIR", str(DEFAULT_VIDEO_DIR))).expanduser().resolve()

LEXICON_PATH = APP_DIR / "isl_lexicon.json"


def load_gloss_to_asset() -> dict[str, str]:
    data = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    gloss_to_asset: dict[str, str] = {}
    for row in data:
        gloss = str(row.get("gloss", "")).strip().upper()
        asset = str(row.get("asset", "")).strip()
        if gloss and asset:
            gloss_to_asset[gloss] = asset
    return gloss_to_asset


GLOSS_TO_ASSET = load_gloss_to_asset()

app = Flask(__name__)

# In-memory “latest event” store for Live mode
LATEST_EVENT: dict[str, object] = {"id": 0}


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "video_dir": str(VIDEO_DIR),
            "video_dir_exists": VIDEO_DIR.exists(),
            "lexicon_entries": len(GLOSS_TO_ASSET),
        }
    )


@app.post("/api/gloss")
def api_gloss():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    result = english_to_isl_gloss(text)
    return jsonify(result.to_dict())


@app.post("/api/sequence")
def api_sequence():
    payload = request.get_json(silent=True) or {}
    tokens_in = payload.get("gloss_tokens") or []
    if not isinstance(tokens_in, list):
        return jsonify({"error": "gloss_tokens must be a list"}), 400

    tokens = [str(t).strip().upper() for t in tokens_in if str(t).strip()]
    missing: list[str] = []
    urls: list[str] = []

    for token in tokens:
        asset = GLOSS_TO_ASSET.get(token)
        if not asset:
            missing.append(token)
            continue
        # URL-encode filename (handles spaces like "Thank You.mp4")
        urls.append(f"/videos/{quote(asset)}")

    return jsonify({"gloss_tokens": tokens, "video_urls": urls, "missing": missing})


@app.post("/api/publish")
def api_publish():
    """
    Receive transcript and/or gloss tokens from an external producer (ASR script),
    map gloss -> videos, and store as the latest event for the web UI to consume.

    Payload examples:
      - {"transcript": "..."}  (server computes ISL gloss using rules)
      - {"transcript": "...", "gloss_tokens": ["HELLO","HOW","YOU"]}
      - {"gloss_tokens": ["HELLO","HOW","YOU"]}
    """
    global LATEST_EVENT
    payload = request.get_json(silent=True) or {}

    transcript = str(payload.get("transcript", "")).strip()
    tokens_in = payload.get("gloss_tokens") or []

    if transcript and not tokens_in:
        gloss_result = english_to_isl_gloss(transcript)
        tokens = gloss_result.gloss_tokens
        gloss_meta = gloss_result.to_dict().get("meta", {})
    else:
        if not isinstance(tokens_in, list):
            return jsonify({"error": "gloss_tokens must be a list"}), 400
        tokens = [str(t).strip().upper() for t in tokens_in if str(t).strip()]
        gloss_meta = {"rules_applied": ["ExternalPublish"], "confidence": 1.0}

    missing: list[str] = []
    urls: list[str] = []
    for token in tokens:
        asset = GLOSS_TO_ASSET.get(token)
        if not asset:
            missing.append(token)
            continue
        urls.append(f"/videos/{quote(asset)}")

    event_id = int(LATEST_EVENT.get("id", 0)) + 1
    LATEST_EVENT = {
        "id": event_id,
        "transcript": transcript,
        "gloss_tokens": tokens,
        "gloss_meta": gloss_meta,
        "video_urls": urls,
        "missing": missing,
    }
    return jsonify(LATEST_EVENT)


@app.get("/api/latest")
def api_latest():
    return jsonify(LATEST_EVENT)


@app.get("/videos/<path:filename>")
def serve_video(filename: str):
    # Flask already path-normalizes; serve only from configured dir
    return send_from_directory(VIDEO_DIR, filename)


if __name__ == "__main__":
    if not STATIC_DIR.exists():
        raise SystemExit(f"Missing static dir: {STATIC_DIR}")
    port = int(os.getenv("PORT", "8000"))
    # Disable reloader to avoid watchdog/fsevents issues on some setups.
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

