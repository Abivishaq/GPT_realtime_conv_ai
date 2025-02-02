import wave
import pyaudio
import numpy as np
import time

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000  # Playback rate
CHUNK = 1024  # Chunk size for playback and microphone

# Initialize PyAudio
p = pyaudio.PyAudio()

# Create playback audio stream
playback_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)

# Create input audio stream for microphone
mic_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

def calibrate_noise_level(duration=2):
    """
    Calibrates the ambient noise level by recording microphone input for a specified duration.

    Parameters:
        duration (int): Time in seconds to record and calculate the baseline noise level.

    Returns:
        float: The average noise level during the calibration period.
    """
    print("Calibrating noise level... Stay quiet.")
    levels = []
    start_time = time.time()
    while time.time() - start_time < duration:
        mic_data = np.frombuffer(mic_stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        levels.append(np.abs(mic_data).mean())
    noise_level = np.mean(levels)
    print(f"Calibrated noise level: {noise_level}")
    return noise_level

def detect_speech(threshold):
    """
    Detects speech by analyzing the microphone input's energy level.

    Parameters:
        threshold (float): Energy level above which speech is detected.

    Returns:
        bool: True if speech is detected, False otherwise.
    """
    mic_data = np.frombuffer(mic_stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
    energy = np.abs(mic_data).mean()
    return energy > threshold

def play_audio_with_detection(file_path, noise_level, sensitivity=2.0):
    """
    Plays an audio file in chunks and stops if speech is detected.

    Parameters:
        file_path (str): Path to the WAV audio file.
        noise_level (float): Calibrated noise level.
        sensitivity (float): Multiplier for the noise level to determine speech threshold.
    """
    speech_threshold = noise_level * sensitivity
    print(f"Speech detection threshold set to: {speech_threshold}")

    try:
        with wave.open(file_path, 'rb') as wf:
            print(f"Playing audio: {file_path}")

            # Check if audio file settings match the stream configuration
            if wf.getsampwidth() != p.get_sample_size(FORMAT) or \
               wf.getnchannels() != CHANNELS or \
               wf.getframerate() != RATE:
                print("Audio settings mismatch. Ensure the file matches the stream configuration.")
                return

            # Read and play audio in chunks
            data = wf.readframes(CHUNK)
            while data:
                # Check if speech is detected
                if detect_speech(speech_threshold):
                    print("Speech detected! Stopping playback.")
                    break

                playback_stream.write(data)
                data = wf.readframes(CHUNK)

            print("Playback finished.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Replace 'your_audio_file.wav' with the path to your WAV file
    audio_file = "output_audio.wav"

    # Calibrate ambient noise level
    ambient_noise_level = calibrate_noise_level()

    # Play audio with speech detection
    # play_audio_with_detection(audio_file, ambient_noise_level)

# Cleanup
playback_stream.close()
mic_stream.close()
p.terminate()
