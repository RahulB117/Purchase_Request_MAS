from crewai import Crew, process

from agents.request_agent import RequestAgent
from agents.price_agent import PriceAgent
from agents.policy_agent import PolicyAgent
from agents.payment_agent import PaymentAgent
from tasks import OrderToPay

class OrderToPayCrew():
    def __init__(self, user_input: str):
        self.user_input   = user_input
    
    def run(self):
        task_list = OrderToPay()
        requestAgent = RequestAgent
        priceAgent = PriceAgent
        policyAgent = PolicyAgent
        paymentAgent = PaymentAgent
        
        
        task_parse   = task_list.parse_request(requestAgent, self.user_input)
        task_quote   = task_list.acquire_price(priceAgent,      {})
        task_policy  = task_list.enforce_policy(policyAgent,     {})
        task_payment = task_list.process_payment(paymentAgent,   {})
        
        crew = Crew(
            agents=[requestAgent, priceAgent, policyAgent, paymentAgent],
            tasks = [task_parse, task_quote, task_policy, task_payment],
            mcp_server_urls={
                "catalog": "http://localhost:8000/mcp",
                "policy":  "http://localhost:8001/mcp",
            },
            verbose = True,
            process = process.sequential
        )
        result = crew.kickoff()
        return result

if __name__ == "__main__":
    user_input = input("Enter your purchase request: ")
    OrderToPayCrew_input = OrderToPayCrew(user_input)
    result = OrderToPayCrew_input.run()
    print("\n\n########################")
    print("## Here is your Crew's result:")
    print("########################\n")
    print(result)