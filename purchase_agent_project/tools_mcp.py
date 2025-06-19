from crewai_tools import MCPServerAdapter

CATALOG_PARAMS = {
    "url": "http://localhost:8000/mcp",
    "transport": "streamable-http"
}

POLICY_PARAMS = {
    "url": "http://localhost:8001/mcp",
    "transport": "streamable-http"
}

_CATALOG_TOOLS = MCPServerAdapter(CATALOG_PARAMS).__enter__()
_POLICY_TOOLS  = MCPServerAdapter(POLICY_PARAMS).__enter__()

catalog_tools = _CATALOG_TOOLS
policy_tools  = _POLICY_TOOLS