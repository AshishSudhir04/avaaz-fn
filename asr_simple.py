from __future__ import annotations

import json
import os
import sys
import threading
import queue
from urllib.request import Request, urlopen

import numpy as np  # type: ignore[import]
import sounddevice as sd  # type: ignore[import]
import webrtcvad  # type: ignore[import]
from faster_whisper import WhisperModel  # type: ignore[import]

from nlp_gloss import english_to_isl_gloss

SAMPLE_RATE = 16000
# Small blocks so we can detect silence quickly (every 200 ms)
BLOCK_SECONDS = 0.2
BLOCK_FRAMES = int(SAMPLE_RATE * BLOCK_SECONDS)
# 20 ms frames for webrtcvad (must be 10, 20, or 30 ms)
VAD_FRAME_MS = 20
VAD_FRAME_SAMPLES = int(SAMPLE_RATE * VAD_FRAME_MS / 1000)
# How many consecutive silent blocks before we consider "speaker stopped"
SILENCE_BLOCKS_THRESHOLD = 4  # 4 * 0.2 s = 0.8 s of silence
# Min fraction of speech frames in a block to count as "speech"
SPEECH_RATIO_THRESHOLD = 0.25
# Max utterance length (seconds) to avoid huge buffers
MAX_UTTERANCE_SECONDS = 30


def _block_speech_ratio(audio_float: np.ndarray, vad: webrtcvad.Vad) -> float:
    """Return fraction of 20 ms frames in this block that VAD marks as speech."""
    audio_int16 = (np.clip(audio_float, -1.0, 1.0) * 32767).astype(np.int16)
    n_frames = 0
    speech_frames = 0
    for i in range(0, len(audio_int16) - VAD_FRAME_SAMPLES + 1, VAD_FRAME_SAMPLES):
        frame = audio_int16[i : i + VAD_FRAME_SAMPLES].tobytes()
        if vad.is_speech(frame, SAMPLE_RATE):
            speech_frames += 1
        n_frames += 1
    return speech_frames / n_frames if n_frames else 0.0


def _publisher_worker(q: "queue.Queue[dict]", webapp_url: str) -> None:
    while True:
        item = q.get()
        if item is None:
            return
        try:
            body = json.dumps(item).encode("utf-8")
            req = Request(
                f"{webapp_url.rstrip('/')}/api/publish",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=3) as _:
                pass
        except Exception:
            # Don't crash ASR if web app isn't running.
            pass


def main():
    print("Loading Whisper model (small, CPU, int8)…")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    vad = webrtcvad.Vad(2)  # 0=quality, 3=aggressive; 2 is a middle ground

    webapp_url = os.getenv("WEBAPP_URL", "http://127.0.0.1:8001")
    pub_q: "queue.Queue[dict]" = queue.Queue(maxsize=5)
    pub_thread = threading.Thread(
        target=_publisher_worker, args=(pub_q, webapp_url), daemon=True
    )
    pub_thread.start()

    buffer: list[np.ndarray] = []
    silence_blocks = 0

    print("Starting microphone ASR. Speak; we transcribe when you pause (silence).")
    print("Press Ctrl+C to stop.\n")

    def callback(indata, frames, time_info, status):
        nonlocal buffer, silence_blocks
        if status:
            print(f"[audio status] {status}", file=sys.stderr)

        audio = indata[:, 0].copy()
        ratio = _block_speech_ratio(audio, vad)

        if ratio >= SPEECH_RATIO_THRESHOLD:
            buffer.append(audio.copy())
            silence_blocks = 0
            # Cap buffer to avoid unbounded growth
            total_samples = sum(b.size for b in buffer)
            if total_samples > SAMPLE_RATE * MAX_UTTERANCE_SECONDS:
                buffer = buffer[-int(SAMPLE_RATE * MAX_UTTERANCE_SECONDS / audio.size) :]
        else:
            if buffer:
                silence_blocks += 1
                if silence_blocks >= SILENCE_BLOCKS_THRESHOLD:
                    # Speaker stopped – transcribe accumulated audio
                    full_audio = np.concatenate(buffer)
                    buffer.clear()
                    silence_blocks = 0

                    segments, _ = model.transcribe(
                        full_audio,
                        language="en",
                        beam_size=5,
                        vad_filter=True,
                    )
                    texts = [seg.text.strip() for seg in segments if seg.text.strip()]
                    if not texts:
                        return
                    transcript = " ".join(texts)
                    print("> ASR :", transcript)
                    gloss_result = english_to_isl_gloss(transcript)
                    print("  GLOSS (ISL rules):", " ".join(gloss_result.gloss_tokens))

                    # Publish to the web app (so it can auto-play videos)
                    try:
                        pub_q.put_nowait(
                            {
                                "transcript": transcript,
                                "gloss_tokens": gloss_result.gloss_tokens,
                            }
                        )
                    except queue.Full:
                        pass

    with sd.InputStream(
        channels=1,
        samplerate=SAMPLE_RATE,
        dtype="float32",
        blocksize=BLOCK_FRAMES,
        callback=callback,
    ):
        try:
            while True:
                sd.sleep(1000)
        except KeyboardInterrupt:
            print("\nStopping.")
        finally:
            try:
                pub_q.put_nowait(None)  # type: ignore[arg-type]
            except Exception:
                pass


if __name__ == "__main__":
    main()