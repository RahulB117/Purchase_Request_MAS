import os
from dotenv import load_dotenv
from crewai import Agent
from crewai.project import agent
from agents.request_agent import RequestAgent as _RawRequestAgent
from agents.price_agent import PriceAgent as _RawPriceAgent
from agents.policy_agent import PolicyAgent as _RawPolicyAgent
from agents.payment_agent import PaymentAgent as _RawPaymentAgent

load_dotenv()

@agent
def request_agent() -> Agent:
    return _RawRequestAgent(
        name="request_agent",
        role="procurement_parser",
        goal="Extract structured purchase request JSON",
        backstory="Transforms natural-language buy requests into structured JSON packages.",
        llm_model=os.getenv("MODEL", "gpt-4o-mini")
    )

@agent
def price_agent() -> Agent:
    return _RawPriceAgent(
        server_url="http://localhost:8000/mcp",
        name="price_agent",
        role="pricing_analyst",
        goal="Find best vendor and compute price",
        backstory="Helps identify the most cost-effective supplier for a requested item.",
        llm_model=os.getenv("MODEL", "gpt-4o-mini")
    )

@agent
def policy_agent() -> Agent:
    return _RawPolicyAgent(
        server_url="http://localhost:8001/mcp",
        name="policy_agent",
        role="approval_officer",
        goal="Approve or reject quotes per policy",
        backstory="Automates policy checks for spend thresholds and vendor preferences.",
        llm_model=os.getenv("MODEL", "gpt-4o-mini")
    )

@agent
def payment_agent() -> Agent:
    return _RawPaymentAgent(
        name="payment_agent",
        role="payment_processor",
        goal="Generate payment instructions for approved quotes",
        backstory="Formats payment instructions in JSON/CSV, flags manual review, and suggests reminders.",
        llm_model=os.getenv("MODEL", "gpt-4o-mini")
    )