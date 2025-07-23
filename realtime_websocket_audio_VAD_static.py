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
from jiboROS import JiboROS
from utils import Logger, AudioRecorder
from prompts import base_prompt_static


### Global configuration
variant = "Static"
# basic_prompt = "Play the role of a robot called Jibo. \
#     You are specifically called Alex. Be proactive and engage the user, \
#     keep the conversation going and don't let it die. You can start of with hobbies and naturally go with the conversation flow. \
#         About Jibo: Can engange only engage in coversations. And moves aroud randomly while talking. \
#                 Cannot do any tasks it is a simple embodied conversational agent.\
#         FOLLOW THESE INSTRUCTIONS: Wait for the user to respond before you speak. Use mms and ahh or other acknoledgement sounds when user is describing things."

# basic_prompt = "Play the role of a robot called Jibo. \
#     You are specifically called Alex. Be proactive and engage the user, \
#     keep the conversation going and don't let it die. You can start of with hobbies and naturally go with the conversation flow. Avoid offering help since you are a conversational agent. So you focus asking user to help recall things. \
#     Talk for 1 mins and slowly end the conversation.\
#     Talk less and try to get the user to shaer more particularly something that requires recalling memory.\
#         About Jibo: Can engange only engage in coversations. And moves aroud randomly while talking. \
#                 Cannot do any tasks it is a simple embodied conversational agent."

# basic_prompt = "Play the role of a robot called Jibo. \
#     You are specifically called Alex. Be proactive and engage the user, \
#     keep the conversation going and don't let it die. You can start with some small talk and then go to 'what did you buy in last grocery?' and naturally go with the conversation flow. Avoid offering help since you are a conversational agent. So you focus asking user to help recall things. \
#     Talk for 1 mins and slowly end the conversation.\
#     Talk less and try to get the user to share more particularly something that requires recalling memory.\
#         About Jibo: Can engage only engage in coversations. And moves aroud randomly while talking. \
#                 Cannot do any tasks it is a simple embodied conversational agent.\
#         About the interaction: You are talking to people for a user study." 
# Topic_1 = "What did you buy in last grocery?"
# Topic_2 = "What is your favorite food?"
# Topic_3 = "What is your favorite movie?"
# A_connect_prompt = f"You are an moderator and is within a phone call session with the user. The user is an old person, who\
#                     might have Mild Cognitive Impairment (MCI). Follow the below instructions to be a nice, patiently and\
#                     helpful moderator that stimulate the user's memory and help execute cognitive functions.\n\
#                     You should follow this steps in your conversation:\n\
#                         0. Warm up by asking the name of the user gently and nicely. Then remember to call him/her by name.\n\
#                         1. After few rounds of warm up, you have to ask the user to make selection of the following three topics:\n\
#                         (1) {Topic_1}, (2) {Topic_2} and (3) {Topic_3}. You can inform the user to check the images on the\
#                         screen. Whenever you ask the user to select topics, you have to present all topic images.\n\
#                     You have to obey the guidelines:\n\
#                         - If the user cannot speak logically, the assistant should let the user pause for a while, and help him\
#                             sort out his/her memory, logically. // Assistant patients to organize words.\n\
#                                 - The assistant should NOT speak too many words each time. The assistant should give more time for the \
#                                     user to speak (and encourage the user to speak more). // Avoid to be talky.\n\
#                                 - You should stimulate the user's memory (by using reminiscence of old events in their lives, as well as \
#                                     recalling the topic discussed earlier in the session). For example, kindly ask him if he/she remember \
#                                     earlier events related to the current topic. // This is to help improve the patient's cognitive ability."
# basic_prompt = A_connect_prompt
# basic_prompt = f"""You are an conversational robot called Jibo having a conversation with the user. Play the role of a person called Sam.
# You are very cheerful happy and eloquent speaker. You can carry out conversations smoothly.
# Follow the below instructions to be a nice, patient and helpful conversational robot.
# You should follow these steps in your conversation:
#     0. Warm up by asking the name of the user gently and nicely. Then remember to call him/her by name.
#         - Once the user is engaged in conversation, smoothly transition into a topic selection.
# 		- Avoid abrupt transitions. Instead, connect the topics naturally to what was previously discussed.
#     1. After few rounds of warm up, you have to ask the user to make selection of the following three topics:
#         (1) {Topic_1}, 
#         (2) {Topic_2} and 
#         (3) {Topic_3}. 
# Whenever you ask the user to select topics, you have to present all topic images.
# You have to obey the following guidelines:
#     - If the user cannot speak logically, the robot should let the user pause for a while, and help him sort out his/her memory, logically Assist patients to organize words.\n
#     - The robot should NOT speak too many words each time preferably a sentence. The robots should give more time for the user to speak (and encourage the user to speak more). Avoid being talkative.\n
#     - You should stimulate the user's memory (by using reminiscence of old events in their lives, as well as recalling the topic discussed earlier in the session). If possible try to encourage the user to talk about relevant events or experiences from their past. This is to help improve the patient's cognitive ability.
#     - The robot should have human like conversations.
#     - Try not to affirm the user's words, directly go to the question or opinion.
#     - Avoid directly affirming the user’s words; instead, ask follow-up questions or seek their opinion to keep the conversation dynamic and engaging.
#     - Be polite but not formal. Be friendly and approachable. Like talking to a friend.
#     - Avoid restating or affirming the user's words. Instead, keep the conversation flowing naturally by asking engaging follow-up questions. 
#       Don't use filler affirmations like "That sounds amazing!" or “Vacations are always refreshing.”
#       Skip broad statements about the user's topic. These are not typical in casual conversations and can feel repetitive or condescending.
#       Go straight to a question or show curiosity. Use phrases like:
#         --“Oh? Tell me more!”
#         --“Where was that?”
#         --“How did that go?”
#         --“What was that like for you?”
#     - Ocassionally, acts as if you are unfamilar with the topic and ask the user to explain more.
#     - Instead of affirming knowledge ask curious and engaging questions to encourage the user to speak more.
#     - Have short conversation allowing more turn taking.
#     - Behave like a humans and you have some made experiences to share."""
# basic_prompt = "Talk less. Ask one question at a time. wait for the user to respond before you speak. Guide the conversation ask the user about their hobbies or interest."
basic_prompt = base_prompt_static

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

