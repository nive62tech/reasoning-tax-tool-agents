#!/usr/bin/env python3
"""Unattended finisher. Leave it running.

1. Backs up current results.
2. Keeps re-running the Gemini benchmark (resumable) until TARGET_REPEATS repeats are complete,
   sleeping 30 minutes between attempts so quota resets / server overload can clear.
3. Runs analyze.py and final_stats.py.
Usage (PowerShell, venv active, GEMINI_API_KEY set):   python run_everything.py
Optional: $env:TARGET_REPEATS = "3"   (default 2)
"""
import json, os, shutil, subprocess, sys, time
from datetime import datetime

TARGET = int(os.getenv("TARGET_REPEATS", "2"))
WAIT_MIN = int(os.getenv("WAIT_MINUTES", "30"))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "60"))
RAW = os.path.join("results", "raw.jsonl")
env = dict(os.environ, PYTHONUTF8="1")
env.setdefault("GEMINI_MODEL", "gemini-3.5-flash-lite")


def stamp(msg): print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def completed():
    done = set()
    if os.path.exists(RAW):
        for line in open(RAW, encoding="utf-8"):
            r = json.loads(line)
            if not r.get("error") and r["rep"] < TARGET:
                done.add((r["task_id"], r["condition"], r["rep"]))
    return len(done)


AUTH_MARKERS = ("API_KEY_INVALID", "API key not valid", "PERMISSION_DENIED", "UNAUTHENTICATED", "API key expired")


def auth_failed_recently(n=10):
    """True if the last n logged runs all failed because of the API key."""
    if not os.path.exists(RAW):
        return False
    tail = open(RAW, encoding="utf-8").read().splitlines()[-n:]
    rows = [json.loads(l) for l in tail]
    return len(rows) >= 3 and all(r.get("error") and any(m in r["error"] for m in AUTH_MARKERS) for r in rows)


def preflight():
    """One tiny request to confirm the key works before starting a long unattended run."""
    from google import genai
    from google.genai import errors
    key = env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=key)  # keep a reference so the client is not closed mid-request
    try:
        client.models.generate_content(model=env["GEMINI_MODEL"], contents="Reply with the word OK.")
        stamp("Key check passed.")
    except errors.APIError as e:
        if any(m in str(e) for m in AUTH_MARKERS) or e.code in (400, 401, 403):
            sys.exit(f"STOP: Google rejected the API key ({e.code}). Create a fresh key at aistudio.google.com/apikey, "
                     "set it with $env:GEMINI_API_KEY = \"...\" (paste the real key, no placeholder text, no extra spaces), then run again.\n" + str(e)[:300])
        stamp(f"Key check inconclusive ({e.code}: quota/overload). Continuing; the loop will retry.")
    except Exception as e:
        stamp(f"Key check could not run ({type(e).__name__}); continuing anyway.")


def main():
    if not (env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY")):
        sys.exit("GEMINI_API_KEY is not set in this window. Set it, then run again.")
    preflight()
    os.makedirs("results", exist_ok=True)
    if os.path.exists(RAW) and not os.path.exists(os.path.join("results", "raw_backup_before_finish.jsonl")):
        shutil.copy(RAW, os.path.join("results", "raw_backup_before_finish.jsonl"))
        stamp("Backed up results/raw.jsonl")
    need = 60 * 2 * TARGET
    stamp(f"Target: {TARGET} repeats = {need} completed runs. Model: {env['GEMINI_MODEL']}")
    for attempt in range(1, MAX_ATTEMPTS + 1):
        have = completed()
        stamp(f"Attempt {attempt}: {have}/{need} runs complete")
        if have >= need:
            break
        subprocess.run([sys.executable, "run_bench.py", "--provider", "gemini", "--repeats", str(TARGET), "--rpm", "4"], env=env)
        if completed() >= need:
            break
        if auth_failed_recently():
            sys.exit("STOP: the API key was rejected again during the run. Fix the key and re-run python run_everything.py.")
        stamp(f"Not finished (quota or server load). Sleeping {WAIT_MIN} min, then retrying...")
        time.sleep(WAIT_MIN * 60)
    stamp(f"Final coverage: {completed()}/{need}")
    subprocess.run([sys.executable, "analyze.py"], env=env)
    subprocess.run([sys.executable, "final_stats.py"], env=env)
    stamp("ALL DONE. Open results\\final_numbers.md and results\\analysis\\summary.md")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        stamp("Stopped by user. Re-run later; progress is saved.")