# Purchase Request Multi-Agent System

A modular AI-driven purchasing assistant using CrewAI, MCP, RAG, and ChromaDB.

## ⭐ Overview
This project implements a multi-agent system to automate and intelligently manage purchase requests. Core features include:

- **CrewAI orchestration** with structured task flow.
- **Model Context Protocol (MCP)** for standardized inter-agent messaging.
- **Multi-agent design** with specialized agents for catalog lookup, pricing, policy validation, and procurement.
- **Retrieval-Augmented Generation (RAG)** powered by ChromaDB for reference-based responses.

## 🚀 Architecture & Code Structure
- `main.py`: Coordinator that loads MCP agents, binds tasks, and runs CrewAI flow.
- `agents_data.py`: Central registry with agent definitions and metadata.
- `tools_mcp.py`: Defines custom tools (functions/interfaces) exposed by agents via MCP.
- `tasks.py`: CrewAI task definitions orchestrating agent interactions.
- `agents/`: Contains implementations of 4 domain-specific agents (e.g., price, policy, catalog, procurement logic).
- `MCP_Servers/`:
  - `catalog_mcp/`: Hosts the price-agent MCP server and tools.
  - `policy_mcp/`: Hosts the policy-agent MCP server and tools.

## 🔧 Technologies Used
- **CrewAI**: Multi-agent orchestration framework.
- **MCP**: Model Context Protocol for agent communication.
- **RAG**: Retrieval-Augmented Generation integrated via ChromaDB vector store.
- **ChromaDB**: Embedding-based storage for knowledge retrieval.
- **OpenAI APIs**: LLM LLM calls managed through CrewAI tools.

## ✅ Use Cases
1. **Catalog Agent** – Retrieves product information using ChromaDB-backed vectors.
2. **Price Agent** – Queries external endpoints via MCP tools for live pricing.
3. **Policy Agent** – Validates and enforces procurement rules via MCP tools.
4. **Coordinator Agent** – Aggregates results and makes purchase decisions.