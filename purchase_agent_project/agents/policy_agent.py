import os
import json
import asyncio
from dotenv import load_dotenv
from typing import Any

from crewai import Agent
from fastmcp import Client

load_dotenv()
assert os.getenv("OPENAI_API_KEY"), "Missing OPENAI_API_KEY"

class PolicyAgent(Agent):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, "_server_url", "http://127.0.0.1:8001/mcp")
    
    """
    Takes the following input JSON:
    {
        "requester": "Name of requester",   
        "quantity": 2,
        "vendor": "Name of vendor",
        "unit_price": 109.95,
        "total_price": 219.9,
        "currency": "USD"
    }
    Calls the MCP tool 'check_policy' from policy_mcp server to verify if the request is within policy limits.
    Returns an output JSON:
    {
        "requester": "Name of requester",
        "vendor": "Name of vendor",
        "total_price": 219.9,
        "approved": "true or false",
        "threshold": 1000.0,
        "preferred_vendors": ["Vendor_1","Vendor_2"],
        "reason": "Within policy limits"
    }
    """
    async def run(self, input_json: dict):
        requester = input_json.get("requester")
        vendor = input_json.get("vendor")
        total_price = input_json.get("total_price")
        
        async with Client(self._server_url) as client:
            response = await client.call_tool(
                "check_policy",
                {
                    "requester": requester,
                    "vendor": vendor,
                    "total_price": total_price
                }
            )
            policy = response.json()
            
        return {
            "requester": requester,
            "vendor": vendor,
            "total_price": total_price,
            "approved": policy.get("approved"),
            "threshold": policy.get("price_threshold"),
            "preferred_vendors": policy.get("registered_vendors"),
            "reason": policy.get("reason")
        }

# Smoke-test        
if __name__ == "__main__":
    agent = PolicyAgent(
        role="approval_officer",
        goal="Approve or reject quotes per policy",
        backstory="Automates policy checks for spend thresholds and vendor preferences."
    )

    test_input = {
      "requester":  "Sarosh",
      "quantity":   2,
      "vendor":     "FakeStore",
      "unit_price": 109.95,
      "total_price":219.9,
      "currency":   "USD"
    }

    result = asyncio.run(agent.run(test_input))
    print("ApprovalAgent Output:", result)