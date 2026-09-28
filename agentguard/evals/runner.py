import json, time, sys
from pathlib import Path
from agentguard.target_agent.agent import run_agent

def run_all(agent_fn=run_agent, out="data/results.jsonl", delay=2.0):
    scenarios = json.loads(Path("data/scenarios.json").read_text(encoding="utf-8"))
    with Path(out).open("w", encoding="utf-8") as f:
        for s in scenarios:
            start = time.time()
            try:
                output, status = agent_fn(s["input"]), "ok"
            except Exception as e:
                output, status = str(e)[:300], "error"
            record = {**s, "output": output, "status": status,
                      "latency_s": round(time.time() - start, 2)}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(s["id"], status)
            time.sleep(delay)

if __name__ == "__main__":
    if "--guarded" in sys.argv:
        from agentguard.firewall.guarded_agent import run_guarded_agent
        run_all(run_guarded_agent, "data/results_guarded.jsonl")
    else:
        run_all()