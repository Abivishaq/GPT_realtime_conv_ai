import wave
import pyaudio

class AudioRecorder:
    def __init__(self, filename="output.wav", format=pyaudio.paInt16, channels=1, rate=24000):
        self.filename = filename
        self.format = format
        self.channels = channels
        self.rate = rate
        
        self.wav_file = wave.open(self.filename, "wb")
        self.wav_file.setnchannels(self.channels)
        self.wav_file.setsampwidth(pyaudio.PyAudio().get_sample_size(self.format))
        self.wav_file.setframerate(self.rate)

    def save_chunk(self, audio_chunk):
        """Write an audio chunk to the WAV file."""
        self.wav_file.writeframes(audio_chunk)

    def close(self):
        """Close the WAV file."""
        self.wav_file.close()


# Function to record audio for testing
def record_audio(recorder, duration=5, chunk=1024):
    """Record audio from the microphone and save it using the provided recorder."""
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=24000,
                    input=True,
                    frames_per_buffer=chunk)

    print(f"Recording for {duration} seconds...")
    for _ in range(0, int(24000 / chunk * duration)):
        audio_chunk = stream.read(chunk)
        recorder.save_chunk(audio_chunk)

    print("Recording complete.")
    stream.stop_stream()
    stream.close()
    p.terminate()


# Example usage:
if __name__ == "__main__":
    recorder = AudioRecorder("test_audio.wav")
    try:
        record_audio(recorder, duration=5)  # Record for 5 seconds
    finally:
        recorder.close()
