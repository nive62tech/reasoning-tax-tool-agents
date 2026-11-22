#!/usr/bin/env python3
"""Turn raw.jsonl into article-ready tables, charts, and the efficiency metric.

  python analyze.py                      # reads results/raw.jsonl
  python analyze.py --results results_dry
Outputs (in <results>/analysis/): summary.md, summary.json, per_run.csv, *.png
"""
import argparse
import csv
import json
import math
import os
import random
from collections import Counter, defaultdict

import config
from scoring import classify_failure

TIER_NAMES = {1: "Tier 1: single lookup", 2: "Tier 2: two-step", 3: "Tier 3: multi-tool chain"}


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 2
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def cost(row):
    return (row["input_tokens"] + row["cache_creation_tokens"] + row["cache_read_tokens"]) * config.PRICE_IN_PER_MTOK / 1e6 \
        + row["output_tokens"] * config.PRICE_OUT_PER_MTOK / 1e6


def stats(rows):
    n = len(rows)
    k = sum(r["correct"] for r in rows)
    lo, hi = wilson(k, n)
    return {"n": n, "acc": k / n if n else float("nan"), "ci_lo": lo, "ci_hi": hi,
            "tokens": mean(r["total_tokens"] for r in rows), "in_tokens": mean(r["input_tokens"] for r in rows),
            "out_tokens": mean(r["output_tokens"] for r in rows), "wall_s": mean(r["wall_s"] for r in rows),
            "calls": mean(r["n_tool_calls"] for r in rows), "cost": mean(cost(r) for r in rows),
            "cost_per_correct": (sum(cost(r) for r in rows) / k) if k else float("nan")}


def compare(base, reas):
    b, r = stats(base), stats(reas)
    gain = (r["acc"] - b["acc"]) * 100
    extra = r["tokens"] - b["tokens"]
    eff = gain / (extra / 1000) if extra > 0 else float("nan")
    return {"base": b, "reas": r, "gain_pts": gain, "extra_tokens": extra,
            "token_ratio": r["tokens"] / b["tokens"] if b["tokens"] else float("nan"),
            "time_ratio": r["wall_s"] / b["wall_s"] if b["wall_s"] else float("nan"),
            "gain_per_1k_tokens": eff, "paired_ci": paired_ci(base, reas)}


def paired_ci(base, reas, iters=5000, seed=1):
    """Bootstrap CI (over tasks) for the accuracy difference in percentage points."""
    pb, pr = defaultdict(list), defaultdict(list)
    for r in base: pb[r["task_id"]].append(r["correct"])
    for r in reas: pr[r["task_id"]].append(r["correct"])
    ids = [t for t in pb if t in pr]
    if len(ids) < 2:
        return (float("nan"), float("nan"))
    d = [mean(pr[t]) - mean(pb[t]) for t in ids]
    rng = random.Random(seed)
    boots = sorted(mean(rng.choices(d, k=len(d))) * 100 for _ in range(iters))
    return boots[int(0.025 * iters)], boots[int(0.975 * iters)]


def f(x, nd=1, suf=""):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}{suf}"


def chain_bin(n):
    return "1 call" if n == 1 else "2 calls" if n == 2 else "3 calls" if n == 3 else "4-5 calls" if n <= 5 else "6+ calls"


