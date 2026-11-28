# Final numbers for the article

## Coverage (completed runs per condition and repeat)

| Condition | Repeat | Runs |
|---|---|---|
| baseline | 0 | 60 |
| baseline | 1 | 60 |
| reasoning | 0 | 60 |
| reasoning | 1 | 60 |

## All data

### Overall

| Condition | N runs | Strict acc. [95% CI] | Answer-only acc. [95% CI] | Mean tokens | Median tokens | Mean calls | Mean thinking tok | Mean wall s |
|---|---|---|---|---|---|---|---|---|
| baseline | 120 | 95.8% [90.6, 98.2] | 95.8% [90.6, 98.2] | 3421 | 2842 | 3.20 | 0 | 7.1 |
| reasoning | 120 | 96.7% [91.7, 98.7] | 97.5% [92.9, 99.1] | 7350 | 3461 | 5.70 | 680 | 8.8 |

Token ratio (mean): **2.15x**; (median): **1.22x**; accuracy gain strict: **+0.8 pts**, answer-only: **+1.7 pts**; mean wall-clock ratio: **1.23x**.


### Tier 1

| Condition | N runs | Strict acc. [95% CI] | Answer-only acc. [95% CI] | Mean tokens | Median tokens | Mean calls | Mean thinking tok | Mean wall s |
|---|---|---|---|---|---|---|---|---|
| baseline | 40 | 100.0% [91.2, 100.0] | 100.0% [91.2, 100.0] | 1726 | 1710 | 1.00 | 0 | 4.7 |
| reasoning | 40 | 100.0% [91.2, 100.0] | 100.0% [91.2, 100.0] | 2061 | 2041 | 1.00 | 240 | 5.2 |

Token ratio (mean): **1.19x**; (median): **1.19x**; accuracy gain strict: **+0.0 pts**, answer-only: **+0.0 pts**; mean wall-clock ratio: **1.11x**.


### Tier 2

| Condition | N runs | Strict acc. [95% CI] | Answer-only acc. [95% CI] | Mean tokens | Median tokens | Mean calls | Mean thinking tok | Mean wall s |
|---|---|---|---|---|---|---|---|---|
| baseline | 40 | 100.0% [91.2, 100.0] | 100.0% [91.2, 100.0] | 2868 | 2865 | 2.02 | 0 | 5.7 |
| reasoning | 40 | 100.0% [91.2, 100.0] | 100.0% [91.2, 100.0] | 3472 | 3472 | 2.00 | 326 | 6.1 |

Token ratio (mean): **1.21x**; (median): **1.21x**; accuracy gain strict: **+0.0 pts**, answer-only: **+0.0 pts**; mean wall-clock ratio: **1.07x**.


### Tier 3

| Condition | N runs | Strict acc. [95% CI] | Answer-only acc. [95% CI] | Mean tokens | Median tokens | Mean calls | Mean thinking tok | Mean wall s |
|---|---|---|---|---|---|---|---|---|
| baseline | 40 | 87.5% [73.9, 94.5] | 87.5% [73.9, 94.5] | 5670 | 4146 | 6.58 | 0 | 11.0 |
| reasoning | 40 | 90.0% [76.9, 96.0] | 92.5% [80.1, 97.4] | 16516 | 7980 | 14.10 | 1475 | 15.0 |

Token ratio (mean): **2.91x**; (median): **1.92x**; accuracy gain strict: **+2.5 pts**, answer-only: **+5.0 pts**; mean wall-clock ratio: **1.36x**.


## Runaway runs

- t3_09 (reasoning, rep 0): 165 tool calls, 129585 tokens, correct=False
- t3_11 (reasoning, rep 1): 141 tool calls, 126196 tokens, correct=False

Excluding task(s) t3_09, t3_11 from BOTH conditions:

### Overall (excluding runaway tasks)

| Condition | N runs | Strict acc. [95% CI] | Answer-only acc. [95% CI] | Mean tokens | Median tokens | Mean calls | Mean thinking tok | Mean wall s |
|---|---|---|---|---|---|---|---|---|
| baseline | 116 | 97.4% [92.7, 99.1] | 97.4% [92.7, 99.1] | 3168 | 2813 | 2.97 | 0 | 6.5 |
| reasoning | 116 | 98.3% [93.9, 99.5] | 99.1% [95.3, 99.8] | 5074 | 3446 | 3.06 | 592 | 7.8 |

