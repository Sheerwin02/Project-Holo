import base64
import os
import re
import json
import time
from openai import OpenAI
from dotenv import load_dotenv
import requests
from utils import get_current_location, get_weather, get_news_updates 
import logging

# Registering the functions
#funcs = [get_current_location, get_weather, get_news_updates]

# Load environment variables
load_dotenv()

# Load OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY, timeout=600)

# Load or create a new assistant
def create_assistant(
        name="Assistant", 
        instructions="You are a helpful assistant.", 
        model="gpt-4o", 
        tools=None, 
        files=None, 
        debug=False
        ):
    """
    Creates an assistant with the given name, instructions, model, tools, and files.

    Args:
        name (str, optional): The name of the assistant. Defaults to "Assistant".
        instructions (str, optional): The instructions for the assistant. Defaults to "You are a helpful assistant.".
        model (str, optional): The model to use for the assistant. Defaults to "gpt-4-o".
        tools (list, optional): The list of tools to provide to the assistant. Defaults to None.
        files (list or str, optional): The list of files or a single file to upload and associate with the assistant. Defaults to None.

    Returns:
        str: The ID of the created assistant.
    """

    assistant_file_path = "assistant.json"
    assistant_json = []

    # Check if assistant file exists
    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, "r") as f:
            assistant_json = json.load(f)

            for assistant_data in assistant_json:
                assistant_name = assistant_data["assistant_name"]
                if assistant_name == name:
                    assistant_id = assistant_data["assistant_id"]
                    print("Loaded existing assistant with ID:", assistant_id)

                    if debug:
                        print(f"Assistant '{name}' already exists with ID: {assistant_id}")

                    return assistant_id
                
    # Upload files to get file IDs
    file_ids = []
    if files:
        if isinstance(files, list):
            for file in files:
                file = client.files.create(
                    file=open(file, "rb"),
                    purpose='user_data'  # Change purpose to a valid option
                )
                file_ids.append(file.id)
        elif isinstance(files, str):
            file = client.files.create(
                file=open(files, "rb"),
                purpose='user_data'  # Change purpose to a valid option
            )
            file_ids.append(file.id)

    # Create assistant
    assistant = client.beta.assistants.create(
        name=name,
        instructions=instructions,
        model=model,
        tools=tools
        #files=file_ids
    )

    assistant_id = assistant.id
    assistant_name = assistant.name

    # Save assistant data to json
    assistant_json.append(
        {
            "assistant_name": assistant_name,
            "assistant_id": assistant_id
        }
    )

    with open(assistant_file_path, "w", encoding="utf-8") as file:
        json.dump(assistant_json, file, ensure_ascii=False, indent=4)
        print("Assistant data saved to:", assistant_file_path)
        
    return assistant_id

# Create thread
def create_thread(debug=False):
    """
    Creates a new thread.

    Returns:
        str: The ID of the created thread.
    """

    thread = client.beta.threads.create()

    thread_id = thread.id

    if debug:
        print("Created new thread with ID:", thread_id)

    return thread_id

# Get response from assistant
def get_completion(assistant_id, thread_id, user_input, funcs, debug=False):
    """
    Executes a completion request with the given parameters.

    Args:
        assistant_id (str): The ID of the assistant.
        thread_id (str): The ID of the thread.
        user_input (str): The user input content.
        funcs (list): A list of functions.
        debug (bool, optional): Whether to print debug information. Defaults to False.

    Returns:
        str: The message as a response to the completion request.
    """

    if debug:
        print("Getting completion for user input:", user_input)

    # Create message
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input
    )

    # Create run
    run = client.beta.threads.runs.create(
      thread_id=thread_id,
      assistant_id=assistant_id,
    )

    # Run
    while True:
        while run.status in ['queued', 'in_progress']:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if debug:
                print("Run status:", run.status)
            time.sleep(1)
        
        if run.status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []

            for tool_call in tool_calls:
                if debug:
                    print("Tool call function:", tool_call.function)
                try:
                    func = next(iter([func for func in funcs if func.__name__ == tool_call.function.name]))
                    try:
                        output = func(**eval(tool_call.function.arguments))
                    except Exception as e:
                        output = "Error: " + str(e)

                    if debug:
                        print(f"{tool_call.function.name}: ", output)
                    
                    tool_outputs.append(
                        {
                            "tool_call_id": tool_call.id, 
                            "output": json.dumps(output)
                        }
                    )

                except StopIteration:
                    if debug:
                        print(f"No matching function for {tool_call.function.name}")
                    continue  # Skip this tool call if no matching function is found
                    
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )

        elif run.status == "failed":
            raise Exception("Run Failed. Error: ", run.last_error)
        
        else:
            messages = client.beta.threads.messages.list(
                thread_id=thread_id
            )
            message = messages.data[0].content[0].text.value
            pattern = r"/imgs/\d{10}\.png"
            match = re.search(pattern, message)
            if match:
                message = {"image": match.group()}
            if debug:
                print(message)
            return message
        
# AI Scheduler 
def suggest_time_for_event(assistant_id, thread_id, event_description, duration_minutes, funcs, debug=False):
    prompt = f"""
    I need to schedule an event: {event_description}.
    The event should last for {duration_minutes} minutes.
    Please suggest an optimal time based on my availability.
    """
    return get_completion(assistant_id, thread_id, prompt, funcs, debug)

# Function to upload file and analyze it
def analyze_file(assistant_id, thread_id, file_path, funcs, debug=False):
    # Upload the file
    try:
        file = client.files.create(
            file=open(file_path, "rb"),
            purpose='user_data'  # Change purpose to a valid option
        )
        file_id = file.id

        if debug:
            logging.info(f"File uploaded successfully with ID: {file_id}")
    except Exception as e:
        logging.error(f"Error uploading file: {e}")
        return f"Error uploading file: {e}"

    # Create message with the uploaded file
    try:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content="Please analyze the attached file.",
            attachments=[{
                "file_id": file_id,
                "tools": [{"type": "file_search"}]  # Add the required tools parameter with type as an object
            }]
        )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )

        # Poll for the run status
        while True:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for tool_call in tool_calls:
                    func = next(iter([func for func in funcs if func.__name__ == tool_call.function.name]))
                    output = func(**json.loads(tool_call.function.arguments))
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(output)
                    })

                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )

            elif run.status == "completed":
                messages = client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                message = messages.data[-1].content
                return message

            elif run.status == "failed":
                raise Exception(f"Run failed with error: {run.last_error}")

            time.sleep(1)

    except Exception as e:
        logging.error(f"Error analyzing file: {e}")
        return f"Error analyzing file: {e}"

# Function to analyze the image
def analyze_image(file_path, debug=False):

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please give feedback on what's you seeing and chat with the user like an human assistant with emotion, your reply is short and people will enjoy chatting with you."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{file_path}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response_json = response.json()

        if debug:
            logging.info(f"OpenAI API response: {response_json}")

        message_content = response_json['choices'][0]['message']['content']
        return message_content

    except Exception as e:
        logging.error(f"Error analyzing image: {e}")
        return f"Error analyzing image: {e}"