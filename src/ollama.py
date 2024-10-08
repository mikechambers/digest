import requests
import json
from requests import Session

class Ollama:
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_LLM = "llama3.1"
    API_TIMEOUT = 300
    NUM_CTX = 8192

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
            "format": "json",
            "temperature": 0,
            "options" : {
                "num_ctx": self.NUM_CTX
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/api/chat"
        response = self.session.post(url, headers=headers, json=data, timeout = self.API_TIMEOUT)

        return response.json()
