import rclpy # ROS2
import time
import threading
from jibo_teleop_ros import JiboTeleop


class JiboROS:
    def __init__(self):
        rclpy.init()
        self.teleop_connection = JiboTeleop()
        morning_motion = 'Misc/greetings_09.keys'
        self.teleop_connection.send_motion_message(morning_motion)
        time.sleep(2)
    
    def send_tts_message(self, message):
        
        self.teleop_connection.send_tts_message(str(message))
        # time.sleep(2.0)
        # self.teleop_connection.waitforJibo()
    def destroy(self):
        self.teleop_connection.destroy()
        rclpy.shutdown()



# # Create a GPTFlow object
# gpt_flow = GptFlow()


# for i in range(10):
#     # get user input 
#     user_input = input("\nYou: ")
#     # check if user wants to exit
#     if user_input.lower() in ["bye", "exit", "quit"]:
#         print("\nAssistant: Goodbye!")
#         break
#     # add user input to messages
#     response = gpt_flow.single_interaction(user_input)
#     print("\nAssistant:", response)