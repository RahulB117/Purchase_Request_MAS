import os, asyncio
from textwrap import dedent
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent

assert os.getenv("OPENAI_API_KEY"), "Missing OPENAI_API_KEY"

class RequestAgent(Agent):
    async def run(self, user_input: str):
        prompt = dedent(f"""
You are a procurement parser. Convert the user's request into JSON with:
request_id, item, quantity, requester, date (YYYY-MM-DD).

User request: "{user_input}"
""")
        response = self.llm.call(prompt)
        return response

if __name__ == "__main__":
    test_agent = RequestAgent(
        role="procurement_parser",
        goal="Extract structured purchase request JSON",
        backstory="Transforms natural-language buy requests into JSON package.",
        llm_model=os.getenv("MODEL", "gpt-4o-mini")
    )
    test_input = "Need 5 studio mics for Alice by June 20"
    print("Input:", test_input)
    print("Output:", asyncio.run(test_agent.run(test_input)))