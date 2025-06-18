import os
import json
import asyncio
import re
from dotenv import load_dotenv
from typing import Any
from crewai import Agent
from fastmcp import Client

load_dotenv()
assert os.getenv("OPENAI_API_KEY"), "Missing OPENAI_API_KEY"


class PriceAgent(Agent):
    
    
    def __init__(self, server_url: str, **kwargs):
        super().__init__(**kwargs)
        self._server_url = server_url

    async def call_tool(self, tool_name: str, params: dict):
        """Call an MCP tool over stdio"""
        
        async with Client(self._server_url) as client:
            tools = await client.list_tools()
            #print("Available tools:", [t.name for t in tools])
            resp = await client.call_tool(tool_name, params)
            
            contents = resp
            if hasattr(resp, "text"):
                contents = [resp]
            elif isinstance(resp, list):
                contents = resp
            
            text = "".join(c.text for c in contents).strip()
            # attempt JSON parse, else return raw string
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text

    async def run(self, request_json: dict) -> dict:
        """
        Takes Input JSON from RequestAgent:
        {
            "request_id": "1",
            "item": "studio mics",
            "quantity": 5,
            "requester": "name of requester",
            "date": "2023-06-20"
        }

        Agent uses MCP tools to:
        1. Build catalog for the requested item
        2. Search for top matches in the catalog
        3. Get price for the requested quantity
        4. Return structured output JSON with vendor and pricing details

        {
            "request_id":  request_id,
            "vendor":      choice["vendor"],
            "unit_price":  choice["unit_price"],
            "total_price": round(choice["unit_price"] * quantity, 2),
            "currency":    "USD"
        }
        """
        request_id = request_json.get("request_id")
        item       = request_json.get("item")
        quantity   = request_json.get("quantity", 1)

        plan_prompt = f"""
            You are a pricing agent. The user wants {quantity}×'{item}'.
            Should you call:
                1) build_catalog(query)
                2) get_catalog_item(item_name)
            Respond with JSON: {{ "tool": "<tool_name>", "params": {{ ... }} }}
            """
        plan_resp = await asyncio.to_thread(self.llm.call, plan_prompt)
        #print("PLAN:", plan_resp)
        clean = plan_resp.strip()
        clean = re.sub(r"^```(?:json)?\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)
        plan = json.loads(clean)

        if plan["tool"] == "build_catalog":
            await self.call_tool("build_catalog", plan["params"])
            catalog = await self.call_tool("get_catalog_item", {"item_name": item})
        else:
            # direct get_catalog_item or other tool
            catalog = await self.call_tool(plan["tool"], plan["params"])

        decision_prompt = f"""
            Here are the catalog entries: {json.dumps(catalog, indent=2)}
            Which vendor should we pick for {quantity}×'{item}', and why?
            Answer with JSON: {{ "vendor": string, "unit_price": number, "reason": string }}
            """
        decision_resp = await asyncio.to_thread(self.llm.call, decision_prompt)
        #print("DECISION:", decision_resp)
        clean = decision_resp.strip()
        clean = re.sub(r"^```(?:json)?\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)
        choice = json.loads(clean)

        llm_price = choice["unit_price"]
        llm_total = round(choice["unit_price"] * quantity, 2)
        # Verify against the catalog’s own pricing logic
        verify = await self.call_tool(
            "get_price",
            {"item_name": item, "quantity": quantity}
        )

        # If there’s a mismatch, override and log it
        if (verify["unit_price"], verify["total_price"]) != (llm_price, llm_total):
            print(
            f"LLM price {llm_price} vs. tool price {verify['unit_price']}, "
            "overriding with tool value"
            )
            choice["unit_price"]  = verify["unit_price"]
            choice["total_price"] = verify["total_price"]
        else:
            choice["total_price"] = llm_total

        quote = {
            "request_id":  request_id,
            "requester":   request_json.get("requester"),
            "vendor":      choice["vendor"],
            "unit_price":  choice["unit_price"],
            "quantity":    quantity,
            "total_price": round(choice["unit_price"] * quantity, 2),
            "currency":    "USD",
            "reason": choice["reason"]
        }
        return quote

# Test it from CLI
if __name__ == "__main__":
    agent = PriceAgent(
        server_url="http://127.0.0.1:8000/mcp",
        role="pricing_analyst",
        goal="Find best vendor and compute price",
        backstory="Helps identify the most cost-effective supplier for a requested item."
    )

    test_input = {
        "request_id": "req-001",
        "item": "laptop",
        "quantity": 2,
        "requester": "Alice",
        "date": "2025-06-20"
    }

    result = asyncio.run(agent.run(test_input))
    print("Final PriceAgent Output:", json.dumps(result, indent=2))