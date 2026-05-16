import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class GithubCardAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash') # Using 1.5 Flash as requested

    async def run(self, prompt: str):
        # Placeholder for agent execution logic using MCP tools
        response = self.model.generate_content(prompt)
        return response.text

def get_agent():
    return GithubCardAgent()
