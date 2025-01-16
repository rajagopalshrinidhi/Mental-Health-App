import asyncio

class ConversationManager:
    def __init__(self):
        self.context = []

    def update_context(self, user_input, response):
        """
        Maintains a history of the conversation.
        """
        self.context.append({"user": user_input, "agent": response})
        if len(self.context) > 5:  # Keep the conversation context manageable
            self.context.pop(0)

    def build_prompt(self, user_input):
        """
        Builds a dynamic prompt using the context and the current input.
        """
        prompt = ""
        for exchange in self.context:
            prompt += f"User: {exchange['user']}\nAgent: {exchange['agent']}\n"
        prompt += f"User: {user_input}\nAgent:"
        return prompt

    async def process_input(self, user_input, get_response_fn):
        """
        Processes user input, sends it to the Vertex AI model, and returns the response.
        """
        prompt = self.build_prompt(user_input)
        response = await get_response_fn(prompt)
        self.update_context(user_input, response)
        return response