# Cardmember Profitability Modeling — Amex Campus Challenge 2026 (Round 1)

A deterministic, first-principles P&L framework that ranks **500,000 Premier Cardmembers** by estimated annual profitability and identifies the **top 20%** — built with **zero labeled training data**, calibrated purely through disciplined leaderboard experimentation.

**Final public leaderboard accuracy: 0.901.**

---

## The Problem

Given ~23 masked cardmember attributes spanning spend behavior, revolve balance, riskiness and benefit utilization, identify which 20% of the portfolio is most profitable to the issuer. The constraints:

- **No training labels.** The target is hidden; the only feedback signal is an accuracy score from a public leaderboard.
- **Deterministic framework required.** Round 1 rewards an explainable, scalable profitability equation over a black-box model.
- **Set-overlap accuracy** on the top-20% flag means only the **80th-percentile decision boundary** matters — changes that are rank-neutral, or that only reshuffle members well above or well below the cutoff, cannot move the score.

This makes the task closer to *reverse-engineering a hidden target under a limited query budget* than to standard supervised learning.

---

## The Approach

### 1. Bottom-up P&L equation

Each cardmember's annual profit is modeled from real credit-card unit economics, with every coefficient derived from issuer economics before any leaderboard tuning:

```
Profit = DiscountRevenue          (category-tiered merchant discount rates)
       + RevolveInterestIncome    (net yield on revolving balance)
       + AnnualFee                (rank-neutral constant)
       - RewardPointLiability     (accrual basis, per-point issuer cost)
       - BenefitUtilizationCost   (cab, entertainment, commerce and lifestyle credits)
       - ExpectedCreditLoss       (LGD x RiskScore x Exposure)
       - ServicingPenalties       (cancellation & collection calls, flat servicing cost)
```

Implemented as a fully **vectorized** NumPy/pandas computation over all 500K records.

| Component | Form | Rationale |
|---|---|---|
| Discount revenue | Category-tiered rates, 2.2%–2.6% of spend | Premium-card MDR band |
| Revolve interest | 24% annual yield on revolving balance | Revolving APR net of funding cost |
| Annual fee | Flat constant | Premier fee is uniform, so rank-neutral |
| Reward liability | Per-point issuer cost × points earned, with a 5x multiplier on the bonus category | Accrual basis, not redemption basis |
| Benefit cost | Utilized lifestyle and travel credits | Statement credits are a direct cost |
| Expected credit loss | `LGD × RiskScore × (Balance + 15% of spend)` | Charge card exposure includes in-cycle spend |
| Servicing penalties | Weighted cancellation and collection call counts, plus flat servicing | Engagement signals as cost drivers |

**Feature usage.** All available attributes are ingested and imputed (zero-fill for spend and count fields, median for the risk score). **13 attributes carry non-zero weight in the final equation** — the remainder were either tested and found rank-neutral, or had no direct P&L line that could be calibrated within the submission budget.

### 2. Label-free calibration loop

With no validation set possible, every leaderboard submission is treated as a scarce experiment:

- **One variable per submission.** Strict coordinate descent; bundled changes are uninterpretable.
- **Flip-fraction pre-screening.** Before spending a submission, a local diagnostic computes what fraction of members a candidate change moves across the top-20% boundary. Changes flipping <0.4% of members cannot move the score enough to justify the cost and are skipped.
- **Directional probing.** When a coefficient shows a gradient, follow it to convergence, then lock it.

Roughly 20 submissions were used out of the 50 permitted — the constraint was self-imposed, not the rulebook.

### 3. Pipeline integrity engineering

Mid-competition, scores stopped responding to code changes. Root cause: a stale output artifact was being re-uploaded while edits ran elsewhere, silently corrupting score-to-config attribution. The fix became part of the methodology:

- Config-stamped, timestamped output filenames (no fixed-name overwrites)
- MD5 fingerprint of the prediction vector printed on every run and logged next to every leaderboard score
- A rebuilt experiment ledger pairing each score with a verifiable artifact hash

### 4. Continuous output, not a binary flag

The submission exports the exact estimated profit per cardmember rather than a self-imposed 0/1 cutoff. Since the grader takes the top 20% by the submitted value, exporting continuous profit preserves the full rank ordering instead of discarding information at an arbitrary threshold.

---

## Results

| Milestone | Public leaderboard accuracy |
|---|---|
| First-principles economic baseline | 0.841 |
| Reward / discount-rate recalibration | 0.855 |
| Validated stable baseline | 0.890 |
| Over-weighted revenue term pruned (leaderboard-driven) | 0.899 |
| Servicing-penalty & revolve-yield tuning | **0.901** |

Along the way, **6 structural hypotheses were tested and falsified** at roughly one submission each — non-linear risk transformations, redemption-based (vs. accrual) reward costing, per-card fee scaling, welcome-bonus terms, and alternative spend bases — each rejection narrowing the inferred functional form of the hidden target.

> Scores above are from the **public leaderboard** (70% of records). The private leaderboard on the remaining 30% is scored separately.

### Two findings that fall out of the equation

**The bonus category is the thinnest-margin spend.** At a 5x reward multiplier, the accrued point liability consumes roughly 58% of the discount revenue that category generates — leaving a net contribution margin about half that of ordinary 1x spend. The highest merchant-discount-rate category is not the most profitable one.

**The model implies a break-even risk score.** Setting revolve yield equal to expected credit loss on the same balance gives a risk-score threshold of ≈0.32. Below it, a revolving balance creates value; above it, expected loss exceeds interest income and the balance is value-destructive.

### Key lessons

1. **Negative results are purchases, not failures.** Every falsified hypothesis constrained the target's structure; the winning configuration was found largely by elimination.
2. **The metric defines the problem.** Only boundary flips matter under set-overlap accuracy — rank-neutral "realism improvements" are wasted submissions.
3. **Masked features are not what they seem.** One feature that looked like total spend proved numerically incompatible with dollar-scale spend (likely transformed or scaled), decisively falsified by a single controlled test.
4. **Artifact integrity is a modeling problem.** An hour of fingerprinting infrastructure is cheaper than three misattributed submissions.

---

## Repository Contents

```
.
├── profitability_engine.py            # P&L equation + submission generator (vectorized)
├── amex_challenge_r1_submission.xlsx  # Final Round 1 submission (Predictions + Framework tabs)
├── problem_statement.pdf              # Official Round 1 problem statement
└── README.md
```

> **Note:** Competition data is not included in this repository per challenge terms. The script expects the official Round 1 dataset CSV in the working directory.

## Running

```bash
pip install pandas numpy openpyxl
python profitability_engine.py
```

The script imputes missing values, applies business caps to benefit-utilization fields, computes the P&L, and writes a two-tab submission workbook.

## Stack

`Python` · `pandas` · `NumPy` · `openpyxl`

---

*Built solo for the American Express Campus Challenge 2026, Round 1.*
