import google.generativeai as genai

def get_mental_health_response(prompt):
    """Interact with Google Generative AI to get a response for the given prompt."""
    # Initialize the API with your API key
    genai.configure(api_key="AIzaSyAt1GqToNZuopuJxnQoLq17T0tE93--M3k")

    # Generate the response using the model
    model = genai.GenerativeModel('gemini-1.5-flash')

    response = model.generate_content(prompt)

    #print(response.text)

    # Extract and return the generated text
    return response.text
