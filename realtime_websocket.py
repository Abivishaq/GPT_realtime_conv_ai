import os
import json
import websocket

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# WebSocket URL and headers
url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
headers = [
    f"Authorization: Bearer {OPENAI_API_KEY}",
    "OpenAI-Beta: realtime=v1",
]

# Maintain session and conversation state
conversation_id = None
conversation_items = []
current_response_text = ""

# WebSocket event handlers
def on_open(ws):
    """Called when WebSocket connection is opened."""
    print("Connected to the Realtime API.")

    # Configure the session
    session_update_event = {
        "type": "session.update",
        "session": {
            "modalities": ["text"],
            "instructions": "You are a helpful assistant.",
            "temperature": 0.7,
        },
    }
    ws.send(json.dumps(session_update_event))
    print("Session configured.")

    # Start the conversation loop
    get_user_input(ws)

def on_message(ws, message):
    """Called when a message is received from the server."""
    global conversation_id, conversation_items, current_response_text

    print(f"Received message: {message}")
    data = json.loads(message)

    if data["type"] == "session.created":
        print("Session created.")
        conversation_id = data["session"]["id"]
        print(f"Conversation ID: {conversation_id}")

    elif data["type"] == "session.updated":
        print("Session updated.")

    elif data["type"] == "conversation.item.created":
        if data["item"]["role"] == "user":
            print("User message acknowledged.")
        elif data["item"]["role"] == "assistant":
            print("Assistant response acknowledged.")
            conversation_items.append(data["item"])

    elif data["type"] == "response.text.delta":
        # Handle streaming text
        delta = data.get("delta", "")
        current_response_text += delta
        print(f"Streaming: {current_response_text}")

    elif data["type"] == "response.text.done":
        # Finalize the assistant response
        final_text = data["text"]
        print(f"GPT (final): {final_text}")
        current_response_text = ""  # Reset for next response
        get_user_input(ws)

    elif data["type"] == "response.done":
        print("Response generation completed.")

    elif data["type"] == "error":
        print(f"Error: {data['error']['message']}")

    else:
        print("Unhandled message type.")

def get_user_input(ws):
    """Prompt for user input and send it to the server."""
    global conversation_items

    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Ending the chat. Goodbye!")
        ws.close()
        return

    # Create a user message in the conversation
    user_message_event = {
        "type": "conversation.item.create",
        "item": {
            "id": f"msg_{len(conversation_items) + 1}",
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": user_input}],
        },
    }
    ws.send(json.dumps(user_message_event))

    # Request a response from the model
    response_event = {
        "type": "response.create",
        "response": {
            "modalities": ["text"],
            "instructions": "Respond to the user message.",
        },
    }
    ws.send(json.dumps(response_event))

def on_error(ws, error):
    """Called when an error occurs."""
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    """Called when the WebSocket connection is closed."""
    print("WebSocket connection closed.")

# Create and run the WebSocket client
ws = websocket.WebSocketApp(
    url,
    header=headers,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
)

ws.run_forever()
