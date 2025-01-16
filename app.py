from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent import ConversationManager
from vertex_ai import get_mental_health_response

app = FastAPI()
conversation_manager = ConversationManager()  # Initialize a global conversation manager

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserInput(BaseModel):
    prompt: str

@app.post("/api/mental-health")
async def mental_health(input: UserInput):
    """API endpoint to handle mental health prompts."""
    user_input = input.prompt
    if not user_input:
        raise HTTPException(status_code=400, detail="No input provided")

    response = await conversation_manager.process_input(user_input, get_mental_health_response)
    return {"response": response}

# Serve static files from the "frontend" directory
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)