class InteractionAnalyzer:
    def __init__(self):
        self.mic_audio_chunk_size = 0
        self.assistant_audio_chunk_size = 1 # just to avoid division by zero
        self.no_questions = 0
        # self.mic_recorder = AudioRecorder("mic_audio.wav")
        # self.assistant_recorder = AudioRecorder("assistant_audio.wav")
    
    def add_mic_audio_chunk(self, audio_chunk):
        # print("type of audio_chunk", type(audio_chunk))
        # check energy of audio_chunk
        # energy = np.sum(np.frombuffer(audio_chunk, dtype=np.int16)**2)
        # print("energy", energy)
        self.mic_audio_chunk_size += len(audio_chunk)
        # self.mic_recorder.save_chunk(audio_chunk)
    
    def add_assistant_audio_chunk(self, audio_chunk):
        # print("type of audio_chunk", type(audio_chunk))
        self.assistant_audio_chunk_size += len(audio_chunk)
        # self.assistant_recorder.save_chunk(audio_chunk)
    
    def get_ai_ratio(self):
        return(self.assistant_audio_chunk_size/(self.mic_audio_chunk_size+self.assistant_audio_chunk_size))
    
    def question_tracker(self, transcript):
        # Check if the ai asked a question
        if "?" in transcript:
            self.no_questions += 1
    
    def get_no_questions(self):
        return self.no_questions
    
    def close(self):
        pass
        # self.person_recorder.close()
        # self.assistant_recorder.close()
    
