import asyncio
import os
import json
from datetime import date, timedelta
from dotenv import load_dotenv
from crewai import Agent

load_dotenv()
assert os.getenv("OPENAI_API_KEY"), "Missing OPENAI_API_KEY"

class PaymentAgent(Agent):
    """
    Takes the following JSON input:
    {
      "requester": "name of requester",
      "quantity": 2,
      "vendor": "name of vendor",
      "unit_price": 109.95,
      "total_price": 219.9,
      "currency": "USD",
      "approved": True/False,
      "reason": "reasons for approval/denial"
    }
    Generates payment instructions in JSON and CSV,
    Flags for manual review when approved is False,
    Adds reminder for payment
    """
    async def run(self, input_json: dict):
        requester    = input_json.get("requester")
        vendor       = input_json.get("vendor")
        amount       = input_json.get("total_price")
        currency     = input_json.get("currency", "USD")
        approved     = input_json.get("approved", False)
        reason       = input_json.get("reason", "")

        # If not approved, require manual review
        if not approved:
            return {
                "requester": requester,
                "vendor": vendor,
                "total_price": amount,
                "approved": approved,
                "requires_manual_review": True,
                "reason": reason
            }

        # Compute due date
        net_terms = 7 # Set for 1 week by default
        due = date.today() + timedelta(days=net_terms)
        due_date_str = due.isoformat()

        # Reminder: one day before due date
        reminder_date = due - timedelta(days=1)
        reminder_text = f"Remind to pay {vendor} {amount:.2f} {currency} on {reminder_date.isoformat()}"

        # JSON payment instruction
        payment_json = {
            "vendor":   vendor,
            "amount":   amount,
            "currency": currency,
            "due_date": due_date_str
        }

        # CSV payment instruction
        csv_header = "vendor,amount,currency,due_date"
        csv_row = f"{vendor},{amount:.2f},{currency},{due_date_str}"
        payment_csv = f"{csv_header}\n{csv_row}"

        # Build output payload
        return {
            "requester": requester,
            "vendor": vendor,
            "total_price": amount,
            "approved": True,
            "payment_instruction_json": payment_json,
            "payment_instruction_csv": payment_csv,
            "reminder": reminder_text
        }

# CLI Test
if __name__ == "__main__":
    agent = PaymentAgent(
        role="payment_processor",
        goal="Generate payment instructions for approved quotes",
        backstory="Formats payment instruction in JSON/CSV, flags manual review, and suggests reminders."
    )
    test_input = {
        "requester": "Ujwal",
        "quantity": 2,
        "vendor": "FakeStore",
        "unit_price": 109.95,
        "total_price": 219.9,
        "currency": "USD",
        "approved": True,
        "reason": "Within policy limits"
    }
    result = asyncio.run(agent.run(test_input))
    print("PaymentAgent Output:", json.dumps(result, indent=2))