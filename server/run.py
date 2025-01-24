import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from instructions import holo_instructions
# from functions import get_city_for_date, get_qa
from assistant import create_assistant, create_thread, get_completion
from utils import get_current_location, get_weather, get_news_updates

# List of functions
funcs = [get_current_location, get_weather, get_news_updates]
# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cuztomize data model
class ChatMessage(BaseModel):
    user_input: str
    thread_id: str

DEBUG = True

# Create assistant
assistant_id = create_assistant(
    name="Holo",
    instructions=holo_instructions,
    model="gpt-4o",
    tools=[
    # {
    #     "type": "retrieval"   
    # },
    {
        "type": "code_interpreter"  
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_location",
            "description": "Get the current geographical location of the user based on IP address.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for the specified location. The assistant will give advice based on the weather and it will also advice the users weather is suitable to go out or not.",
            "parameters": {
                "type": "object",
                "properties": {
                    # "city": {
                    #     "type": "string",
                    #     "description": "The city for which to get the weather."
                    # }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_updates",
            "description": "Get the latest news updates on a given topic in a short summary. The assistant will reply in a short sentence",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic for which to get the news updates."
                    }
                },
                "required": ["topic"]
            }
        }
    },
],
    #files=["./files/holo.jpg"]
)

## TEST ROOT
@app.get("/")
async def root():
    return {"message": "Welcome to the Holo Assistant API!"}

@app.get("/create_thread")
async def create_thread_endpoint():
    # Create Thread
    thread_id = create_thread(debug=DEBUG)
    return {"thread_id": thread_id}

@app.post("/chat")
async def chat_endpoint(request: ChatMessage):
    # Get response
    message = main(request.user_input, request.thread_id, debug=DEBUG)
    return {
        "message": message
    }

def main(query, thread_id, debug=False):
    # Functions
    message = get_completion(assistant_id, thread_id, query, funcs, debug)
    return message


if __name__ == "__main__":
    uvicorn.run(app, port=8000)