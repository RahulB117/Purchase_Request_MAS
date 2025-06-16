from fastmcp import FastMCP
import requests
from chromadb import PersistentClient
from chromadb.config import Settings
from typing import Any
from sentence_transformers import SentenceTransformer

# Setup ChromaDB
chroma_client = PersistentClient(
    path = "chroma_db",
    settings = Settings(persist_directory="chroma_db", anonymized_telemetry=False)
)
collection = chroma_client.get_or_create_collection("catalog_collection")

# Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize FastMCP server
#mcp = FastMCP(name="catalog", host="127.0.0.1", port=8000, path="/mcp")
mcp = FastMCP(name="catalog")

def _fetch_catalog(item_name: str) -> list[dict]:
    query_embedding = embedder.encode([item_name]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=5)
    return results["metadatas"][0] if results["metadatas"] else []

@mcp.tool()
def build_catalog(query: str) -> str:
    """
    Pulls products from fakestoreapi.com, embeds product titles,
    and stores vendor metadata in ChromaDB.
    """
    try:
        res = requests.get("https://fakestoreapi.com/products", timeout=5)
        products = res.json()
    except Exception as e:
        return f"API fetch error: {e}"

    matching = [p for p in products if query.lower() in p["title"].lower()]
    if not matching:
        return f"No matches found for '{query}'."

    titles = [p["title"] for p in matching]
    embeddings = embedder.encode(titles).tolist()

    print(f"[build_catalog] Matching products found: {len(matching)}")
    print(f"[build_catalog] Collection count BEFORE insert: {collection.count()}")

    for i, product in enumerate(matching):
        collection.add(
            documents=[product["title"]],
            embeddings=[embeddings[i]],
            metadatas=[{"vendor": "FakeStore", "unit_price": round(product["price"], 2)}],
            ids=[f"{product['id']}_{query}_{i}"]
        )
    print(f"[build_catalog] Collection count AFTER insert: {collection.count()}")

    return f"{len(matching)} products embedded into catalog for query '{query}'."

@mcp.tool()
def get_catalog_item(item_name: str) -> list:
    """
    Returns top-5 semantically matched products to the item name.
    """
    return _fetch_catalog(item_name)

@mcp.tool()
def get_price(item_name: str, quantity: int) -> dict[str, Any]:
    """
    Selects best price among top matches and computes total cost.
    """
    print(f"[get_price] Fetching price for {quantity} x {item_name}")
    entries = _fetch_catalog(item_name)

    if not entries:
        return {"error": f"No items found for '{item_name}'."}

    best = min(entries, key=lambda x: x["unit_price"])
    return {
        "vendor": best["vendor"],
        "unit_price": best["unit_price"],
        "total_price": round(best["unit_price"] * quantity, 2),
        "currency": "USD"
    }

if __name__ == "__main__":
    print("Starting Catalog MCP server...")
    #mcp.run(transport="streamable-http")
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")