import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def create_thread():
    response = requests.get(f"{BASE_URL}/create_thread")
    if response.status_code == 200:
        return response.json()["thread_id"]
    else:
        print(f"Error creating thread: Status code {response.status_code}")
        print(f"Response: {response.text}")
        return None

def chat_with_assistant(thread_id, user_input):
    payload = {
        "user_input": user_input,
        "thread_id": thread_id
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(f"{BASE_URL}/chat", headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json()["message"]
    else:
        print(f"Error in chat request: Status code {response.status_code}")
        print(f"Response: {response.text}")
        return None

if __name__ == "__main__":
    thread_id = create_thread()
    if thread_id:
        print(f"New thread created with ID: {thread_id}")
        while True:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Ending the chat. Goodbye!")
                break
            response = chat_with_assistant(thread_id, user_input)
            if response:
                print(f"Assistant: {response}")
            else:
                print("Failed to get response from assistant")
    else:
        print("Failed to create a new thread. Exiting.")
