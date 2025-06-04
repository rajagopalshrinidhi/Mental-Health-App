from pydantic_ai import Agent, ModelRetry
from pydantic_ai.models.vertexai import VertexAIModel
from pydantic import BaseModel
import os

# --- Google Cloud Configuration ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
LOCATION = "us-central1"
MODEL = "gemini-2.5-flash-preview-05-20"

# Validate environment variables
if not PROJECT_ID or not SERVICE_ACCOUNT_FILE:
    raise ValueError("Environment variables GOOGLE_CLOUD_PROJECT and GOOGLE_APPLICATION_CREDENTIALS must be set.")

class MentalHealthResponse(BaseModel):
    text: str

class MentalHealthAgent(Agent):
    model = VertexAIModel(
        model_name=MODEL,
        service_account_file=SERVICE_ACCOUNT_FILE,
        project_id=PROJECT_ID,
        region=LOCATION,
    )
    result_type = MentalHealthResponse

    system_prompt = """
        You are a mental health companion providing empathetic and supportive responses.
        You should not answer any technical, mathematical, or unrelated questions.
        Keep the conversation focused on mental health and well-being.
    """

    @staticmethod
    def validate_response(response: MentalHealthResponse) -> MentalHealthResponse:
        if not response:
            # Log the error for debugging
            print("Empty response received. Retrying...")
            raise ModelRetry("The response is empty.")
        return response

async def get_mental_health_response(prompt: str) -> str:
    agent = MentalHealthAgent(model=VertexAIModel(
        model_name=MODEL,
        service_account_file=SERVICE_ACCOUNT_FILE,
        project_id=PROJECT_ID,
        region=LOCATION,
    ))
    response = await agent.run(prompt)
    return response.data
