import os
import json
import base64
import wave
import websocket
import pyaudio
import threading
import queue
import numpy as np
from collections import deque
import time

class InteractionAnalyzer:
    def __init__(self):
        self.person_audio_chunk_size = 0
        self.assistant_audio_chunk_size = 0
        self.no_questions = 0
    
    def add_person_audio_chunk(self, audio_chunk):
        self.person_audio_chunk_size += len(audio_chunk)
    
    def add_assistant_audio_chunk(self, audio_chunk):
        self.assistant_audio_chunk_size += len(audio_chunk)
    
    def get_ratio(self):
        return self.person_audio_chunk_size / self.assistant_audio_chunk_size
    
    def question_tracker(self, transcript):
        # Check if the user asked a question
        if "?" in transcript:
            self.no_questions += 1
    
    def get_no_questions(self):
        return self.no_questions

class RealtimeAssistant:
    def __init__(self, api_key=None, model="gpt-4o-realtime-preview-2024-12-17",
                 format=pyaudio.paInt16, channels=1, rate=24000, chunk=1024,
                 output_audio_file="output_audio.wav", silence_duration=0.8,
                 energy_threshold=500, dynamic_thresholding=True):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in environment variables.")

        self.url = f"wss://api.openai.com/v1/realtime?model={model}"
        self.headers = [
            f"Authorization: Bearer {self.api_key}",
            "OpenAI-Beta: realtime=v1",
        ]
    
        self.current_response_id = None
        self.current_assistant_item_id = None
        self.playback_position = 0  # Track played audio duration in ms
        self.playback_start = 0  # Total duration of played audio in ms
        self.pause_for_user = False


        # Audio configuration
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.silence_frames = int(silence_duration * rate / chunk)
        
        # Voice activity detection
        # self.energy_threshold = energy_threshold
        # self.dynamic_thresholding = dynamic_thresholding
        # self.energy_window = deque(maxlen=10)  # 10-chunk (~100ms) moving average
        # self.silence_counter = 0
        # self.is_speaking = False
        # self.audio_buffer = []

        # Audio file output
        self.output_audio_file = output_audio_file

        # Audio processing
        self.p = pyaudio.PyAudio()
        self.audio_stream = None
        self.wav_file = None

        # Threading components
        self.playback_queue = queue.Queue()
        self.recording_thread = None
        self.playback_thread = None
        self.is_recording = False

        ######### TMP ##################
        self.I1 = "Talk like Yoda"
        self.I2 = "Talk like a pirate"

        ##############################

        # WebSocket connection
        self.ws = websocket.WebSocketApp(
            self.url,
            header=self.headers,
            on_open=lambda ws: self.on_open(ws),
            on_message=lambda ws, msg: self.on_message(ws, msg),
            on_error=lambda ws, error: self.on_error(ws, error),
            on_close=lambda ws, code, msg: self.on_close(ws, code, msg),
        )
    def swap_instructions(self):
        tmp = self.I1
        self.I1 = self.I2
        self.I2 = tmp
        self.update_instructions(self.I1)

    def run(self):
        """Start the real-time assistant connection."""
        self.wav_file = wave.open(self.output_audio_file, "wb")
        self.wav_file.setnchannels(self.channels)
        self.wav_file.setsampwidth(self.p.get_sample_size(self.format))
        self.wav_file.setframerate(self.rate)

        self.audio_stream = self.p.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            output=True
        )

        # Start playback thread
        self.playback_thread = threading.Thread(target=self.playback_audio)
        self.playback_thread.start()

        self.ws.run_forever()

    def on_open(self, ws):
        """Handle WebSocket connection opening."""
        print("Connected to the Realtime API.")
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "instructions": "Play the role of a table top robot called Jibo. You are specifically called Alex. Be proactive and engage the user, keep the conversation going and don't let it die. You can start of with hobbies and naturally go with the conversation flow. About Jibo: Can engange only engage in coversations. And moves aroud randomly while talking.",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.7,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 1000
                },
                "voice": "ash",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
            },
        }
        self.ws.send(json.dumps(session_config))
        print("Session configured.")
        
        # Start continuous recording in a separate thread
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self.record_and_send_audio)
        self.recording_thread.start()

    def on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        data = json.loads(message)

        
        if data["type"] == "response.audio.delta":
            audio_chunk = base64.b64decode(data["delta"])
            self.playback_queue.put(audio_chunk)
            
        elif data["type"] == "input_audio_buffer.speech_started":
            print("Speech detected")
            self.pause_for_user = True
            # self.handle_interrupt()
        elif data["type"] == "input_audio_buffer.speech_stopped":
            print("Speech ended")
            self.pause_for_user = False
            self.swap_instructions()

        elif data["type"] == "response.done":
            print("Response generation completed.")
            self.current_response_id = None
            self.current_assistant_item_id = None
        
        elif data["type"] == "response.created":
            print("Response created.")
            self.current_response_id = data["event_id"]
            
        elif data["type"] == "conversation.item.created":
            print("data", data)
            if data["item"]["role"] == "assistant":
                self.current_assistant_item_id = data["item"]["id"]
                print(f"Tracking assistant item: {self.current_assistant_item_id}")
                self.playback_start = time.time()
                
        elif data["type"] == "error":
            print(f"Error: {data['error']['message']}")

        elif data["type"] == "response.audio_transcript.delta":
            print(f"Transcript: {data['delta']}")

            
        else:
            print(f"Unhandled message type: {data['type']}")
            pass

    def update_instructions(self, instructions):
        """Update the session instructions."""
        event = {
            "type": "session.update",
            "session": {
                "instructions": instructions,
            },
        }
        self.ws.send(json.dumps(event))

    def record_and_send_audio(self):
        """Continuously record audio with voice activity detection."""
        print("Recording... Speak now (Ctrl+C to stop).")
        try:
            input_stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )

            while self.is_recording:
                # Read audio chunk
                audio_data = input_stream.read(self.chunk, exception_on_overflow=False)

                # Calculate energy and detect speech
                self.send_audio(audio_data)

        except Exception as e:
            if self.is_recording:
                print(f"\nRecording error: {e}")
        finally:
            if input_stream:
                input_stream.stop_stream()
                input_stream.close()

    def send_audio(self,audio_chunk):
        """Send accumulated audio and clear buffer."""
        if not audio_chunk:
            return

        # combined_audio = b''.join(self.audio_buffer)
        event = {
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(audio_chunk).decode("utf-8"),
        }
        self.ws.send(json.dumps(event))
        # self.ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
        # self.audio_buffer.clear()

    def playback_audio(self):
        """Continuously play audio from the playback queue."""
        try:
            while True:
                if self.pause_for_user:
                    #clear the queue
                    print("Pausing audio")
                    while not self.playback_queue.empty():
                        print("Clearing audio queue")
                        self.playback_queue.get()
                    continue
                else:
                    print("Playing audio")
                audio_chunk = self.playback_queue.get()
                if audio_chunk is None:
                    break
                
                # Calculate duration of this chunk in ms
                duration_ms = (len(audio_chunk) / (self.rate * 2)) * 1000  # PCM16: 2 bytes/sample
                self.playback_position += int(duration_ms)
                
                self.audio_stream.write(audio_chunk)
                self.wav_file.writeframes(audio_chunk)
                with open("output_audio.pcm", "ab") as pcm_file:
                    pcm_file.write(audio_chunk)
        except Exception as e:
            print(f"Playback error: {e}")

    def on_error(self, ws, error):
        """Handle WebSocket errors."""
        print(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection closing."""
        print("\nConnection closed.")
        self.is_recording = False
        
        # Cleanup threads
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join()

        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_queue.put(None)
            self.playback_thread.join()

        # Close audio resources
        if self.wav_file:
            self.wav_file.close()
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        self.p.terminate()

if __name__ == "__main__":
    assistant = RealtimeAssistant(
        energy_threshold=300,  # Initial energy threshold
        silence_duration=0.8,  # Seconds of silence to consider speech ended
        dynamic_thresholding=False  # Auto-adjust to ambient noise
    )
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        assistant.ws.close()