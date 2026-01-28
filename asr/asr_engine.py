import whisper
import sounddevice as sd
import numpy as np
import datetime

model = whisper.load_model("tiny.en")

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.5  # small chunks
SILENCE_THRESHOLD = 0.005
SILENCE_CHUNKS_TO_STOP = 4  # silence ~2 sec

def is_silent(audio):
    return np.abs(audio).mean() < SILENCE_THRESHOLD

def record_audio():
    print("🚀 Avaaz Smart ASR Started\n")

    buffer = []
    silence_counter = 0
    recording = False

    while True:
        audio = sd.rec(int(CHUNK_DURATION * SAMPLE_RATE),
                       samplerate=SAMPLE_RATE,
                       channels=1,
                       dtype='float32')
        sd.wait()

        audio = np.squeeze(audio)

        if not is_silent(audio):
            if not recording:
                print("🎤 Speech detected...")
                recording = True
            buffer.append(audio)
            silence_counter = 0

        elif recording:
            silence_counter += 1
            buffer.append(audio)

            if silence_counter >= SILENCE_CHUNKS_TO_STOP:
                print("🧠 Processing sentence...")
                full_audio = np.concatenate(buffer)

                result = model.transcribe(full_audio, fp16=False)
                text = result["text"].strip().lower()

                if text:
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] 🗣 {text}\n")

                # reset
                buffer = []
                recording = False
                silence_counter = 0
