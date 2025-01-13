from agent import MentalHealthAgent
from vertex_ai import get_mental_health_response

def mental_health_chat():
    """Simple text-based interaction for the Mental Health Companion."""
    print("Welcome to your Mental Health Companion!")
    print("Type 'exit' to end the conversation.\n")

    agent = MentalHealthAgent()  # Initialize the agent

    while True:
        user_input = input("How are you feeling? ")
        if user_input.lower() == 'exit':
            print("Take care! Remember, you're not alone. Goodbye!")
            break

        response = agent.process_input(user_input, get_mental_health_response)
        print(f"Companion: {response}\n")