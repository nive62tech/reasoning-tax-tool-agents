#!/usr/bin/env python3
"""Computes every extra number the article needs and writes results/final_numbers.md.
Works with any number of repeats. Usage: python final_stats.py [--results results]"""
import argparse, json, math, os, statistics as st
from collections import Counter, defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("--results", default="results")
ap.add_argument("--outlier-calls", type=int, default=40, help="a task with any run above this many tool calls is a 'runaway' task")
a = ap.parse_args()

rows = [json.loads(l) for l in open(os.path.join(a.results, "raw.jsonl"), encoding="utf-8")]
rows = [r for r in rows if not r.get("error")]
C = ("baseline", "reasoning")


def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 2
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def summ(rs):
    n = len(rs)
    if not n: return None
    ks, ka = sum(r["correct"] for r in rs), sum(r["answer_correct"] for r in rs)
    tok = [r["total_tokens"] for r in rs]
    return {"n": n, "strict": ks / n, "strict_ci": wilson(ks, n), "ans": ka / n, "ans_ci": wilson(ka, n),
            "mean_tok": st.mean(tok), "median_tok": st.median(tok),
            "calls": st.mean(r["n_tool_calls"] for r in rs),
            "think": st.mean(r.get("thinking_tokens", 0) for r in rs),
            "wall": st.mean(r["wall_s"] for r in rs), "wall_med": st.median(r["wall_s"] for r in rs)}


def block(title, rs):
    out = [f"### {title}", "", "| Condition | N runs | Strict acc. [95% CI] | Answer-only acc. [95% CI] | Mean tokens | Median tokens | Mean calls | Mean thinking tok | Mean wall s |",
           "|---|---|---|---|---|---|---|---|---|"]
    s = {}
    for c in C:
        x = summ([r for r in rs if r["condition"] == c]); s[c] = x
        if x:
            out.append(f"| {c} | {x['n']} | {x['strict']*100:.1f}% [{x['strict_ci'][0]*100:.1f}, {x['strict_ci'][1]*100:.1f}] | "
                       f"{x['ans']*100:.1f}% [{x['ans_ci'][0]*100:.1f}, {x['ans_ci'][1]*100:.1f}] | {x['mean_tok']:.0f} | {x['median_tok']:.0f} | "
                       f"{x['calls']:.2f} | {x['think']:.0f} | {x['wall']:.1f} |")
    if s[C[0]] and s[C[1]]:
        b, r = s[C[0]], s[C[1]]
        out.append(f"\nToken ratio (mean): **{r['mean_tok']/b['mean_tok']:.2f}x**; (median): **{r['median_tok']/b['median_tok']:.2f}x**; "
                   f"accuracy gain strict: **{(r['strict']-b['strict'])*100:+.1f} pts**, answer-only: **{(r['ans']-b['ans'])*100:+.1f} pts**; "
                   f"mean wall-clock ratio: **{r['wall']/b['wall']:.2f}x**.\n")
    return "\n".join(out) + "\n"


md = ["# Final numbers for the article", ""]
reps = Counter((r["condition"], r["rep"]) for r in rows)
md += ["## Coverage (completed runs per condition and repeat)", "", "| Condition | Repeat | Runs |", "|---|---|---|"]
md += [f"| {c} | {rp} | {n} |" for (c, rp), n in sorted(reps.items())] + [""]

md += ["## All data", "", block("Overall", rows)]
for t in (1, 2, 3):
    md.append(block(f"Tier {t}", [r for r in rows if r["tier"] == t]))

# runaway tasks
run_tasks = sorted({r["task_id"] for r in rows if r["n_tool_calls"] > a.outlier_calls})
md += ["## Runaway runs", ""]
big = [r for r in rows if r["n_tool_calls"] > a.outlier_calls]
if big:
    md += [f"- {r['task_id']} ({r['condition']}, rep {r['rep']}): {r['n_tool_calls']} tool calls, {r['total_tokens']} tokens, correct={r['correct']}" for r in big]
    md += ["", f"Excluding task(s) {', '.join(run_tasks)} from BOTH conditions:", ""]
    keep = [r for r in rows if r["task_id"] not in run_tasks]
    md += [block("Overall (excluding runaway tasks)", keep), block("Tier 3 (excluding runaway tasks)", [r for r in keep if r["tier"] == 3])]
