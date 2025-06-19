from crewai import Task
from textwrap import dedent
from tools_mcp import catalog_tools, policy_tools

class OrderToPay():
    def _tip_section(self):
        return "Excellent work is rewarded with a large bonus payment."
    def parse_request(self, agent, user_input):
        return Task(
            name = "parse_request",
            description=dedent(
                f"""
                **Task**: Parse user's human-readable purchase request into structured JSON.
                **Description**: Take the user's request and convert it into a JSON object with the following fields:
                    - "request_id": Unique identifier for the request
                    - "item": Name of the item being requested
                    - "quantity": Number of items requested
                    - "requester": Name of the person making the request
                    - "date": Date of the request in YYYY-MM-DD format
                **Parameters**:
                    - user_input: {user_input}
                **Note**: {self._tip_section()}
                """
            ),
            agent=agent,
            tools = [],
            expected_output="JSON with request_id, item, quantity, requester, date"
        )
    
    def acquire_price(self, agent, request_json):
        return Task(
            name = "acquire_price",
            description=dedent(
                f"""
                **Task**: Acquire the best price for the requested item.
                **Description**: Given a request in JSON format, use relevant MCP server tools under tools to:
                    1. Build a catalog for the requested item
                    2. Search for top matches in the catalog
                    3. Get price for the requested quantity
                    4. Return structured output JSON with vendor and pricing details:
                        - request_id: Unique identifier for the request
                        - requester: Name of the requester
                        - vendor: Name of the vendor chosen
                        - unit_price: Price per unit of the item
                        - quantity: Number of items requested
                        - total_price: Total price for the requested quantity
                        - currency: Currency of the price (default is "USD")
                        - reason: Reason for the choice of vendor
                        - status: False when item is missing in catalog
                **Parameters**:
                    - request_json: {request_json}
                **Note**: {self._tip_section()}
                """
            ),
            agent=agent,
            tools=catalog_tools,
            expected_output=dedent(
                """
                {
                    "request_id": "<request_id>",
                    "requester": "<requester_name>",
                    "vendor": "<vendor_name>",
                    "unit_price": <unit_price>,
                    "quantity": <quantity>,
                    "total_price": <total_price>,
                    "currency": "USD",
                    "reason": "<reason_for_choice>",
                    "status": <True|False>
                }
                """
            )
        )
        
    def enforce_policy(self, agent, request_json):
        return Task(
            name= "enforce_policy",
            description=dedent(
                f"""
                **Task**: Check if the purchase request is within policy limits.
                **Description**: Given a purchase request in JSON format, use relevant MCP Server tools under tools to:
                 - Verify if the request is within policy limits
                 - Return structured output JSON with approval status and policy details:
                    - requester: Name of the requester
                    - vendor: Name of the vendor
                    - total_price: Total price of the request
                    - approved: True if within policy, False otherwise
                    - reason: Reason for approval/denial
                    - escalate: True if manual review is required
                    - status: False when item is missing in catalog
                    
                **Parameters**:
                    - request_json: {request_json}
                **Note**: {self._tip_section()}
                """
            ),
            agent=agent,
            tools=policy_tools,
            expected_output=dedent("""
                {
                    "requester": "<requester_name>",
                    "vendor": "<vendor_name>",
                    "total_price": <total_price>,
                    "approved": true,
                    "reason": "<reason_for_approval_or_denial>",
                    "escalate": <True|False>,
                    "status": <True|False>
                }
                """
            )
        )
        
    def process_payment(self, agent, request_json):
        return Task(
            name = "process_payment",
            description=dedent(f"""
                **Task**: Generate payment instructions based on the approved purchase request.
                **Description**: Given a purchase request in JSON format:
                    - Generate payment instructions in email, JSON or CSV formats
                    - Flag for manual review if not approved
                    - Add a reminder for payment
                    - returns structured output JSON with payment details:
                        - requester: Name of the requester
                        - vendor: Name of the vendor
                        - total_price: Total price of the request
                        - approved: True if payment instructions generated, False otherwise
                        - format: Either email, JSON or CSV
                        - payment_instruction: Detailed payment instruction to be mailed, formatted or otherwise
                        - notes: payment reminder date.
                        - status: False when item is missing in catalog
                **Parameters**:
                    - request_json: {request_json}
                **Note**: {self._tip_section()}
                """
            ),
            agent=agent,
            tools=[],
            expected_output=dedent("""
            {
                "requester": "<requester_name>",
                "vendor": "<vendor_name>",
                "total_price": "<total_price>",
                "approved": True,
                "format": "<format>",
                "payment_instruction": "<payment_instruction>",
                "notes": "<notes>",
                "status": <True|False>
            }
            """
            )
        )