#!/usr/bin/env python3
"""Run every task under both conditions and log accuracy, tokens, and time.

Examples
  python run_bench.py --dry-run                # offline test, no API calls
  python run_bench.py --limit 6                # smoke test on 6 real tasks
  python run_bench.py --repeats 3 --workers 4  # full run, 3 repetitions
Safe to interrupt and re-run: completed (task, condition, rep) triples are skipped.
"""
import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import config
from mockdb import MockDB, TOOL_SCHEMAS, execute_tool
from scoring import score_run
from tasks import build_tasks

SYSTEM_PROMPT = (
    "You are an operations assistant for an online store. You have tools that query the store's "
    "database. Use the tools to find information; never guess IDs or values, and do arithmetic carefully. "
    "If an entity does not exist, answer NOT_FOUND. When you are finished, end your reply with a single "
    "final line in exactly this form:\nANSWER: <answer>\n"
    "Answer formats: numbers as plain digits with up to 2 decimals (no currency symbols or units); "
    "yes/no questions as 'yes' or 'no'; lists of IDs comma-separated; text values exactly as stored."
)


def run_one(client, db, task, cname, cond, rep):
    messages = [{"role": "user", "content": task["prompt"]}]
    u = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}
    tool_log, thinking_chars, api_s, turns = [], 0, 0.0, 0
    final_text, stop_reason, error = "", None, None
    t0 = time.perf_counter()
    try:
        for _ in range(config.MAX_TURNS):
            kw = dict(model=cond["model"], max_tokens=config.MAX_TOKENS, system=SYSTEM_PROMPT,
                      tools=TOOL_SCHEMAS, messages=messages)
            if cond["thinking"]:
                kw["thinking"] = cond["thinking"]
            elif config.BASELINE_TEMPERATURE is not None:
                kw["temperature"] = config.BASELINE_TEMPERATURE
            c0 = time.perf_counter()
            resp = client.messages.create(**kw)
            api_s += time.perf_counter() - c0
            turns += 1
            us = resp.usage
            u["input"] += us.input_tokens or 0
            u["output"] += us.output_tokens or 0
            u["cache_creation"] += getattr(us, "cache_creation_input_tokens", 0) or 0
            u["cache_read"] += getattr(us, "cache_read_input_tokens", 0) or 0
            stop_reason = resp.stop_reason
            for b in resp.content:
                if b.type == "thinking":
                    thinking_chars += len(getattr(b, "thinking", "") or "")
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason == "tool_use":
                results = []
                for b in resp.content:
                    if b.type == "tool_use":
                        res, is_err = execute_tool(db, b.name, b.input)
                        tool_log.append({"name": b.name, "args": b.input, "error": is_err})
                        results.append({"type": "tool_result", "tool_use_id": b.id,
                                        "content": json.dumps(res), "is_error": is_err})
                messages.append({"role": "user", "content": results})
            else:
                final_text = "".join(b.text for b in resp.content if b.type == "text")
                break
    except Exception as e:  # recorded, excluded from analysis, retried on next run
        error = f"{type(e).__name__}: {e}"[:500]
    wall = time.perf_counter() - t0

    names = [t["name"] for t in tool_log]
    row = {
        "task_id": task["id"], "tier": task["tier"], "template": task["template"],
        "n_ref_calls": task["n_ref_calls"], "condition": cname, "model": cond["model"], "rep": rep,
        "expected": task["expected"], "turns": turns, "n_tool_calls": len(tool_log),
        "n_tool_errors": sum(t["error"] for t in tool_log), "tool_names": names, "tool_log": tool_log,
        "input_tokens": u["input"], "output_tokens": u["output"],
        "cache_creation_tokens": u["cache_creation"], "cache_read_tokens": u["cache_read"],
        "total_tokens": sum(u.values()), "thinking_chars": thinking_chars,
        "wall_s": round(wall, 3), "api_s": round(api_s, 3), "stop_reason": stop_reason,
        "error": error, "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    row.update(score_run(task, final_text, names))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--workers", type=int, default=1, help="parallel runs (1 gives the cleanest timing)")
    ap.add_argument("--limit", type=int, help="only the first N tasks per tier-interleaved order")
    ap.add_argument("--tiers", type=int, nargs="*", default=[1, 2, 3])
    ap.add_argument("--conditions", nargs="*", default=["baseline", "reasoning"])
    ap.add_argument("--out", default=None, help="output dir (default results/ or results_dry/)")
    ap.add_argument("--dry-run", action="store_true", help="simulate the agent offline")
    a = ap.parse_args()

    out_dir = a.out or ("results_dry" if a.dry_run else "results")
    os.makedirs(out_dir, exist_ok=True)
    raw = os.path.join(out_dir, "raw.jsonl")

    db = MockDB()
    tasks = [t for t in build_tasks(db) if t["tier"] in a.tiers]
    if a.limit:  # round-robin across tiers so a smoke test touches every tier
        by = {k: [t for t in tasks if t["tier"] == k] for k in a.tiers}
        tasks = [by[k][i] for i in range(a.limit) for k in a.tiers if i < len(by[k])][: a.limit]

    if a.dry_run:
        from fake_client import FakeClient
        client = FakeClient(tasks)
    else:
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise SystemExit("Set ANTHROPIC_API_KEY first (or use --dry-run).")
        import anthropic
        client = anthropic.Anthropic(max_retries=6, timeout=300)

    done = set()
    if os.path.exists(raw):
        for line in open(raw):
            r = json.loads(line)
            if not r.get("error"):
                done.add((r["task_id"], r["condition"], r["rep"]))

    jobs = []
    for i, t in enumerate(tasks):
        for rep in range(a.repeats):
            order = a.conditions if (i + rep) % 2 == 0 else list(reversed(a.conditions))  # counter-balance order
            for c in order:
                if (t["id"], c, rep) not in done:
                    jobs.append((t, c, rep))
    print(f"{len(tasks)} tasks x {a.repeats} reps x {len(a.conditions)} conditions -> {len(jobs)} runs to do "
          f"({len(done)} already done). Output: {raw}")
    for c in a.conditions:
        print(f"  {c}: model={config.CONDITIONS[c]['model']} thinking={config.CONDITIONS[c]['thinking']}")

    lock, counter = threading.Lock(), {"n": 0}

    def work(job):
        t, c, rep = job
        row = run_one(client, db, t, c, config.CONDITIONS[c], rep)
        with lock:
            with open(raw, "a") as f:
                f.write(json.dumps(row) + "\n")
            counter["n"] += 1
            flag = "OK " if row["correct"] else ("ERR" if row["error"] else "BAD")
            print(f"[{counter['n']}/{len(jobs)}] {flag} {t['id']:7s} {c:9s} rep{rep} "
                  f"tok={row['total_tokens']:6d} t={row['wall_s']:5.1f}s calls={row['n_tool_calls']}"
                  + (f"  {row['error']}" if row["error"] else ""), flush=True)

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(work, jobs))
    print("Done. Next: python analyze.py" + (" --results results_dry" if a.dry_run else ""))


if __name__ == "__main__":
    main()
