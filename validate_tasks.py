#!/usr/bin/env python3
"""Sanity-check the task set: reference calls run without error, prompts are unique,
and answer types are well-formed. Run this before spending API credits."""
from collections import Counter
from mockdb import MockDB, execute_tool
from tasks import build_tasks
from scoring import answer_matches

db = MockDB()
tasks = build_tasks(db)
bad = 0
assert len({t["prompt"] for t in tasks}) == len(tasks), "duplicate prompts"
for t in tasks:
    errs = [execute_tool(db, n, a)[1] for n, a in t["reference_calls"]]
    expect_err = t["expected"] == "NOT_FOUND"
    if (any(errs) and not expect_err) or (expect_err and not any(errs)):
        print("PROBLEM", t["id"], t["reference_calls"]); bad += 1
    exp = t["expected"]
    probe = ", ".join(exp) if isinstance(exp, list) else str(exp)
    if not answer_matches(t, probe):
        print("SCORER MISMATCH", t["id"], exp); bad += 1
print(f"{len(tasks)} tasks, tiers {dict(Counter(t['tier'] for t in tasks))}, problems: {bad}")
raise SystemExit(1 if bad else 0)
