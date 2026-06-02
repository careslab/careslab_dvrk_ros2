import sounddevice as sd
from scipy.io.wavfile import write
from vosk import Model as VoskModel, KaldiRecognizer
import wave
import json

# Step 1: Record audio
fs = 16000
duration = 10
filename = "vosk_test.wav"
print("Recording for 10 seconds...")
recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
sd.wait()

# 💡 Convert float32 -> int16 so wave module can read it
import numpy as np
write(filename, fs, (recording * 32767).astype(np.int16))
print(f"Audio saved as {filename}")

# Step 2: Transcribe with Vosk
print("Transcribing with Vosk...")
wf = wave.open(filename, "rb")
vosk_model = VoskModel("model")  # Make sure the model folder is named exactly 'model'
rec = KaldiRecognizer(vosk_model, wf.getframerate())

vosk_text = ""
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        vosk_text += result.get("text", "") + " "
final_result = json.loads(rec.FinalResult())
vosk_text += final_result.get("text", "")
print("Vosk Transcript:", vosk_text.strip())
