# Avaaz – Speech-to-Indian Sign Language (ISL)

**Beginner-friendly guide to how the codebase works and which files you need to run the speech-to-sign model in the web.**

---

## What does this project do?

1. **You speak** into the microphone.
2. **ASR (speech recognition)** turns your speech into English text.
3. **NLP (glossing)** turns that text into **ISL gloss tokens** (e.g. "What is your name?" → `YOUR NAME WHAT`).
4. **Video mapping** looks up each gloss token in a lexicon and finds the matching sign video (e.g. `HELLO` → `Hello.mp4`).
5. **Frontend (web)** shows the transcript, gloss, and plays the sign videos one after another.

So the pipeline is: **Speech → ASR → NLP (gloss) → Video mapping → Web UI**.

---

## How the project is divided

| Part | What it does | Main files |
|------|----------------|------------|
| **Frontend** | Web page: type/paste text, see gloss, play sign videos, or use "Live" to get updates from the mic | `web_static/index.html` |
| **ASR** | Listens to the microphone, detects when you stop speaking, turns that audio into text, then runs gloss + sends result to the web app | `asr_simple.py` |
| **NLP** | Converts English text into ISL gloss tokens using rules + a small lexicon | `nlp_gloss.py` |
| **Video mapping** | Backend that loads the lexicon (gloss → video file), serves videos, and exposes APIs the frontend and ASR use | `web_app.py`, `isl_lexicon.json`, video folder |

---

## Files you need to run the speech-to-sign model in the web

Only these are required for the **full flow** (speak → see text + gloss → watch sign videos in the browser):

| File or folder | Purpose |
|----------------|---------|
| `web_app.py` | Flask server: serves the web UI, `/api/gloss`, `/api/sequence`, `/api/publish`, `/api/latest`, and video files |
| `web_static/index.html` | Single-page frontend: text input, gloss display, video player, "Live" mode that polls `/api/latest` |
| `asr_simple.py` | Microphone ASR (Whisper or Google), runs gloss via `nlp_gloss`, and POSTs to `/api/publish` so the web app gets new transcript + gloss + video URLs |
| `nlp_gloss.py` | English → ISL gloss (rules + lexicon). Used by `web_app` and `asr_simple` |
| `isl_lexicon.json` | Map from **gloss token** (e.g. `"HELLO"`) to **video filename** (e.g. `"Hello.mp4"`). Required for video mapping |
| `INDIAN SIGN LANGUAGE ANIMATED VIDEOS /` | Folder containing the `.mp4` sign videos. Can be changed with env var `ISL_VIDEO_DIR` |

**Not required** for this web flow (optional or for other use):

- `asr.py` – standalone ASR + gloss in the terminal only; does not talk to the web app
- `isl_intro_templates.json` – example phrases; used for reference, not by the running app
- `web_app.py` is the only backend you need for the web; it already imports and uses `nlp_gloss` and the lexicon

---

## 1. Frontend (`web_static/index.html`)

- **What it is:** One HTML file with embedded CSS and JavaScript. No separate build step.
- **What it does:**
  - **Text → Gloss → Play:** You type English in the textarea, click "Gloss + Play". The page calls `POST /api/gloss` with the text, gets back gloss tokens, then `POST /api/sequence` with those tokens to get video URLs, then plays those videos in order.
  - **Play Gloss only:** You type or paste gloss tokens (e.g. `YOUR NAME WHAT`), click "Play Gloss". It calls `POST /api/sequence` and plays the returned videos.
  - **Live mode:** Click "Live: Start". The page polls `GET /api/latest` every 700 ms. When the backend has a new "event" (from `asr_simple.py` via `POST /api/publish`), it shows the transcript and gloss and auto-plays the corresponding sign videos.
- **APIs it uses:**
  - `POST /api/gloss` – body `{ "text": "..." }` → returns `{ "gloss_tokens": [...], "meta": {...} }`
  - `POST /api/sequence` – body `{ "gloss_tokens": ["HELLO","HOW","YOU"] }` → returns `{ "video_urls": [...], "missing": [...] }`
  - `GET /api/latest` – returns the latest event (transcript, gloss_tokens, video_urls, etc.) for Live mode
  - `GET /health` – used once for a sanity check

So the frontend is just the UI; all "speech → gloss → which videos" logic lives in the backend and ASR.

---

## 2. ASR (`asr_simple.py`)

- **What it does:**
  - Records from the microphone in small chunks (e.g. 200 ms).
  - Uses **VAD (Voice Activity Detection)** to detect when you’ve stopped speaking (e.g. ~0.8 s of silence).
  - Takes the accumulated audio and runs **speech-to-text** (Whisper by default, or Google with `--stt google`).
  - Sends the transcript to **NLP** (`nlp_gloss.english_to_isl_gloss`) to get gloss tokens.
  - **Publishes** that result to the web app with `POST /api/publish` (body: `transcript` + `gloss_tokens`). The web app then stores this as the "latest event" and maps gloss → videos; the frontend in Live mode picks it up from `GET /api/latest` and plays the videos.
- **How to run (with web):**
  - Start the web app first (e.g. `PORT=8002 python web_app.py`).
  - Then run:  
    `WEBAPP_URL=http://127.0.0.1:8002 python asr_simple.py`  
    or  
    `python asr_simple.py --webapp-url http://127.0.0.1:8002`
