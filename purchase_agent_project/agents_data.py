import os
from dotenv import load_dotenv
from crewai import Agent
from crewai.project import agent
from agents.request_agent import RequestAgent as _RawRequestAgent
from agents.price_agent import PriceAgent as _RawPriceAgent
from agents.policy_agent import PolicyAgent as _RawPolicyAgent
from agents.payment_agent import PaymentAgent as _RawPaymentAgent

load_dotenv()

@agent(
    name="request_agent",
    role="procurement_parser",
    goal="Extract structured purchase request JSON",
    backstory="Transforms natural-language buy requests into structured JSON packages."
)
def request_agent():
    return _RawRequestAgent(
        llm_model=os.getenv("MODEL", "gpt-4o-mini")
    )

@agent(
    name="price_agent",
    role="pricing_analyst",
    goal="Find best vendor and compute price",
    backstory="Helps identify the most cost-effective supplier for a requested item."
)
def price_agent():
    return _RawPriceAgent(
        llm_model=os.getenv("MODEL", "gpt-4o-mini")
    )

@agent(
    name="policy_agent",
    role="approval_officer",
    goal="Approve or reject quotes per policy",
    backstory="Automates policy checks for spend thresholds and vendor preferences."
)
def policy_agent():
    return _RawPolicyAgent(
        llm_model=os.getenv("MODEL", "gpt-4o-mini")
    )

@agent(
    name="payment_agent",
    role="payment_processor",
    goal="Generate payment instructions for approved quotes",
    backstory="Formats payment instructions in JSON/CSV, flags manual review, and suggests reminders."
)
def payment_agent():
    return _RawPaymentAgent(
        llm_model=os.getenv("MODEL", "gpt-4o-mini")
    )