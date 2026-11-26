#!/usr/bin/env python3
"""Run every task under both conditions and log accuracy, tokens, and time.

Examples
  python run_bench.py --provider gemini --dry-run     # offline test, no API calls
  python run_bench.py --provider gemini --limit 6     # smoke test with real API calls
  python run_bench.py --provider gemini --repeats 1   # full run
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
from mockdb import MockDB
from providers import AnthropicProvider, GeminiProvider, QuotaExhausted, new_state
from scoring import score_run
from tasks import build_tasks


def run_one(provider, db, task, cname, cond, rep):
    st, error = new_state(), None
    t0 = time.perf_counter()
    try:
        provider.run(task, db, cond, st)
    except QuotaExhausted:
        raise
    except Exception as e:  # recorded, excluded from analysis, retried on next run
        error = f"{type(e).__name__}: {e}"[:500]
    raw_wall = time.perf_counter() - t0
    wall = max(0.0, raw_wall - st["wait_s"])  # exclude client-side throttling / retry sleeps

    names = [t["name"] for t in st["tool_log"]]
    total = st["input"] + st["output"] + st["cache_creation"] + st["cache_read"]
    row = {
        "task_id": task["id"], "tier": task["tier"], "template": task["template"],
        "n_ref_calls": task["n_ref_calls"], "condition": cname, "model": cond["model"],
        "thinking_spec": cond["thinking"], "rep": rep, "expected": task["expected"],
        "turns": st["turns"], "n_tool_calls": len(names),
        "n_tool_errors": sum(t["error"] for t in st["tool_log"]), "tool_names": names, "tool_log": st["tool_log"],
        "input_tokens": st["input"], "output_tokens": st["output"], "thinking_tokens": st["thinking"],
        "cache_creation_tokens": st["cache_creation"], "cache_read_tokens": st["cache_read"],
        "total_tokens": total, "thinking_chars": st["thinking_chars"],
        "wall_s": round(wall, 3), "wall_s_raw": round(raw_wall, 3), "api_s": round(st["api_s"], 3),
        "stop_reason": st["stop_reason"], "error": error, "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    row.update(score_run(task, st["final_text"], names))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["anthropic", "gemini"], default=config.PROVIDER)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--workers", type=int, default=1, help="parallel runs (1 gives the cleanest timing)")
    ap.add_argument("--limit", type=int, help="only N tasks, round-robin across tiers (smoke test)")
    ap.add_argument("--max-runs", type=int, help="stop after N runs this session (useful for daily free-tier quotas)")
    ap.add_argument("--rpm", type=float, help="Gemini: max requests per minute (default from config)")
    ap.add_argument("--tiers", type=int, nargs="*", default=[1, 2, 3])
    ap.add_argument("--conditions", nargs="*", default=["baseline", "reasoning"])
    ap.add_argument("--out", default=None, help="output dir (default results/ or results_dry/)")
    ap.add_argument("--dry-run", action="store_true", help="simulate the agent offline")
    a = ap.parse_args()

    out_dir = a.out or ("results_dry" if a.dry_run else "results")
    os.makedirs(out_dir, exist_ok=True)
    raw = os.path.join(out_dir, "raw.jsonl")
    conds = config.get_conditions(a.provider)
    p_in, p_out = config.get_prices(a.provider)

    db = MockDB()
    tasks = [t for t in build_tasks(db) if t["tier"] in a.tiers]
    if a.limit:
        by = {k: [t for t in tasks if t["tier"] == k] for k in a.tiers}
        tasks = [by[k][i] for i in range(a.limit) for k in a.tiers if i < len(by[k])][: a.limit]

    if a.provider == "anthropic":
        if a.dry_run:
            from fake_client import FakeClient
            provider = AnthropicProvider(FakeClient(tasks))
        else:
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise SystemExit("Set ANTHROPIC_API_KEY first (or use --dry-run).")
            import anthropic
            provider = AnthropicProvider(anthropic.Anthropic(max_retries=6, timeout=300))
    else:
        from google.genai import errors, types
        if a.dry_run:
            from fake_client import FakeGeminiClient
            provider = GeminiProvider(FakeGeminiClient(tasks), types, errors, rpm=0)
        else:
            key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not key:
                raise SystemExit("Set GEMINI_API_KEY first (or use --dry-run).")
            from google import genai
            provider = GeminiProvider(genai.Client(api_key=key), types, errors, rpm=a.rpm)

    json.dump({"provider": a.provider, "conditions": conds, "price_in": p_in, "price_out": p_out,
               "dry_run": a.dry_run}, open(os.path.join(out_dir, "meta.json"), "w"), indent=1)

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
    if a.max_runs:
        jobs = jobs[: a.max_runs]
    print(f"{len(tasks)} tasks x {a.repeats} reps x {len(a.conditions)} conditions -> {len(jobs)} runs this session "
          f"({len(done)} already done). Provider: {a.provider}. Output: {raw}")
    for c in a.conditions:
        print(f"  {c}: model={conds[c]['model']} thinking={conds[c]['thinking']}")

    lock, counter, abort = threading.Lock(), {"n": 0}, threading.Event()

    def work(job):
        if abort.is_set():
            return
        t, c, rep = job
        try:
            row = run_one(provider, db, t, c, conds[c], rep)
        except QuotaExhausted as e:
            abort.set()
            print(f"\nDAILY QUOTA REACHED: {e}\nProgress is saved. Re-run the same command later to continue.", flush=True)
            return
        with lock:
            with open(raw, "a") as f:
                f.write(json.dumps(row) + "\n")
            counter["n"] += 1
            flag = "OK " if row["correct"] else ("ERR" if row["error"] else "BAD")
            print(f"[{counter['n']}/{len(jobs)}] {flag} {t['id']:7s} {c:9s} rep{rep} "
                  f"tok={row['total_tokens']:6d} think={row['thinking_tokens']:5d} t={row['wall_s']:5.1f}s "
                  f"calls={row['n_tool_calls']}" + (f"  {row['error']}" if row["error"] else ""), flush=True)

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(work, jobs))
    print("Done. Next: python analyze.py" + (f" --results {out_dir}" if out_dir != "results" else ""))


if __name__ == "__main__":
    main()
