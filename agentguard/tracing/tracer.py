import json, time, uuid, functools
from pathlib import Path

TRACE_FILE = Path("data/traces.jsonl")

def trace(step_name):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.time()
            status, result = "ok", None
            try:
                result = fn(*args, **kwargs)
                return result
            except Exception as e:
                status, result = "error", str(e)
                raise
            finally:
                TRACE_FILE.parent.mkdir(exist_ok=True)
                with TRACE_FILE.open("a") as f:
                    f.write(json.dumps({
                        "id": str(uuid.uuid4()),
                        "step": step_name,
                        "input": str((args, kwargs))[:500],
                        "output": str(result)[:500],
                        "status": status,
                        "latency_s": round(time.time() - start, 3),
                        "ts": time.time(),
                    }) + "\n")
        return wrapper
    return deco