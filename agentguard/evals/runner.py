import json, time
from pathlib import Path
from agentguard.target_agent.agent import run_agent

def run_all(delay: float = 2.0):
    scenarios = json.loads(Path("data/scenarios.json").read_text(encoding="utf-8"))
    with Path("data/results.jsonl").open("w", encoding="utf-8") as f:
        for s in scenarios:
            start = time.time()
            try:
                output, status = run_agent(s["input"]), "ok"
            except Exception as e:
                output, status = str(e)[:300], "error"
            record = {**s, "output": output, "status": status,
                      "latency_s": round(time.time() - start, 2)}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(s["id"], status)
            time.sleep(delay)  # protects the free-tier rate limit

if __name__ == "__main__":
    run_all()