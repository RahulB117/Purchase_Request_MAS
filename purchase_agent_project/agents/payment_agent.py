import asyncio
import os
import json
import re
import textwrap
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
    Generates payment instructions in email, JSON or CSV,
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

        plan_prompt = textwrap.dedent(f"""
            You are a payment agent. The amount is {amount:.2f} {currency} to {vendor}, due on {due_date_str}.
            Decide if you should generate:
                1. JSON instruction,
                2. CSV instruction,
                3. A friendly email reminder?
            Respond *only* with JSON: {{ "format": "<JSON|CSV|EMAIL>", "notes": string }}
            """)
        plan_resp = await asyncio.to_thread(self.llm.call, plan_prompt)
        cleaned_plan = plan_resp.strip()
        cleaned_plan = re.sub(r"^```(?:json)?\s*", "", cleaned_plan)
        cleaned_plan = re.sub(r"\s*```$", "", cleaned_plan)
        plan = json.loads(cleaned_plan)
        # print("Payment Plan:", plan)

        format_inst = plan["format"].upper()
        if format_inst == "EMAIL":
            email_prompt = textwrap.dedent(f"""
                Compose a friendly email reminder for {vendor} payment of {amount:.2f} {currency} due on {due_date_str}.
                Include the reminder text: "{reminder_text}"
                Ensure the mail is sent to {requester} and of formal mail format.
                Respond *only* with JSON: {{ "To": string, "Subject": string, "Body": string }}
                """)
            raw_instr = await asyncio.to_thread(self.llm.call, email_prompt)
            instructions = raw_instr.strip()
            instructions = re.sub(r"^```(?:json)?\s*", "", instructions)
            instructions = re.sub(r"\s*```$", "", instructions)
            email = json.loads(instructions)
            # print("Email Reminder:", email)
        elif format_inst == "CSV":
            instructions = f"vendor,amount,currency,due_date\n{vendor},{amount:.2f},{currency},{due_date_str}"
        else:
            instructions = {
                "vendor": vendor,
                "amount": amount,
                "currency": currency,
                "due_date": due_date_str
            }
            instructions = json.dumps(instructions, indent=2)

        return {
            "requester": requester,
            "vendor": vendor,
            "total_price": amount,
            "approved": True,
            "format": format_inst,
            "payment_instruction": instructions,
            "notes": plan.get("notes", ""),
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