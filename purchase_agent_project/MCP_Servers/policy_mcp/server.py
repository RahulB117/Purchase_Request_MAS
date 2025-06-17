from fastmcp import FastMCP

mcp  = FastMCP(name = "policy")

# Only registered users can make purchases
_POLICY_DB = {
    "price_thresholds": {
        "Sarosh": 1000,
        "Ujwal": 500,
        "Aditya": 1000,
        "Joel": 1000,
        "__default__": 0 # Default threshold for others
    },
    "registered_vendors": {
        "Sarosh": ["FakeStore", "eBay"],
        "Ujwal": ["FakeStore", "eBay"],
        "Aditya": ["FakeStore", "eBay"],
        "Joel": ["FakeStore", "eBay"],
        "__default__": []# Default vendor for others
    },
}


# @mcp.resource("config://policy_database")
# def policy_database():
#     return _POLICY_DB

@mcp.tool()
def get_approved_price(requester: str, data=_POLICY_DB) -> float:
    """
    returns allowed price threshold for requester.
    returns 0 if requester is not registered.
    """
    return data["price_thresholds"].get(
        requester, 
        data["price_thresholds"]["__default__"]
        )
    
@mcp.tool()
def get_registered_vendors(requester: str, data=_POLICY_DB) -> list:
    """
    returns list of registered vendors for requester.
    returns empty list if requester is not registered.
    """
    return data["registered_vendors"].get(
        requester, 
        data["registered_vendors"]["__default__"]
        )
    
@mcp.tool()
def check_policy(
    requester: str,
    vendor: str,
    total_price: float
    ) -> dict:
    """
    Checks if total_price is within the allowed threshold.
    Checks if vendor is registered for requester.
    Returns Approval Status with reason if not approved.
    """
    reasons = []
    data = _POLICY_DB
    price_threshold = data["price_thresholds"].get(
        requester,
        data["price_thresholds"]["__default__"]
    )
    approved_vendors = data["registered_vendors"].get(
        requester,
        data["registered_vendors"]["__default__"]
    )
    
    if requester not in data["price_thresholds"]:
        reasons.append(f"{requester} is not registered. Request not approved.")
    
    if total_price > price_threshold:
        reasons.append(f"Total price {total_price} exceeds threshold of {price_threshold}. Request not approved.")
    
    known_vendors = {vendor for list in data["registered_vendors"].values() for vendor in list}
    if vendor not in approved_vendors:
        if vendor not in known_vendors:
            reasons.append(f"{vendor} is not a registered vendor. Request not approved.")
        else:
            reasons.append(f"{vendor} is not registered for {requester}. Request not approved.")
    
    approved = not reasons
    reason = "Policy check passed." if approved else "Policy check failed:".join(reasons)
    
    return {
        "approved": approved,
        "price_threshold": price_threshold,
        "registered_vendors": approved_vendors,
        "reason": reason
    }
    
if __name__ == "__main__":
    print("Starting Policy MCP server...")
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
        path="/mcp"
    )