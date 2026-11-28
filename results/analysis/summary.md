# Results summary

Models: baseline=`gemini-3.5-flash-lite`, reasoning=`gemini-3.5-flash-lite` (baseline thinking: `level:minimal`; reasoning thinking: `level:high`). Provider: gemini. Runs analysed: 120 baseline, 120 reasoning.
Prices used for cost: $0.75/Mtok input, $3.75/Mtok output (list-price equivalent; edit config.py). Total tokens = input + output (output includes thinking tokens). Wall-clock excludes client-side throttling and retry sleeps.

## Headline numbers (for the abstract)

- Accuracy: **95.8%** (baseline) vs **96.7%** (reasoning): **+0.8 points** (95% CI -3.3 to 5.8).
- Tokens per task: **3421** vs **7350** (**2.15x**).
- Wall-clock per task: **7.1s** vs **8.8s** (**1.23x**).
- Efficiency: **0.21 accuracy points per 1,000 extra tokens**.
- Cost per task: $0.0030 vs $0.0084; cost per *correct* answer: $0.0031 vs $0.0087.
- Mean tool calls per task: 3.20 vs 5.70.

## Overall

| Scope | N runs/cond | Baseline acc. | Reasoning acc. | Gain (pts) [95% CI] | Tokens/task base → reas | Token ratio | Time ratio | Gain per 1k extra tokens |
|---|---|---|---|---|---|---|---|---|
| All tasks | 120/120 | 95.8% | 96.7% | +0.8 [-3.3, 5.8] | 3421 → 7350 | 2.15x | 1.23x | 0.21 |

## By complexity tier

| Tier | N runs/cond | Baseline acc. | Reasoning acc. | Gain (pts) [95% CI] | Tokens/task base → reas | Token ratio | Time ratio | Gain per 1k extra tokens |
|---|---|---|---|---|---|---|---|---|
| Tier 1: single lookup | 40/40 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1726 → 2061 | 1.19x | 1.11x | 0.00 |
| Tier 2: two-step | 40/40 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2868 → 3472 | 1.21x | 1.07x | 0.00 |
| Tier 3: multi-tool chain | 40/40 | 87.5% | 90.0% | +2.5 [-10.0, 17.5] | 5670 → 16516 | 2.91x | 1.36x | 0.23 |

## By minimum number of dependent tool calls (finer complexity curve)

| Minimum tool calls needed | N runs/cond | Baseline acc. | Reasoning acc. | Gain (pts) [95% CI] | Tokens/task base → reas | Token ratio | Time ratio | Gain per 1k extra tokens |
|---|---|---|---|---|---|---|---|---|
| 1 call | 44/44 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1726 → 2065 | 1.20x | 1.14x | 0.00 |
| 2 calls | 32/32 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2874 → 3482 | 1.21x | 1.03x | 0.00 |
| 3 calls | 24/24 | 100.0% | 95.8% | -4.2 [-12.5, 0.0] | 3498 → 5689 | 1.63x | 1.35x | -1.90 |
| 4-5 calls | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 3186 → 4037 | 1.27x | 0.76x | 0.00 |
| 6+ calls | 16/16 | 68.8% | 81.2% | +12.5 [-12.5, 43.8] | 9123 → 32936 | 3.61x | 1.45x | 0.52 |

## By task template

| Task template | N runs/cond | Baseline acc. | Reasoning acc. | Gain (pts) [95% CI] | Tokens/task base → reas | Token ratio | Time ratio | Gain per 1k extra tokens |
|---|---|---|---|---|---|---|---|---|
| big_orders_open_tickets | 8/8 | 37.5% | 62.5% | +25.0 [-25.0, 75.0] | 10673 → 55334 | 5.18x | 1.68x | 0.56 |
| customer_discount | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2666 → 3305 | 1.24x | 1.27x | 0.00 |
| customer_email | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1721 → 2088 | 1.21x | 1.35x | 0.00 |
| customer_tier | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1709 → 1988 | 1.16x | 0.66x | 0.00 |
| discounted_total | 8/8 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 4136 → 5328 | 1.29x | 0.90x | 0.00 |
| email_open_tickets | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2774 → 3461 | 1.25x | 1.01x | 0.00 |
| fulfillable | 8/8 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 3112 → 3956 | 1.27x | 1.07x | 0.00 |
| lowest_stock_across_orders | 8/8 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 7574 → 10538 | 1.39x | 1.09x | 0.00 |
| newsletter | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1710 → 2026 | 1.19x | 0.88x | 0.00 |
| not_found | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1689 → 2053 | 1.22x | 1.32x | 0.00 |
| not_found_chain | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1722 → 2105 | 1.22x | 1.64x | 0.00 |
| open_tickets | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1756 → 2149 | 1.22x | 0.85x | 0.00 |
| order_buyer_tickets | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2891 → 3708 | 1.28x | 1.23x | 0.00 |
| order_country | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2898 → 3478 | 1.20x | 1.10x | 0.00 |
| order_customer_name | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2864 → 3366 | 1.18x | 1.07x | 0.00 |
| order_first_item_category | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2880 → 3513 | 1.22x | 0.67x | 0.00 |
| order_first_item_name | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2862 → 3426 | 1.20x | 0.89x | 0.00 |
| order_first_item_stock | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 3155 → 3602 | 1.14x | 1.08x | 0.00 |
| order_newsletter | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 3965 → 4757 | 1.20x | 1.17x | 0.00 |
| order_status | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1792 → 2086 | 1.16x | 1.27x | 0.00 |
| order_total | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1795 → 2158 | 1.20x | 1.14x | 0.00 |
| product_price | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1711 → 2021 | 1.18x | 2.05x | 0.00 |
| stock | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1699 → 2031 | 1.20x | 1.34x | 0.00 |
| tier_discount | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1679 → 2012 | 1.20x | 0.80x | 0.00 |
| upgrade_eligibility | 8/8 | 100.0% | 87.5% | -12.5 [-37.5, 0.0] | 2855 → 7423 | 2.60x | 2.50x | -2.74 |

## Failure categories (count of failed runs)

| Category | Baseline | Reasoning |
|---|---|---|
| no final answer (ran out of turns/tokens) | 2 | 3 |
| right answer without required calls (guess) | 0 | 1 |
| skipped required tool calls | 3 | 0 |

## Task-level wins/losses

- Reasoning better on 2 tasks: t3_10, t3_11
- Baseline better on 2 tasks: t3_09, t3_17

## Token accounting note

Mean output tokens per task rose from 150 to 970 (+820); this increase is almost entirely thinking tokens. Mean input tokens: 3271 vs 6379. Provider-reported thinking tokens per task: 0 (baseline) vs 680 (reasoning).
