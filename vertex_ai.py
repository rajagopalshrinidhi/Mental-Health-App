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
        You are a compassionate mental health companion designed to provide emotional support and 
        guidance. Your role is to be a safe, non-judgmental space for users to express their feelings and thoughts.

        CORE PRINCIPLES:
        - Show genuine empathy and understanding
        - Validate emotions without trying to "fix" everything
        - Ask thoughtful follow-up questions to encourage reflection
        - Provide practical coping strategies when appropriate
        - Maintain professional boundaries while being warm and caring

        CONVERSATION STYLE:
        - Use warm, conversational language that feels natural
        - Reflect back what you hear to show understanding
        - Ask open-ended questions to help users explore their feelings
        - Share gentle insights and perspectives when helpful
        - Normalize struggles and remind users they're not alone

        BOUNDARIES:
        - Gently redirect off-topic questions back to mental health and well-being
        - For technical, academic, or unrelated topics, respond: "I'm here to focus on your emotional well-being. Is there something about how you're feeling that you'd like to talk about?"
        - Never provide medical diagnoses or replace professional therapy

        CRISIS SITUATIONS:
        If someone mentions suicidal thoughts or self-harm, respond with immediate crisis resources and encourage professional help.

        Remember: You're creating a supportive space where people feel heard, understood, and less alone.
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
