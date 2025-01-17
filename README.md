# Mental Health Companion

Welcome to the Mental Health Companion! This project provides a supportive and empathetic chatbot designed to assist users with their mental health and well-being.

## Features

- Provides empathetic and supportive responses to user inputs.
- Maintains a conversation context to keep the dialogue coherent.
- Avoids answering technical, mathematical, or unrelated questions.
- Simple and relaxing web-based user interface.

## Project Structure
```
└── 📁Mental Health App
    └── 📁frontend
        └── background.jpg
        └── index.html
    └── .gitignore
    └── agent.py
    └── app.py
    └── mental_health_chat.py
    └── README.md
    └── requirements.txt
    └── vertex_ai.py
```

## Setup and Installation

### Prerequisites

- Python 3.7 or higher
- FastAPI
- Uvicorn
- Pydantic
- Google Generative AI
- PRAW (Python Reddit API Wrapper)
- httpx
- BeautifulSoup

### Installation

NOTE: These instructions are for Mac, and the bash file name could vary depending on your OS.

1. Clone the repository:

```sh
git clone https://github.com/yourusername/mental-health-companion.git
cd mental-health-companion
```

2. Create a virtual environment and activate it:

```sh
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
```

3. Install the required dependencies:
```sh
pip install -r requirements.txt
```

4. Set up environment variables for Google Cloud:

```sh
nano ~/.bash_profile
```

Add the export line:

```sh
export GOOGLE_APPLICATION_CREDENTIALS="<path to json service account key>"
```
Save the file and exit (Ctrl + O, then Enter, followed by Ctrl + X).

Reload the configuration:

```sh
source ~/.bash_profile
```

## Running the Application

### Start the FastAPI server
Run the following to start the application, after changing your directory to the root of the project (Mental Health App), if you are not already in it:
```sh
python app.py
```
Open your web browser and navigate to http://localhost:8000 to access the Mental Health Companion UI.

### Usage
Type your feelings or thoughts into the input box and click "Send".
The chatbot will respond with empathetic and supportive messages.
Type 'exit' to end the conversation and then close the webpage.