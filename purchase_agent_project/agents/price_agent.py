import asyncio
import os
from dotenv import load_dotenv
from crewai import Agent
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import json

load_dotenv()
assert os.getenv("OPENAI_API_KEY"), "Missing OPENAI_API_KEY"


class PriceAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def call_tool(self, tool_name: str, params: dict):
        """Call an MCP tool over stdio"""
        server_params = StdioServerParameters(
            command="python",
            args=["purchase_agent_project/MCP_Servers/catalog_mcp/server.py"]
        )
        async with stdio_client(server_params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                response = await session.list_tools()
                tools = response.tools
                print("\nConnected to server with tools:", [tool.name for tool in tools])
                
                result = await session.call_tool(tool_name, arguments=params)
                if isinstance(result.content, list) and hasattr(result.content[0], "text"):
                    raw_text = result.content[0].text
                    try:
                        # Try parsing as JSON if it looks like a dict or list
                        return json.loads(raw_text)
                    except json.JSONDecodeError:
                        return raw_text
                else:
                    return result.content

    async def run(self, request_json: dict):
        item = request_json.get("item")
        quantity = request_json.get("quantity", 1)

        print(f"Building catalog for '{item}'...")
        build = await self.call_tool("build_catalog", {"query": item})
        print("Catalog build result:", build)

        print(f"Searching for top matches for '{item}'...")
        catalog = await self.call_tool("get_catalog_item", {"item_name": item})
        print("Top match:", catalog)

        print(f"Getting price for {quantity}x {item}...")
        price = await self.call_tool("get_price", {"item_name": item, "quantity": quantity})
        return price

# Test it from CLI
if __name__ == "__main__":
    agent = PriceAgent(
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
    print("Final PriceAgent Output:", result)