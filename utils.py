import os
import time
import wave
import pyaudio

class Logger:
    def __init__(self,variant):
        self.variant = variant
        # get log no
        log_no_txt_fn = os.path.join(os.path.dirname(__file__), "logs", "log_no.txt")
        
        if not os.path.exists(log_no_txt_fn):
            log_fold = os.path.join(os.path.dirname(__file__), "logs")
            os.makedirs(log_fold, exist_ok=True)
            with open(log_no_txt_fn, "w") as f:
                f.write("0")
        with open(log_no_txt_fn, "r") as f:
            self.log_no = int(f.read())
        self.log_no += 1
        with open(log_no_txt_fn, "w") as f:
            f.write(str(self.log_no))
        
        # create log folder
        self.log_folder = os.path.join(os.path.dirname(__file__), "logs", f"log_{self.log_no}")
        os.makedirs(self.log_folder, exist_ok=True)
        
        # creta metadata file
        metadata_fn = os.path.join(self.log_folder, "metadata.txt")
        with open(metadata_fn, "w") as f:
            f.write("Log created at: " + time.ctime())
            f.write("\n\n")
            f.write("Log no: " + str(self.log_no))
            f.write("\n\n")
            f.write("Variant: " + self.variant)
            f.write("\n\n")
        
        # create transcript file
        self.transcript_fn = os.path.join(self.log_folder, "transcript.txt")

        # create Audio file
        self.assisant_audio_fn = os.path.join(self.log_folder, "assistant_audio.wav")
        self.mic_audio_fn = os.path.join(self.log_folder, "mic_audio.wav")
        self.assisant_audio_recorder = AudioRecorder(self.assisant_audio_fn)
        self.mic_audio_recorder = AudioRecorder(self.mic_audio_fn)
    
    def log_transcript(self, transcript):
        with open(self.transcript_fn, "a") as f:
            f.write(transcript)
            f.write("\n")
        
    def log_assistant_audio(self, audio_chunk):
        self.assisant_audio_recorder.save_chunk(audio_chunk)

    def log_mic_audio(self, audio_chunk):
        self.mic_audio_recorder.save_chunk(audio_chunk)

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


