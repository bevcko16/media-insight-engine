# Output modes

Default: **Client-Ready Insights**. Switch when the user asks ("deep dive", "exec summary",
"show your workings", "what should we do next"). Several modes can be combined.

## 1. Client-Ready Insights (default)

- 2 to 6 insights is typical; fewer is fine; zero is acceptable with an honest explanation.
- Each: an optional short bold headline (a finding, not a label) and one paragraph of 50 to 110
  words.
- Ordered by strategic importance to the objective.
- No scores, tiers, logs, rejected hypotheses or script names. Uncertainty shows in the wording.
- If an important caveat applies to the whole set (definitions differ, data partial), one short
  note at the end.
- Data-governance problems the client should know about (embedded instructions in a source file,
  duplicated or cumulative exports, mixed currencies) go in that note too, in plain language.

## 2. Deep Diagnostic Analysis

For the analyst or the agency team.
- Data scope and quality (from Stage A): grain, period, issues and how they were handled.
- Findings by theme (delivery, cost, attention, action, creative, allocation), each with the
  supporting table (from `metric_calculation.py`), the competing interpretations and which the
  evidence favours.
- Limitations and what further data would change the view.
- Optimisation opportunities, marked as evidence-backed or as tests.

## 3. Executive Summary

- 3 to 5 bullets or a 120 to 180 word paragraph.
- What happened against the objective, the one or two things that matter most, and the decision
  or question for the reader.
- No metric soup. At most one or two numbers per point.

## 4. Evidence and Validation Report

An audit trail. For each insight:
- Source file, sheet and the rows or filters used.
- Every claim: metric, filters, stated value, recomputed value, status (from the validator output).
- Comparison method (weighted, mix-adjusted, within-stratum, etc.).
- Evidence tier and confidence.
- Alternatives considered and why they were ruled out or remain open.
- Limitations.
Then:
- **Rejected hypotheses**: each with the reason (refuted, noise, insufficient volume,
  definition mismatch, hard gate failed).
- Data-quality issues and how they were handled.

## 5. Recommendations and Next Steps

A table or numbered list, each item with:
- The action and its scope.
- Basis: **evidence-backed** (existing data supports it) or **test** (a hypothesis to validate).
- For tests: design (split, holdout, sequential), success metric, minimum duration or volume.
- Expected direction of impact, confidence (high/medium/low) and feasibility (high/medium/low).
- Priority = impact × confidence × feasibility, highest first.

Do not recommend budget moves on the basis of a hypothesis. Recommend the test.
