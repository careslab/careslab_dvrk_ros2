import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import whisper
import os

# Step 1: Record audio
fs = 16000
duration = 10  # seconds
filename = "whisper_test.wav"
print("Recording for 10 seconds...")
recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
sd.wait()

# 💡 Convert float32 -> int16
write(filename, fs, (recording * 32767).astype(np.int16))
print(f"Audio saved as {filename}")

# Step 2: Transcribe with Whisper
print("Transcribing with Whisper...")
model = whisper.load_model("base")  # options: tiny, base, small, medium, large
result = model.transcribe(filename)
print("Whisper Transcript:", result["text"].strip())
