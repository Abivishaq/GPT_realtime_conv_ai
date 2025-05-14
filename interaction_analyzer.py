
import numpy as np

import time

from utils import Logger, AudioRecorder

from prompts import base_prompt


class InteractionAnalyzer:
    def __init__(self,logger):
        self.mic_audio_chunk_size = 0
        self.assistant_audio_chunk_size = 1 # just to avoid division by zero
        self.no_questions = 0
        self.no_user_inputs = 0
        self.time_start = time.time()
        self.target_time = 60*14 # 15 mins
        self.logger = logger # Sync the logger from RealtimeAssistant
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
        return(self.assistant_audio_chunk_size/self.mic_audio_chunk_size)
    
    def question_tracker(self, transcript):
        # Check if the user asked a question
        if "?" in transcript:
            self.no_questions += 1
    
    def update_user_input_count(self):
        self.no_user_inputs += 1
    
    def get_question_ratio(self):
        print("__"*50)
        print("no_user_inputs", self.no_user_inputs)
        print("^"*50)
        if self.no_user_inputs == 0:
            # raise ValueError("No user inputs recorded yet.")
            print("No user inputs recorded yet.")
            return 0
        print("no_questions", self.no_questions)
        print("Q_ratio", self.no_questions/self.no_user_inputs)
        return self.no_questions/self.no_user_inputs
        # return self.no_questions
    
    def get_updated_instructions(self):
        # length control
        instructions = ""
        ai_ratio = self.get_ai_ratio()
        print("ai_ratio", ai_ratio)
        time_now = time.time()
        # if time_now - self.time_start > self.target_time :
        #     instructions += "You have been talking for too long. Try to wrap up the conversation. Say bye."
        #     print("#"*50)
        #     print("Time to wrap up")
        #     print("#"*50)
        ai_ratio_threshold = 0.5
        if ai_ratio > ai_ratio_threshold:
            instructions += "RESPOND WITH ONLY ONE SENTENCE WITH A MAXIMUM OF 10 WORDS."
            # instructions += "Speak like a pirate."
            print("#"*50)
            print("It is in speak less mode:")
        else:
            instructions += "Try to share a experience."
            # instructions += "talk like a pirate"
            print("*"*50)
            print("It is in speak more mode:")
        question_ratio = self.get_question_ratio()
        print("question_ratio", question_ratio)
        if question_ratio > 0.5:
            instructions += "Don't ask a question."
        if question_ratio < 0.3:
            instructions += "Ask more questions to keep the conversation going."

        self.logger.log_metrics(self.no_user_inputs, ai_ratio, question_ratio)
        
        instructions = base_prompt + instructions
        return instructions
    
    def close(self):
        pass
        # self.person_recorder.close()
        # self.assistant_recorder.close()