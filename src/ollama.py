import requests
import json
from requests import Session

OLLAMA_URL = "http://localhost:11434/api/chat"

session = None
llm = "llama3.1"
url = OLLAMA_URL

def init_session():
    global session

    session = Session()


def prompt(prompt, url = OLLAMA_URL):

    data = {
        "model": "llama3.1",
        "messages": [
            {
                "role": "user",
                "content": prompt

            }
        ],
        "stream": False,
        "format": "json"
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = None
    if session:
        response = session.post(url, headers = headers, json=data)
    else:
        response = requests.post(url, headers = headers, json=data)

    return response.json()
