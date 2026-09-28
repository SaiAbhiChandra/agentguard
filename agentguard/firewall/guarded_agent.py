import json
from agentguard.tracing.tracer import trace
from agentguard.target_agent.agent import call_llm, get_order_status, SYSTEM_PROMPT, FALLBACK
from agentguard.firewall.policy import (scan_input, validate_tool_call,
                                        filter_output, log_event, REFUSAL)

@trace("guarded_agent_run")
def run_guarded_agent(user_input: str) -> str:
    ok, reason = scan_input(user_input)
    if not ok:
        log_event("input_blocked", reason, user_input)
        return REFUSAL

    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}]
    tool_ids, calls = [], 0

    for _ in range(4):
        resp = call_llm(messages).choices[0].message
        if not resp.tool_calls:
            answer = resp.content or FALLBACK
            ok, reason = filter_output(answer, user_input, tool_ids)
            if not ok:
                log_event("output_blocked", reason, answer)
                return REFUSAL
            return answer

        messages.append(resp)
        for tc in resp.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except Exception:
                args = {}
            ok, reason = validate_tool_call(tc.function.name, args, calls)
            calls += 1
            if not ok:
                log_event("tool_blocked", reason, f"{tc.function.name} {args}")
                result = f"Blocked by security policy ({reason}). Ask the user for a valid numeric order ID."
            else:
                tool_ids.append(str(args["order_id"]))
                result = get_order_status(**args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    return FALLBACK