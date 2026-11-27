# media-insight-engine

A Claude Agent Skill for paid media performance analysis that behaves like a sceptical senior media
analyst: it validates the data, computes every number deterministically, generates and tests
hypotheses, interprets results against the campaign's objective, and passes every insight through
a critical review and an automated evidence gate before anything reaches a client.

Core principle: **an observation is not an insight.**

## What is in the box

```
media-insight-engine/
├── SKILL.md                      entry point: rules, workflow, when to read what
├── references/                   loaded on demand (progressive disclosure)
│   ├── analytical-methodology.md     stages, arithmetic rules, valid comparisons, statistics limits
│   ├── hypothesis-generation.md      diverge, judge, test, keep refuted ideas
│   ├── media-strategy.md             roles, auction and optimisation mechanics, tensions
│   ├── campaign-objectives.md        KPI frames: awareness, video, consideration, conversion; luxury, FMCG
│   ├── platform-specific-analysis.md Meta, TikTok, Pinterest, YouTube, Google, DV360, LinkedIn
│   ├── metric-definitions.md         formulas used and traps
│   ├── critical-review.md            reviewer checklist, evidence tiers, insights.json schema
│   ├── insight-quality-rubric.md     weighted rubric, hard gates, calibration
│   ├── writing-guidelines.md         British English and Turkish writing standards
│   ├── benchmarking-methodology.md   no invented benchmarks; contextual matching
│   └── output-modes.md               5 output modes
├── scripts/                      deterministic engine (Python, pandas + openpyxl only)
│   ├── mie_common.py                 loading, header detection, column mapping (EN/TR), weighted maths, stats
│   ├── data_validation.py            Stage A profile and data-quality issues
│   ├── metric_calculation.py         weighted segment tables, shares, Wilson intervals
│   ├── exploratory_analysis.py       Stage B candidate discovery (12 analysis types)
│   └── evidence_validation.py        Stage D gate: recompute claims, lint writing, rubric
├── templates/                    brand, campaign, reporting preferences, benchmark register, insight library
├── knowledge/                    your client-specific files (read at start, never written without consent)
├── examples/                     strong, weak and annotated examples, validated by the scripts
├── tests/                        14 synthetic scenarios + 40 unit tests
├── evals/                        baseline vs skill evaluation and results
├── docs/reference-repo-evaluation.md
├── THIRD_PARTY_NOTICES.md, LICENSE (MIT), requirements.txt
```

## Installation

Requirements: Python 3.10+ with `pandas` and `openpyxl` (`pip install -r requirements.txt`).

**Claude Code (personal skill)**
```bash
mkdir -p ~/.claude/skills && unzip media-insight-engine.skill -d ~/.claude/skills/
```
or copy the `media-insight-engine/` folder to `~/.claude/skills/` (or `.claude/skills/` inside a
project to share it with a team via git).

**Claude.ai / Claude Desktop**
Settings → Capabilities (or Customize) → Skills → Upload skill → choose `media-insight-engine.skill`
(it is a zip with the skill folder at its root; rename to `.zip` if your client asks for a zip).
Code execution must be enabled for the scripts to run.

**Check it works**
```bash
cd ~/.claude/skills/media-insight-engine && python3 -m unittest discover -s tests
```

## Usage

Upload or point to the file(s) and ask in plain language, for example:

- "Here's the Q3 awareness campaign export and the media plan. Give me the client-ready insights."
- "Deep diagnostic on this TikTok and Meta creative data, objective is video completion."
- "Executive summary for the CMO, plus recommendations and next steps."
- "Show me the evidence and validation report for these insights."
- "Check these draft insights I wrote against the data." (paste them)
- "Bu kampanya için Türkçe içgörü yaz."

Running the scripts directly:

```bash
python3 scripts/data_validation.py report.xlsx
python3 scripts/exploratory_analysis.py report.xlsx --sheet "Creative" --objective video
python3 scripts/metric_calculation.py report.xlsx --sheet "Creative" --by platform --by format
python3 scripts/evidence_validation.py report.xlsx insights.json --sheet "Creative"
```

## Making it yours

Copy templates into `knowledge/<client>/` and fill them in: objectives, platform roles,
benchmarks (with source and date), approved and rejected insights, feedback, terminology. The skill
reads them each time. That is how it improves without retraining.

## Design choices

- **One structured workflow, not multiple agents.** The critical review is a role switch plus a
  deterministic gate. In testing, the gate catches the failures that matter (wrong numbers,
  unbacked numbers, unhedged causality, table restatement) more reliably than a second free-text
  reviewer would.
- **Fixed, tested analyses rather than generated code.** Discovery uses twelve tested analysis types;
  the model adds its own angles on top and tests them with `metric_calculation.py`.
- **Local only.** No network calls, no APIs, no external services.

See `docs/reference-repo-evaluation.md` for what was adopted, adapted and rejected from the four
reference repositories, and `evals/EVALUATION.md` for test results and known limitations.
