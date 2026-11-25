# Does Extended Reasoning Pay for Itself in Tool-Calling Agents?
Experiment kit: 60 deterministic tool-calling tasks, a runner that executes each one with and without
extended thinking, and an analysis script that outputs article-ready tables and charts.

## 1. Setup (2 minutes)
```bash
cd agent_reasoning_bench
python -m venv .venv && source .venv/bin/activate     # optional
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...                   # Windows PowerShell: $env:ANTHROPIC_API_KEY="..."
```

## 2. Run order
```bash
python validate_tasks.py            # checks the task set (no API calls)
python run_bench.py --dry-run       # offline simulation to confirm everything works (fake numbers, goes to results_dry/)
python run_bench.py --limit 6       # SMOKE TEST: 6 real tasks x 2 conditions. Check it works and glance at cost.
python run_bench.py --repeats 3     # FULL RUN: 60 tasks x 3 reps x 2 conditions = 360 runs
python analyze.py                   # writes results/analysis/summary.md, summary.json, per_run.csv, PNG charts
```
- Interrupt and re-run any time: finished runs are skipped, errored runs are retried.
- `--workers 4` speeds things up but adds rate-limit and timing noise. Use `--workers 1` (default) for the wall-clock numbers you will report.
- Expect a few dollars for the full run at typical Sonnet-class prices (tier 3 chains with thinking are the most expensive part). Do the smoke test first and extrapolate: smoke-test cost x (360 / 12).

## 3. What gets measured
| Item | How |
|---|---|
| Accuracy | A run is correct only if the `ANSWER:` line matches ground truth **and** all required tools were called (no lucky guesses). `answer_correct` and `required_ok` are stored separately. |
| Tokens | Input + output summed over **every turn** (each turn resends the conversation). Thinking tokens are billed as output and are included in `output_tokens`. |
| Time | `wall_s` = whole task incl. tool execution; `api_s` = time spent inside API calls. |
| Efficiency | `(acc_reasoning - acc_baseline) in pts / (extra tokens per task / 1000)`, overall, per tier, and per chain length. |
| Uncertainty | Wilson 95% CI on accuracies; paired bootstrap CI (resampling tasks) on the accuracy difference. |
| Cost | Tokens x prices in `config.py`. **Set the prices to your model's current ones.** |

## 4. The task set (60 tasks, 20 per tier)
All tools are mocked over a seeded in-memory store (30 customers, 40 products, 120 orders, 45 tickets), so ground truth is exact.
- **Tier 1, single lookup:** status, total, email, price, stock, tier, open tickets, newsletter, discount, plus 2 NOT_FOUND checks.
- **Tier 2, two dependent steps:** order to customer to newsletter/name/country; order to first item to product/stock/category; email to tickets; tier to discount; NOT_FOUND chains.
- **Tier 3, multi-tool chains (3 to 10 calls, aggregation and conditional logic):** discounted order total, inventory fulfilment check, big orders in a month to customers with open tickets, lowest-stock product across a customer's orders, rule-based tier-upgrade eligibility.

`tasks.json` has every prompt, expected answer, and reference call chain. The model never sees the reference calls.

## 5. Configuration (`config.py` or environment variables)
- `BASELINE_MODEL`, `REASONING_MODEL`: default is the **same model** with thinking off/on, which isolates the effect of reasoning. To compare two different models, set them to different IDs (e.g. a fast model vs a reasoning model); say so in the article's Method section.
- `THINKING_BUDGET` (default 8000). A good extra experiment: rerun with 2000 and 16000 into separate dirs (`--out results_b2000`) to get a budget-vs-accuracy curve.
- `THINKING_JSON`: override the whole thinking parameter if your model expects a different shape, e.g. `'{"type":"adaptive"}'`.
- `PRICE_IN_PER_MTOK`, `PRICE_OUT_PER_MTOK`, `MAX_TURNS`, `MAX_TOKENS`.

## 6. Troubleshooting
- **404 / model not found:** set `BASELINE_MODEL` and `REASONING_MODEL` to a model ID your account has.
- **400 error mentioning `thinking`:** your model wants a different thinking parameter. Set `THINKING_JSON`, or check the current extended-thinking docs.
- **429 / overloaded:** lower `--workers`. The client already retries up to 6 times.
- **Many "no final answer" failures:** raise `MAX_TURNS`.
- Check `raw.jsonl` (full tool-call logs per run) to see exactly what the model did on any failed run.

## 7. What to send back for the article
1. `results/analysis/summary.md`
2. `results/analysis/summary.json`
3. The 4 PNG charts (optional)
4. Any surprises you noticed (a model, thinking budget, or task that behaved oddly)

## 8. Notes for the Limitations section
- 60 tasks x repeats is small; read the CIs, not just the point estimates.
- Mocked, clean, deterministic tools: real APIs are noisier.
- Token counts are a proxy for cost; pricing and caching differ by provider. Prompt caching is not used here.
- Wall-clock time depends on provider load at run time.
- Thinking tokens are not reported separately, so the "extra output tokens" under reasoning are the best estimate of thinking spend.
- `fake_client.py` produces made-up numbers for testing only. **Never report `results_dry/`.**

## Files
`run_bench.py` runner | `analyze.py` stats + charts | `tasks.py` task generator | `mockdb.py` database + tool implementations |
`scoring.py` answer parsing + failure categories | `validate_tasks.py` sanity checks | `fake_client.py` offline simulator | `config.py` settings


Phase 1 - done