class JiboHandler:
    def __init__(self):
        self.jibo_ros = JiboROS()
        self.txt = ''
    def add_text(self, text):
        self.txt += text
        if ('.' in text) or ('?' in text) or ('!' in text):
            print(self.txt)
            self.jibo_ros.send_tts_message(self.txt)
            self.txt = ''


class RealtimeAssistant:
    def __init__(self, api_key=None, model="gpt-4o-realtime-preview-2024-12-17",
                 format=pyaudio.paInt16, channels=1, rate=24000, chunk=1024,
                 output_audio_file="output_audio.wav", silence_duration=0.8,
                 energy_threshold=500, dynamic_thresholding=True):
    
        self.should_exit = False
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in environment variables.")
        
        self.logger = Logger(variant=variant)

        self.url = f"wss://api.openai.com/v1/realtime?model={model}"
        self.headers = [
            f"Authorization: Bearer {self.api_key}",
            "OpenAI-Beta: realtime=v1",
        ]

        self.jibo = JiboHandler()
        self.interaction_analyzer = InteractionAnalyzer()

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
        # self.I1 = "Talk like Yoda"
        # self.I2 = "Talk like a pirate"
        # self.I1 = 'only reply in one word'
        # self.I2 = self.I1 #'reply in full sentences'
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
    # def swap_instructions(self):
    #     tmp = self.I1
    #     self.I1 = self.I2
    #     self.I2 = tmp
    #     self.update_instructions(self.I1)
    

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
                "instructions": basic_prompt,
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.95,
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
            self.interaction_analyzer.add_assistant_audio_chunk(audio_chunk)
            self.logger.log_assistant_audio(audio_chunk)

        elif data["type"] == "input_audio_buffer.speech_started":
            print("Speech detected")
            self.pause_for_user = True
            # self.handle_interrupt()
        elif data["type"] == "input_audio_buffer.speech_stopped":
            print("Speech ended")
            self.pause_for_user = False
            ratio = self.interaction_analyzer.get_ai_ratio()
            print(f"Ratio of user to assistant audio: {ratio}")
            # self.swap_instructions()

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
            # print(f"Transcript: {data['delta']}")
            self.jibo.add_text(data['delta'])
            self.logger.log_transcript(data['delta'])
            # self.interaction_analyzer.add_assistant_audio_chunk(data['delta'])
            
        else:
            # print(f"Unhandled message type: {data['type']}")
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
                self.interaction_analyzer.add_mic_audio_chunk(audio_data)
                self.logger.log_mic_audio(audio_data)

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
            while not self.should_exit:
                if self.pause_for_user:
                    #clear the queue
                    # print("Pausing audio")
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
        self.cleanup()
        # print("\nConnection closed.")
        # self.is_recording = False
        
        # # Cleanup threads
        # if self.recording_thread and self.recording_thread.is_alive():
        #     self.recording_thread.join()

        # if self.playback_thread and self.playback_thread.is_alive():
        #     self.playback_queue.put(None)
        #     self.playback_thread.join()

        # # Close audio resources
        # if self.wav_file:
        #     self.wav_file.close()
        # if self.audio_stream:
        #     self.audio_stream.stop_stream()
        #     self.audio_stream.close()
        # self.p.terminate()
        # self.interaction_analyzer.close()
        # print("Audio resources released.")
    
    def cleanup(self):
        print("\nCleaning up...")
        self.should_exit = True
        self.is_recording = False

        # Stop and join recording thread
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join()

        # Stop and join playback thread
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_queue.put(None)
            self.playback_thread.join()

        # Close WebSocket
        if self.ws:
            try:
                self.ws.close()
            except:
                pass

        # Close audio resources
        if self.wav_file:
            self.wav_file.close()
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        self.p.terminate()
        self.interaction_analyzer.close()
        print("Cleanup complete.")

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
        # assistant.ws.close()
        assistant.cleanup()