Token ratio (mean): **1.60x**; (median): **1.22x**; accuracy gain strict: **+0.9 pts**, answer-only: **+1.7 pts**; mean wall-clock ratio: **1.20x**.


### Tier 3 (excluding runaway tasks)

| Condition | N runs | Strict acc. [95% CI] | Answer-only acc. [95% CI] | Mean tokens | Median tokens | Mean calls | Mean thinking tok | Mean wall s |
|---|---|---|---|---|---|---|---|---|
| baseline | 36 | 91.7% [78.2, 97.1] | 91.7% [78.2, 97.1] | 5105 | 4086 | 6.22 | 0 | 9.4 |
| reasoning | 36 | 94.4% [81.9, 98.5] | 97.2% [85.8, 99.5] | 10201 | 5642 | 6.53 | 1279 | 12.6 |

Token ratio (mean): **2.00x**; (median): **1.38x**; accuracy gain strict: **+2.8 pts**, answer-only: **+5.6 pts**; mean wall-clock ratio: **1.34x**.


## Longest chains (6+ reference calls)

### 6+ calls

| Condition | N runs | Strict acc. [95% CI] | Answer-only acc. [95% CI] | Mean tokens | Median tokens | Mean calls | Mean thinking tok | Mean wall s |
|---|---|---|---|---|---|---|---|---|
| baseline | 16 | 68.8% [44.4, 85.8] | 68.8% [44.4, 85.8] | 9123 | 7437 | 10.56 | 0 | 15.0 |
| reasoning | 16 | 81.2% [57.0, 93.4] | 81.2% [57.0, 93.4] | 32936 | 15620 | 29.19 | 2416 | 21.8 |

Token ratio (mean): **3.61x**; (median): **2.10x**; accuracy gain strict: **+12.5 pts**, answer-only: **+12.5 pts**; mean wall-clock ratio: **1.45x**.


## Task-level wins/losses (mean over repeats)

- Reasoning better: 2 tasks: t3_10, t3_11
- Baseline better: 2 tasks: t3_09, t3_17

## Repeat-to-repeat stability

- baseline: 1 tasks gave different correctness across repeats (t3_12)
- reasoning: 4 tasks gave different correctness across repeats (t3_09, t3_11, t3_12, t3_17)

## Every failed run (strict scoring)

| Task | Condition | Rep | Final answer | Expected | Answer correct | Required tools called | Calls | Tokens | Stop |
|---|---|---|---|---|---|---|---|---|---|
| t3_09 | reasoning | 0 | None | ['C007', 'C015', 'C028'] | False | True | 165 | 129585 | FinishReason.STOP |
| t3_10 | baseline | 0 | NOT_FOUND | ['C018', 'C019'] | False | False | 6 | 8346 | FinishReason.STOP |
| t3_10 | baseline | 1 | NOT_FOUND | ['C018', 'C019'] | False | False | 4 | 5523 | FinishReason.STOP |
| t3_11 | baseline | 0 | None | ['C011', 'C018', 'C019'] | False | False | 15 | 23208 | FinishReason.STOP |
| t3_11 | baseline | 1 | ANSWER: NOT_FOUND | ['C011', 'C018', 'C019'] | False | False | 4 | 5456 | FinishReason.STOP |
| t3_11 | reasoning | 1 | None | ['C011', 'C018', 'C019'] | False | False | 141 | 126196 | FinishReason.STOP |
| t3_12 | baseline | 1 | None | ['C007', 'C015', 'C028'] | False | True | 15 | 23391 | FinishReason.STOP |
| t3_12 | reasoning | 1 | None | ['C007', 'C015', 'C028'] | False | False | 15 | 66392 | FinishReason.STOP |
| t3_17 | reasoning | 0 | no | no | True | False | 1 | 2417 | FinishReason.STOP |

## Correct answers that skipped required tools (possible valid shortcuts)

- t3_17 (reasoning, rep 0): called ['get_customer']; customer C015 is **gold** tier; template `upgrade_eligibility`

## Token distribution (all runs)

| Condition | min | p25 | median | p75 | p90 | max |
|---|---|---|---|---|---|---|
| baseline | 1674 | 1725 | 2847 | 3583 | 5523 | 23391 |
| reasoning | 1938 | 2090 | 3461 | 5036 | 10696 | 129585 |
