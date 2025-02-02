import base64
import io
import time  # Import time module for measuring execution time
from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play

# Initialize OpenAI client
start_time = time.time()
client = OpenAI()
print(f"Client initialization: {time.time() - start_time:.4f} seconds")

# Generate completion with audio
start_time = time.time()
completion = client.chat.completions.create(
    model="gpt-4o-audio-preview",
    modalities=["text", "audio"],
    audio={"voice": "alloy", "format": "wav"},
    messages=[
        {
            "role": "user",
            "content": "Is a golden retriever a good family dog?"
        }
    ]
)
print(f"API completion generation: {time.time() - start_time:.4f} seconds")

# Decode the audio data
start_time = time.time()
wav_bytes = base64.b64decode(completion.choices[0].message.audio.data)
print(f"Audio decoding: {time.time() - start_time:.4f} seconds")

# Convert the audio bytes into an AudioSegment object
start_time = time.time()
audio = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
print(f"AudioSegment conversion: {time.time() - start_time:.4f} seconds")

# Play the audio directly
start_time = time.time()
play(audio)
print(f"Audio playback: {time.time() - start_time:.4f} seconds")