else:
    md += ["No run exceeded the tool-call threshold.", ""]

# chain length
md += ["## Longest chains (6+ reference calls)", "", block("6+ calls", [r for r in rows if r["n_ref_calls"] >= 6])]

# task-level wins and losses
pt = defaultdict(lambda: defaultdict(list))
for r in rows: pt[r["task_id"]][r["condition"]].append(r["correct"])
win = sorted(t for t, d in pt.items() if d["baseline"] and d["reasoning"] and st.mean(d["reasoning"]) > st.mean(d["baseline"]))
loss = sorted(t for t, d in pt.items() if d["baseline"] and d["reasoning"] and st.mean(d["reasoning"]) < st.mean(d["baseline"]))
md += ["## Task-level wins/losses (mean over repeats)", "", f"- Reasoning better: {len(win)} tasks: {', '.join(win) or 'none'}",
       f"- Baseline better: {len(loss)} tasks: {', '.join(loss) or 'none'}", ""]

# repeat-to-repeat consistency
cons = []
for c in C:
    unstable = [t for t, d in pt.items() if len(set(d[c])) > 1]
    cons.append(f"- {c}: {len(unstable)} tasks gave different correctness across repeats ({', '.join(sorted(unstable)) or 'none'})")
md += ["## Repeat-to-repeat stability", ""] + cons + [""]

# failures with detail
md += ["## Every failed run (strict scoring)", "", "| Task | Condition | Rep | Final answer | Expected | Answer correct | Required tools called | Calls | Tokens | Stop |", "|---|---|---|---|---|---|---|---|---|---|"]
for r in sorted((r for r in rows if not r["correct"]), key=lambda r: (r["task_id"], r["condition"], r["rep"])):
    md.append(f"| {r['task_id']} | {r['condition']} | {r['rep']} | {r['final_answer']} | {r['expected']} | {r['answer_correct']} | {r['required_ok']} | {r['n_tool_calls']} | {r['total_tokens']} | {r['stop_reason']} |")
md.append("")

# t3_17 shortcut check
try:
    from tasks import get_tasks
    from mockdb import MockDB
    db = MockDB(); tk = {t["id"]: t for t in get_tasks()}
    sc = [r for r in rows if r["answer_correct"] and not r["required_ok"]]
    md += ["## Correct answers that skipped required tools (possible valid shortcuts)", ""]
    for r in sc:
        t = tk[r["task_id"]]
        cid = next((c[1].get("customer_id") for c in t["reference_calls"] if c[1].get("customer_id")), None)
        tier = db.customers[cid]["tier"] if cid else "n/a"
        md.append(f"- {r['task_id']} ({r['condition']}, rep {r['rep']}): called {r['tool_names']}; customer {cid} is **{tier}** tier; template `{t['template']}`")
    if not sc: md.append("- none")
    md.append("")
except Exception as e:
    md += [f"(shortcut check skipped: {e})", ""]

# token distribution
md += ["## Token distribution (all runs)", "", "| Condition | min | p25 | median | p75 | p90 | max |", "|---|---|---|---|---|---|---|"]
for c in C:
    v = sorted(r["total_tokens"] for r in rows if r["condition"] == c)
    q = lambda p: v[min(len(v) - 1, int(p * (len(v) - 1) + 0.5))]
    md.append(f"| {c} | {v[0]} | {q(.25)} | {q(.5)} | {q(.75)} | {q(.9)} | {v[-1]} |")
md.append("")

out = os.path.join(a.results, "final_numbers.md")
open(out, "w", encoding="utf-8").write("\n".join(md))
print("Wrote", out)
