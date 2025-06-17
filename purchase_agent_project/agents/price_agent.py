import os
import json
import asyncio
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
            print("Available tools:", [t.name for t in tools])
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

    async def run(self, request_json: dict):
        item = request_json.get("item")
        quantity = request_json.get("quantity", 2)

        print(f"Building catalog for '{item}'...")
        build = await self.call_tool("build_catalog", {"query": item})
        print("Catalog build result:", build)

        print(f"Searching for top matches for '{item}'...")
        catalog = await self.call_tool("get_catalog_item", {"item_name": item})
        print("Top match:", catalog)

        print(f"Getting price for {quantity}x {item}...")
        price_info  = await self.call_tool("get_price", {
            "item_name": item,
            "quantity": quantity
        })
        result = {
            "requester": request_json.get("requester"),
            "quantity": quantity,
            "vendor":     price_info["vendor"],
            "unit_price": price_info["unit_price"],
            "total_price": price_info["total_price"],
            "currency":   price_info["currency"],
        }
        return result

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