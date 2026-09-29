import json, time, sys
from collections import defaultdict
from pathlib import Path
from agentguard.target_agent.agent import run_agent
from agentguard.redteam.attacks import build_attacks, succeeded, build_holdout_attacks

def run(agent_fn=run_agent, out="data/redteam_results.jsonl", delay=1.5, holdout=False):
    attacks = build_holdout_attacks() if holdout else build_attacks()
    results = []
    with Path(out).open("w", encoding="utf-8") as f:
        for a in attacks:
            try:
                output, status = agent_fn(a["input"]), "ok"
            except Exception as e:
                output, status = str(e)[:300], "error"
            hit = status == "ok" and succeeded(a["detect"], output)
            rec = {**a, "output": output, "status": status, "attack_success": hit}
            results.append(rec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(a["id"], "HIT" if hit else "blocked" if status == "ok" else "error")
            time.sleep(delay)
    report(results)
    return results

def report(results):
    print("\n=== Red-team report ===")
    total = len(results)
    hits = sum(r["attack_success"] for r in results)
    print(f"Attack success rate: {hits}/{total} ({100*hits//max(total,1)}%)")
    for key in ("category", "mutation"):
        groups = defaultdict(list)
        for r in results:
            groups[r[key]].append(r["attack_success"])
        for g, v in groups.items():
            print(f"  {key:9} {g:12} {sum(v)}/{len(v)}")

if __name__ == "__main__":
    import sys
    guarded = "--guarded" in sys.argv
    holdout = "--holdout" in sys.argv
    fn = run_agent
    out = "data/redteam_results.jsonl"
    if guarded:
        from agentguard.firewall.guarded_agent import run_guarded_agent
        fn = run_guarded_agent
        out = "data/redteam_guarded.jsonl"
    if holdout:
        out = out.replace(".jsonl", "_holdout.jsonl")
    run(fn, out, holdout=holdout)