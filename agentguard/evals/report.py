import json, time, sys
from pathlib import Path
from agentguard.evals.judge import evaluate

def main(src="data/results.jsonl", dst="data/scores.json", delay=2.0):
    items = [json.loads(l) for l in Path(src).read_text(encoding="utf-8").splitlines() if l.strip()]
    scored = []
    for it in items:
        scored.append(evaluate(it))
        print(it["id"], "->", "PASS" if scored[-1]["task_success"] else "FAIL")
        time.sleep(delay)
    Path(dst).write_text(json.dumps(scored, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== AgentGuard report ===")
    for cat in ("normal", "edge", "adversarial"):
        rows = [s for s in scored if s["category"] == cat]
        if not rows:
            continue
        ok = sum(r["task_success"] for r in rows)
        unsafe = sum(not r["safe"] for r in rows)
        hall = sum(r["hallucination"] for r in rows)
        avg = sum(r["latency_s"] for r in rows) / len(rows)
        print(f"{cat:12} success {ok}/{len(rows)} ({100*ok//len(rows)}%)  unsafe {unsafe}  hallucinations {hall}  avg latency {avg:.2f}s")
    total = sum(s["task_success"] for s in scored)
    print(f"{'overall':12} success {total}/{len(scored)} ({100*total//len(scored)}%)")

if __name__ == "__main__":
    if "--guarded" in sys.argv:
        main("data/results_guarded.jsonl", "data/scores_guarded.json")
    else:
        main()