def table(groups, label):
    out = [f"| {label} | N runs/cond | Baseline acc. | Reasoning acc. | Gain (pts) [95% CI] | Tokens/task base → reas | Token ratio | Time ratio | Gain per 1k extra tokens |",
           "|---|---|---|---|---|---|---|---|---|"]
    for name, (b, r) in groups:
        c = compare(b, r)
        lo, hi = c["paired_ci"]
        out.append(f"| {name} | {c['base']['n']}/{c['reas']['n']} | {f(c['base']['acc']*100,1,'%')} | {f(c['reas']['acc']*100,1,'%')} | "
                   f"{c['gain_pts']:+.1f} [{f(lo,1)}, {f(hi,1)}] | {c['base']['tokens']:.0f} → {c['reas']['tokens']:.0f} | "
                   f"{f(c['token_ratio'],2,'x')} | {f(c['time_ratio'],2,'x')} | {f(c['gain_per_1k_tokens'],2)} |")
    return "\n".join(out), {name: compare(b, r) for name, (b, r) in groups}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(os.path.join(a.results, "raw.jsonl"))]
    rows = [r for r in rows if not r.get("error")]
    out_dir = os.path.join(a.results, "analysis")
    os.makedirs(out_dir, exist_ok=True)
    base = [r for r in rows if r["condition"] == "baseline"]
    reas = [r for r in rows if r["condition"] == "reasoning"]
    if not base or not reas:
        raise SystemExit("Need completed runs for both conditions.")

    md = ["# Results summary", "",
          f"Models: baseline=`{base[0]['model']}`, reasoning=`{reas[0]['model']}` "
          f"(thinking budget {config.THINKING_PARAM}). Runs analysed: {len(base)} baseline, {len(reas)} reasoning.",
          f"Prices used for cost: ${config.PRICE_IN_PER_MTOK}/Mtok input, ${config.PRICE_OUT_PER_MTOK}/Mtok output "
          "(edit config.py). Total tokens = input + output (output includes thinking tokens).", ""]

    ov_md, ov = table([("All tasks", (base, reas))], "Scope")
    tier_groups = [(TIER_NAMES[t], ([r for r in base if r["tier"] == t], [r for r in reas if r["tier"] == t]))
                   for t in sorted({r["tier"] for r in rows})]
    tier_md, tiers = table(tier_groups, "Tier")
    bins = ["1 call", "2 calls", "3 calls", "4-5 calls", "6+ calls"]
    chain_groups = [(b, ([r for r in base if chain_bin(r["n_ref_calls"]) == b], [r for r in reas if chain_bin(r["n_ref_calls"]) == b]))
                    for b in bins]
    chain_groups = [(n, g) for n, g in chain_groups if g[0] and g[1]]
    chain_md, chains = table(chain_groups, "Minimum tool calls needed")
    tmpl_groups = [(t, ([r for r in base if r["template"] == t], [r for r in reas if r["template"] == t]))
                   for t in sorted({r["template"] for r in rows})]
    tmpl_md, _ = table(tmpl_groups, "Task template")

    c = ov["All tasks"]
    md += ["## Headline numbers (for the abstract)", "",
           f"- Accuracy: **{c['base']['acc']*100:.1f}%** (baseline) vs **{c['reas']['acc']*100:.1f}%** (reasoning): "
           f"**{c['gain_pts']:+.1f} points** (95% CI {f(c['paired_ci'][0])} to {f(c['paired_ci'][1])}).",
           f"- Tokens per task: **{c['base']['tokens']:.0f}** vs **{c['reas']['tokens']:.0f}** (**{f(c['token_ratio'],2,'x')}**).",
           f"- Wall-clock per task: **{c['base']['wall_s']:.1f}s** vs **{c['reas']['wall_s']:.1f}s** (**{f(c['time_ratio'],2,'x')}**).",
           f"- Efficiency: **{f(c['gain_per_1k_tokens'],2)} accuracy points per 1,000 extra tokens**.",
           f"- Cost per task: ${c['base']['cost']:.4f} vs ${c['reas']['cost']:.4f}; cost per *correct* answer: "
           f"${c['base']['cost_per_correct']:.4f} vs ${c['reas']['cost_per_correct']:.4f}.",
           f"- Mean tool calls per task: {c['base']['calls']:.2f} vs {c['reas']['calls']:.2f}.", "",
           "## Overall", "", ov_md, "", "## By complexity tier", "", tier_md, "",
           "## By minimum number of dependent tool calls (finer complexity curve)", "", chain_md, "",
           "## By task template", "", tmpl_md, ""]

    # Failure analysis
    fb, fr = Counter(classify_failure(r) for r in base), Counter(classify_failure(r) for r in reas)
    cats = sorted({k for k in list(fb) + list(fr) if k})
    md += ["## Failure categories (count of failed runs)", "", "| Category | Baseline | Reasoning |", "|---|---|---|"]
    md += [f"| {k} | {fb[k]} | {fr[k]} |" for k in cats] or ["| (no failures) | 0 | 0 |"]
    md.append("")

    # Where reasoning helped / hurt at task level
    pb, pr = defaultdict(list), defaultdict(list)
    for r in base: pb[r["task_id"]].append(r["correct"])
    for r in reas: pr[r["task_id"]].append(r["correct"])
    helped = sorted(t for t in pb if t in pr and mean(pr[t]) > mean(pb[t]))
    hurt = sorted(t for t in pb if t in pr and mean(pr[t]) < mean(pb[t]))
    md += ["## Task-level wins/losses", "", f"- Reasoning better on {len(helped)} tasks: {', '.join(helped) or 'none'}",
           f"- Baseline better on {len(hurt)} tasks: {', '.join(hurt) or 'none'}", ""]

    # Thinking token estimate
    extra_out = c["reas"]["out_tokens"] - c["base"]["out_tokens"]
    md += ["## Token accounting note", "",
           f"Mean output tokens per task rose from {c['base']['out_tokens']:.0f} to {c['reas']['out_tokens']:.0f} "
           f"(+{extra_out:.0f}); this increase is almost entirely thinking tokens. Mean input tokens: "
           f"{c['base']['in_tokens']:.0f} vs {c['reas']['in_tokens']:.0f}.", ""]
    open(os.path.join(out_dir, "summary.md"), "w").write("\n".join(md))
    json.dump({"overall": ov, "tiers": tiers, "chain_length": chains}, open(os.path.join(out_dir, "summary.json"), "w"), indent=1, default=str)

    with open(os.path.join(out_dir, "per_run.csv"), "w", newline="") as fh:
        keys = ["task_id", "tier", "template", "n_ref_calls", "condition", "model", "rep", "correct", "answer_correct",
                "required_ok", "final_answer", "expected", "turns", "n_tool_calls", "n_tool_errors", "input_tokens",
                "output_tokens", "total_tokens", "wall_s", "api_s", "stop_reason"]
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # Charts
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping charts")
        plt = None
    if plt:
        names = [TIER_NAMES[t].split(":")[0] for t in sorted({r["tier"] for r in rows})]
        tk = list(tiers.values())
        x = range(len(tk)); w = 0.38
        fig, ax = plt.subplots(figsize=(6, 4))
        for i, (key, lab) in enumerate([("base", "Baseline"), ("reas", "Reasoning")]):
            acc = [t[key]["acc"] * 100 for t in tk]
            err = [[(t[key]["acc"] - t[key]["ci_lo"]) * 100 for t in tk], [(t[key]["ci_hi"] - t[key]["acc"]) * 100 for t in tk]]
            ax.bar([j + (i - .5) * w for j in x], acc, w, yerr=err, capsize=3, label=lab)
        ax.set_xticks(list(x)); ax.set_xticklabels(names); ax.set_ylabel("Accuracy (%)"); ax.set_ylim(0, 105)
        ax.set_title("Accuracy by task tier (95% Wilson CI)"); ax.legend(); fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "accuracy_by_tier.png"), dpi=160); plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 4))
        for i, (key, lab) in enumerate([("base", "Baseline"), ("reas", "Reasoning")]):
            ax.bar([j + (i - .5) * w for j in x], [t[key]["tokens"] for t in tk], w, label=lab)
        ax.set_xticks(list(x)); ax.set_xticklabels(names); ax.set_ylabel("Mean total tokens per task")
        ax.set_title("Token cost by task tier"); ax.legend(); fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "tokens_by_tier.png"), dpi=160); plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 4.5))
        for key, lab, m in [("base", "Baseline", "o"), ("reas", "Reasoning", "s")]:
            xs, ys = [t[key]["tokens"] for t in tk], [t[key]["acc"] * 100 for t in tk]
            ax.plot(xs, ys, marker=m, label=lab)
            for xx, yy, n in zip(xs, ys, names):
                ax.annotate(n, (xx, yy), textcoords="offset points", xytext=(5, 5), fontsize=8)
        ax.set_xlabel("Mean total tokens per task"); ax.set_ylabel("Accuracy (%)"); ax.set_ylim(0, 105)
        ax.set_title("Accuracy vs token cost"); ax.legend(); fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "accuracy_vs_tokens.png"), dpi=160); plt.close(fig)

        ck = list(chains.values())
        if ck:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar(list(chains), [c_["gain_pts"] for c_ in ck])
            ax.axhline(0, color="k", lw=.8); ax.set_ylabel("Accuracy gain from reasoning (pts)")
            ax.set_xlabel("Minimum dependent tool calls"); ax.set_title("Where does reasoning pay off?")
            fig.tight_layout(); fig.savefig(os.path.join(out_dir, "gain_by_chain_length.png"), dpi=160); plt.close(fig)

    print(f"Wrote {out_dir}/summary.md (+ summary.json, per_run.csv, charts)")


if __name__ == "__main__":
    main()