- **Useful options:**
  - `--stt whisper` (default) or `--stt google`
  - `--no-publish` – run ASR + gloss only in the terminal, do not send to the web app

So for "speech to sign in the web", you need `asr_simple.py` running with the correct `WEBAPP_URL` so it pushes to the same server the frontend is using.

---

## 3. NLP – Glossing (`nlp_gloss.py`)

- **What it does:** Converts **English text** into **ISL gloss tokens** (order and wording suitable for sign language).
  - **Input:** e.g. `"What is your name?"`
  - **Output:** e.g. `["YOUR", "NAME", "WHAT"]` (and which rule was used, confidence, etc.).
- **How it works (simplified):**
  - **Normalize:** Lowercase, remove punctuation, split into words, drop stopwords ("is", "the", "a", …).
  - **Rules:** A fixed list of patterns is tried in order (e.g. "what + your + name" → `YOUR NAME WHAT`; "hello" → `HELLO`; "I am happy" → `ME HAPPY`; "thank you" → `THANK_YOU`; etc.).
  - **Lexicon:** A small Python dictionary maps common English words to gloss symbols (e.g. "you" → "YOU", "name" → "NAME").
  - **Fallback:** If no rule matches, each word is mapped through the lexicon (or uppercased), so you still get a sequence of gloss tokens.
- **Main function you care about:** `english_to_isl_gloss(text: str) -> GlossResult`. It returns `gloss_tokens` (list of strings) and metadata. Both `web_app.py` and `asr_simple.py` call this.

So NLP is the "brain" that turns sentences into the right sequence of signs (gloss tokens); it does not know about videos—that’s the next part.

---

## 4. Video mapping (backend + data)

- **Where it lives:** In `web_app.py` plus `isl_lexicon.json` and the video folder.
- **What it does:**
  - **Lexicon:** At startup, `web_app.py` reads `isl_lexicon.json`. Each entry has at least `gloss` and `asset` (e.g. `"HELLO"` → `"Hello.mp4"`). It builds a map: **gloss token → video filename**.
  - **APIs:**
    - **`POST /api/sequence`** – Receives a list of gloss tokens. For each token, looks up the video file in the lexicon. Returns a list of **video URLs** (e.g. `/videos/Hello.mp4`) and a list of **missing** tokens (no video in the lexicon).
    - **`POST /api/publish`** – Receives transcript and/or gloss tokens (e.g. from `asr_simple.py`). If only transcript is sent, the server runs `english_to_isl_gloss(transcript)` to get tokens. Then it does the same gloss→video mapping, stores the result as the "latest event", and returns it. The frontend’s Live mode uses this via `GET /api/latest`.
  - **Serving videos:** `GET /videos/<filename>` serves the file from the video directory (default: `INDIAN SIGN LANGUAGE ANIMATED VIDEOS /`, overridable with `ISL_VIDEO_DIR`).

So "video mapping" = lexicon (gloss → filename) + backend logic that turns a list of gloss tokens into a list of video URLs and serves the files. The frontend and ASR only need to send text or gloss tokens; they don’t need to know where the videos are stored.

---

## End-to-end: running the speech-to-sign model in the web

1. **Prepare**
   - Install dependencies (e.g. `flask`, `faster-whisper`, `sounddevice`, `webrtcvad`, `numpy`; for Google STT: `SpeechRecognition`).
   - Ensure `isl_lexicon.json` exists and the video folder exists and contains the `.mp4` files referenced in the lexicon.

2. **Start the web app**
   ```bash
   cd /path/to/avaaz
   PORT=8002 python web_app.py
   ```
   Leave this running. It serves the frontend and all APIs.

3. **Start the ASR (so it sends to the web app)**
   ```bash
   python asr_simple.py --webapp-url http://127.0.0.1:8002
   ```
   (Or set `WEBAPP_URL=http://127.0.0.1:8002` and run `python asr_simple.py`.)

4. **Use the web UI**
   - Open **http://127.0.0.1:8002** in the browser.
   - Either:
     - Type English and click "Gloss + Play", or type gloss and click "Play Gloss", or  
     - Click "Live: Start" and speak; when ASR detects end of speech, the page will update and play the sign videos.

The only files that *must* exist and be used for this flow are: **`web_app.py`**, **`web_static/index.html`**, **`asr_simple.py`**, **`nlp_gloss.py`**, **`isl_lexicon.json`**, and the **video folder** (with the correct path in the app or in `ISL_VIDEO_DIR`). Everything else is optional for this "speech to sign in the web" path.

---

## Quick reference – file roles

| File | Role in "speech-to-sign in web" |
|------|----------------------------------|
| `web_app.py` | Backend: serves UI, gloss API, sequence API, publish/latest, videos |
| `web_static/index.html` | Frontend: text, gloss, video player, Live polling |
| `asr_simple.py` | Mic → speech-to-text → gloss → POST to `/api/publish` |
| `nlp_gloss.py` | English → ISL gloss tokens (used by web app and ASR) |
| `isl_lexicon.json` | Gloss token → video filename (used by web app for mapping) |
| `INDIAN SIGN LANGUAGE ANIMATED VIDEOS /` (or `ISL_VIDEO_DIR`) | Directory of `.mp4` sign videos |

This is everything you need to understand and run the codebase for the web-based speech-to-sign model.
