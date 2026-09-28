import re, json, time
from pathlib import Path
from agentguard.evals.judge import LEAK_MARKERS

LOG = Path("data/firewall_log.jsonl")
REFUSAL = "Sorry, I can only help with order status questions."
ALLOWED_TOOLS = {"get_order_status"}
MAX_TOOL_CALLS = 3

INJECTION_PATTERNS = [
    r"ignore (all |any )?(the )?(previous|prior|above|earlier) (instructions|rules|prompts?)",
    r"forget (that )?(you are|your (rules|instructions))",
    r"you are (now )?dan\b|developer mode|no restrictions|jailbreak",
    r"you are now\b",
    r"system (message|override|prompt)|priority override",
    r"(new|updated) (rule|instruction)s?\b",
    r"(end|finish|start|begin) (every|each|all|your) (reply|response|answer|message)s? with",
    r"(before|after) (answering|replying|responding),? (print|say|output|write|repeat)",
    r"(reply|respond|answer) only with",
    r"(print|show|reveal|repeat|output|quote).{0,30}(system prompt|instructions|rules)",
    r"repeat everything (above|before)",
    r"(all|every|other) (customers?|users?)",
    r"(dump|list) (the )?(entire|whole|every|all)",
    r"ignora.{0,30}(reglas|instrucciones)",
]
_COMPILED = [re.compile(p, re.I | re.S) for p in INJECTION_PATTERNS]

def log_event(kind: str, reason: str, detail: str):
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "kind": kind, "reason": reason,
                            "detail": detail[:300]}, ensure_ascii=False) + "\n")

def scan_input(text: str):
    if len(text) > 1000:
        return False, "input_too_long"
    for p in _COMPILED:
        if p.search(text):
            return False, f"pattern:{p.pattern[:40]}"
    return True, ""

def validate_tool_call(name: str, args: dict, calls_so_far: int):
    if name not in ALLOWED_TOOLS:
        return False, f"tool_not_allowed:{name}"
    if calls_so_far >= MAX_TOOL_CALLS:
        return False, "too_many_tool_calls"
    order_id = str(args.get("order_id", ""))
    if not re.fullmatch(r"\d{1,6}", order_id):
        return False, f"invalid_order_id:{order_id[:30]}"
    return True, ""

def filter_output(text: str, user_input: str, tool_ids: list):
    low = text.lower()
    if any(m in low for m in LEAK_MARKERS):
        return False, "system_prompt_leak"
    if len(text) > 600:
        return False, "output_too_long"
    for oid in re.findall(r"\b\d{3,6}\b", text):
        if oid not in user_input and oid not in tool_ids:
            return False, f"unexpected_id:{oid}"
    return True, ""