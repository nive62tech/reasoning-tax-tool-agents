# Results summary

Models: baseline=`gemini-3.5-flash-lite`, reasoning=`gemini-3.5-flash-lite` (baseline thinking: `level:minimal`; reasoning thinking: `level:high`). Provider: gemini. Runs analysed: 60 baseline, 60 reasoning.
Prices used for cost: $0.75/Mtok input, $3.75/Mtok output (list-price equivalent; edit config.py). Total tokens = input + output (output includes thinking tokens). Wall-clock excludes client-side throttling and retry sleeps.

## Headline numbers (for the abstract)

- Accuracy: **96.7%** (baseline) vs **96.7%** (reasoning): **+0.0 points** (95% CI -6.7 to 6.7).
- Tokens per task: **3475** vs **6882** (**1.98x**).
- Wall-clock per task: **10.6s** vs **11.8s** (**1.11x**).
- Efficiency: **0.00 accuracy points per 1,000 extra tokens**.
- Cost per task: $0.0031 vs $0.0082; cost per *correct* answer: $0.0032 vs $0.0085.
- Mean tool calls per task: 3.23 vs 5.90.

## Overall

| Scope | N runs/cond | Baseline acc. | Reasoning acc. | Gain (pts) [95% CI] | Tokens/task base → reas | Token ratio | Time ratio | Gain per 1k extra tokens |
|---|---|---|---|---|---|---|---|---|
| All tasks | 60/60 | 96.7% | 96.7% | +0.0 [-6.7, 6.7] | 3475 → 6882 | 1.98x | 1.11x | 0.00 |

## By complexity tier

| Tier | N runs/cond | Baseline acc. | Reasoning acc. | Gain (pts) [95% CI] | Tokens/task base → reas | Token ratio | Time ratio | Gain per 1k extra tokens |
|---|---|---|---|---|---|---|---|---|
| Tier 1: single lookup | 20/20 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1725 → 2066 | 1.20x | 1.09x | 0.00 |
| Tier 2: two-step | 20/20 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2840 → 3464 | 1.22x | 1.03x | 0.00 |
| Tier 3: multi-tool chain | 20/20 | 90.0% | 90.0% | +0.0 [-20.0, 20.0] | 5860 → 15117 | 2.58x | 1.15x | 0.00 |

## By minimum number of dependent tool calls (finer complexity curve)

| Minimum tool calls needed | N runs/cond | Baseline acc. | Reasoning acc. | Gain (pts) [95% CI] | Tokens/task base → reas | Token ratio | Time ratio | Gain per 1k extra tokens |
|---|---|---|---|---|---|---|---|---|
| 1 call | 22/22 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1725 → 2064 | 1.20x | 1.12x | 0.00 |
| 2 calls | 16/16 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2840 → 3502 | 1.23x | 0.98x | 0.00 |
| 3 calls | 12/12 | 100.0% | 91.7% | -8.3 [-25.0, 0.0] | 3513 → 5707 | 1.62x | 1.27x | -3.80 |
| 4-5 calls | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 3191 → 3859 | 1.21x | 0.68x | 0.00 |
| 6+ calls | 8/8 | 75.0% | 87.5% | +12.5 [-25.0, 50.0] | 9573 → 29408 | 3.07x | 1.15x | 0.63 |

## By task template

| Task template | N runs/cond | Baseline acc. | Reasoning acc. | Gain (pts) [95% CI] | Tokens/task base → reas | Token ratio | Time ratio | Gain per 1k extra tokens |
|---|---|---|---|---|---|---|---|---|
| big_orders_open_tickets | 4/4 | 50.0% | 75.0% | +25.0 [-50.0, 100.0] | 11462 → 48766 | 4.25x | 1.26x | 0.67 |
| customer_discount | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2666 → 3338 | 1.25x | 1.36x | 0.00 |
| customer_email | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1717 → 2066 | 1.20x | 1.42x | 0.00 |
| customer_tier | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1710 → 1992 | 1.17x | 0.58x | 0.00 |
| discounted_total | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 4138 → 5398 | 1.30x | 0.82x | 0.00 |
| email_open_tickets | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2778 → 3522 | 1.27x | 0.93x | 0.00 |
| fulfillable | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 3115 → 3839 | 1.23x | 1.04x | 0.00 |
| lowest_stock_across_orders | 4/4 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 7683 → 10050 | 1.31x | 0.96x | 0.00 |
| newsletter | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1710 → 2026 | 1.18x | 0.81x | 0.00 |
| not_found | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1690 → 2079 | 1.23x | 1.27x | 0.00 |
| not_found_chain | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1722 → 2050 | 1.19x | 1.67x | 0.00 |
| open_tickets | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1756 → 2179 | 1.24x | 0.78x | 0.00 |
| order_buyer_tickets | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2891 → 3659 | 1.27x | 1.19x | 0.00 |
| order_country | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2900 → 3476 | 1.20x | 1.07x | 0.00 |
| order_customer_name | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2864 → 3354 | 1.17x | 1.02x | 0.00 |
| order_first_item_category | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2876 → 3557 | 1.24x | 0.51x | 0.00 |
| order_first_item_name | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2862 → 3444 | 1.20x | 0.83x | 0.00 |
| order_first_item_stock | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 2879 → 3667 | 1.27x | 1.11x | 0.00 |
| order_newsletter | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 3958 → 4568 | 1.15x | 1.17x | 0.00 |
| order_status | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1792 → 2054 | 1.15x | 1.27x | 0.00 |
| order_total | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1795 → 2134 | 1.19x | 1.05x | 0.00 |
| product_price | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1706 → 2025 | 1.19x | 2.36x | 0.00 |
| stock | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1695 → 2064 | 1.22x | 1.40x | 0.00 |
| tier_discount | 2/2 | 100.0% | 100.0% | +0.0 [0.0, 0.0] | 1679 → 2038 | 1.21x | 0.71x | 0.00 |
| upgrade_eligibility | 4/4 | 100.0% | 75.0% | -25.0 [-75.0, 0.0] | 2904 → 7529 | 2.59x | 2.30x | -5.40 |

## Failure categories (count of failed runs)

| Category | Baseline | Reasoning |
|---|---|---|
| no final answer (ran out of turns/tokens) | 1 | 1 |
| right answer without required calls (guess) | 0 | 1 |
| skipped required tool calls | 1 | 0 |

## Task-level wins/losses

- Reasoning better on 2 tasks: t3_10, t3_11
- Baseline better on 2 tasks: t3_09, t3_17

## Token accounting note

Mean output tokens per task rose from 153 to 1023 (+870); this increase is almost entirely thinking tokens. Mean input tokens: 3322 vs 5859. Provider-reported thinking tokens per task: 0 (baseline) vs 712 (reasoning).
