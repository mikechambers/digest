import requests
import json
from requests import Session

class Ollama:
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_LLM = "llama3.1"

    def __init__(self, llm=DEFAULT_LLM, base_url=DEFAULT_BASE_URL ):
        self.session = None
        self.llm = llm
        self.base_url = base_url
        self.init_session()

    def init_session(self):
        self.session = Session()

    def prompt(self, prompt):

        data = {
            "model": self.llm,
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

        url = f"{self.base_url}/api/chat"
        response = self.session.post(url, headers=headers, json=data)
        
        return response.json()
