import sys

import sounddevice as sd  # type: ignore[import]
from faster_whisper import WhisperModel  # type: ignore[import]

from nlp_gloss import english_to_isl_gloss


def main():
    # 1. Load model (CPU, int8 for speed)
    print("Loading Whisper model (base, CPU, int8)…")
    model = WhisperModel("small", device="cpu", compute_type="int8")

    # 2. Set audio params
    samplerate = 16000          # 16 kHz
    block_seconds = 4.0         # process every block_seconds
    block_frames = int(samplerate * block_seconds)

    print("Starting microphone ASR. Speak into your mic.")
    print("Press Ctrl+C to stop.\n")

    def callback(indata, frames, time_info, status):
        if status:
            print(f"[audio status] {status}", file=sys.stderr)

        # indata: float32 [-1, 1], shape (frames, channels)
        audio = indata[:, 0].copy()  # mono

        # 3. Transcribe this chunk
        segments, _ = model.transcribe(audio, language="en")
        texts = [seg.text.strip() for seg in segments if seg.text.strip()]
        if texts:
            transcript = " ".join(texts)
            print("> ASR  :", transcript)
            gloss_result = english_to_isl_gloss(transcript)
            if gloss_result.gloss_tokens:
                print("  GLOSS:", " ".join(gloss_result.gloss_tokens))

    # 4. Open input stream and loop until Ctrl+C
    with sd.InputStream(
        channels=1,
        samplerate=samplerate,
        dtype="float32",
        blocksize=block_frames,
        callback=callback,
    ):
        try:
            while True:
                sd.sleep(1000)  # keep process alive
        except KeyboardInterrupt:
            print("\nStopping.")


if __name__ == "__main__":
    main()