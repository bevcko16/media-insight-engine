# Third-party notices

This skill contains **no code, prompt text or documentation copied** from the repositories below.
All code and text were written for this project. The repositories were studied, and some ideas
and methodological concepts were adopted or adapted, as described in
`docs/reference-repo-evaluation.md`. Ideas and methods are acknowledged here as a matter of
attribution and good practice.

| Project | Licence | Use in this skill |
|---|---|---|
| LangChain Paid Media Agent, https://github.com/langchain-ai/paid-media-agent | Apache License 2.0 | Concepts: derive ratios from summed base metrics; missing data is not zero; equal-length comparison windows; observation / explanation / hypothesis separation; benchmark discipline |
| Dataslayer Marketing Skills, https://github.com/Dataslayer-AI/Marketing-skills (© 2026 Dataslayer S.L.) | MIT | Concepts: analyst-persona diagnosis steps; tracking and conversion-definition sanity checks |
| Data Prospector, https://github.com/FrancisCrickInstitute/Data-Prospector (Francis Crick Institute) | GNU GPL v3.0 | Concepts only: diverge-then-judge angle generation across stances; independent insight and soundness judgements with a three-way soundness verdict; not trusting self-assessed novelty; reporting refuted ideas. No GPL code or prompts are included, so the GPL does not apply to this skill |
| rampstackco claude-skills, ads-performance-analytics, https://github.com/rampstackco/claude-skills (© 2026 RampStack Co.) | MIT | Concepts: catalogue of interpretation failures; attribution and reconciliation discipline |

Data Prospector's design in turn cites Anthropic's "Building effective agents" (Schluntz & Zhang,
2024).

## Runtime dependencies

| Package | Licence |
|---|---|
| pandas | BSD-3-Clause |
| openpyxl | MIT |
| numpy (pandas dependency) | BSD-3-Clause |

Platform names (Meta, TikTok, Pinterest, Google, YouTube, DV360, LinkedIn) are trademarks of their
owners and are used only descriptively.
