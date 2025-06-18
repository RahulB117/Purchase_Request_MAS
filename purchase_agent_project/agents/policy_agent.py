import os
import json
import asyncio
import re
import textwrap
from dotenv import load_dotenv
from typing import Any
from crewai import Agent
from fastmcp import Client

load_dotenv()
assert os.getenv("OPENAI_API_KEY"), "Missing OPENAI_API_KEY"

class PolicyAgent(Agent):
    """
    Takes the following input JSON:
    {
        "request_id": "req-001"
        "requester": "Name of requester",
        "quantity": 2,
        "vendor": "Name of vendor",
        "unit_price": 109.95,
        "quantity:": 2,
        "total_price": 219.9,
        "currency": "USD",
        "reason": "Populated by PriceAgent"
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, "_server_url", "http://127.0.0.1:8001/mcp")

    async def call_tool(self, tool_name: str, params: dict):
        async with Client(self._server_url) as client:
            resp = await client.call_tool(tool_name, params)
            chunks = resp if isinstance(resp, list) else [resp]
            text   = "".join(c.text for c in chunks).strip()
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text

    async def run(self, input_json: dict):
        
        requester   = input_json["requester"]
        vendor      = input_json["vendor"]
        total_price = input_json["total_price"]

        plan_prompt = textwrap.dedent(f"""
            You are a policy agent. Given:
                requester: {requester}
                vendor:    {vendor}
                total_price: {total_price}
            Decide which tool(s) to call and with what parameters.
            Options:
                1. get_approval_price(requester)
                2. get_registered_vendors(requester)
                3. check_policy(requester, vendor, total_price)
            Respond *only* with JSON:
            {{ "steps": [
                    {{ "tool": "<tool_name>", "params": {{ ... }} }},
                    ...
            ] }}
            """)
        raw_plan = await asyncio.to_thread(self.llm.call, plan_prompt)
        # print("PLAN:", raw_plan)
        plan_str = raw_plan.strip()
        plan_str = re.sub(r"^```(?:json)?\s*", "", plan_str)
        plan_str = re.sub(r"\s*```$", "", plan_str)
        plan = json.loads(plan_str)

        policy = None
        for step in plan["steps"]:
            tool_name = step["tool"]
            params    = step["params"]
            result = await self.call_tool(tool_name, params)
            if tool_name == "check_policy":
                policy = result

        if policy is None:
            policy = await self.call_tool("check_policy", {
                "requester":   requester,
                "vendor":      vendor,
                "total_price": total_price
            })

        decision_prompt = textwrap.dedent(f"""
            Policy tool returned: {json.dumps(policy, indent=2)}
            Based on this, should we approve or reject?
            Answer *only* with JSON:
            {{ "approved": bool, "reason": string, "escalate": bool }}
            """)
        raw_dec = await asyncio.to_thread(self.llm.call, decision_prompt)
        # print("DECISION:", raw_dec)
        cleaned_dec = raw_dec.strip()
        cleaned_dec = re.sub(r"^```(?:json)?\s*", "", cleaned_dec)
        cleaned_dec = re.sub(r"\s*```$", "", cleaned_dec)
        verdict = json.loads(cleaned_dec)
            
        return {
            "requester": requester,
            "vendor": vendor,
            "total_price": total_price,
            "approved": verdict["approved"],
            "reason": verdict["reason"],
            "escalate": verdict["escalate"]
        }

# Smoke-test        
if __name__ == "__main__":
    agent = PolicyAgent(
        server_url="http://127.0.0.1:8001/mcp",
        role="approval_officer",
        goal="Approve or reject quotes per policy",
        backstory="Automates policy checks for spend thresholds and vendor preferences."
    )

    test_input = {
      "request_id": "req-001",
      "requester":  "Sarosh",
      "vendor":     "FakeStore",
      "unit_price": 109.95,
      "quantity":   2,
      "total_price":219.9,
      "currency":   "USD",
      "reason":     "Test Populated by PriceAgent"
    }

    result = asyncio.run(agent.run(test_input))
    print("Final PolicyAgent Output:", json.dumps(result, indent=2))