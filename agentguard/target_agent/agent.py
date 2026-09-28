import os, json
from dotenv import load_dotenv
from litellm import completion
from agentguard.tracing.tracer import trace

load_dotenv()
MODEL = os.getenv("MODEL")

@trace("tool:get_order_status")
def get_order_status(order_id: str) -> str:
    fake_db = {"101": "Shipped", "102": "Processing", "103": "Delivered"}
    return fake_db.get(order_id, "Order not found")

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_order_status",
        "description": "Get the status of an order by ID",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
}]

@trace("llm_call")
def call_llm(messages):
    return completion(model=MODEL, messages=messages, tools=TOOLS)

@trace("agent_run")
def run_agent(user_input: str) -> str:
    messages = [
        {"role": "system", "content": "You are a support agent. Use tools when needed."},
        {"role": "user", "content": user_input},
    ]
    resp = call_llm(messages).choices[0].message
    if resp.tool_calls:
        messages.append(resp)
        for tc in resp.tool_calls:
            args = json.loads(tc.function.arguments)
            result = get_order_status(**args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        resp = call_llm(messages).choices[0].message
    return resp.content

if __name__ == "__main__":
    print(run_agent("What is the status of order 101?"))