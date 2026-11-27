# Writing guidelines

## The standard

Write as a senior strategist writing for a marketing director who has already seen the table.
They do not need the numbers read back to them. They need to know what the numbers mean together,
for their objective, and what (if anything) to do about it.

## Principles

- **Lead with the meaning, support with the number.** Numbers belong inside the argument, not as
  the argument.
- **One idea per paragraph.** Typically 50 to 110 words.
- **Specific nouns, active verbs.** "YouTube bought fewer impressions than planned because its CPM
  ran 36% above plan" not "There were some delivery challenges on YouTube".
- **Name the mechanism when the evidence supports it; hedge when it does not.**
- **Vary structure.** Some paragraphs end with an implication, some with a question, some simply
  explain. Do not end every one with "we recommend".
- **No forced narrative.** Inconclusive is a finding. Underperformance is stated plainly and
  without blame language.
- **British English** (optimise, behaviour, programme, centre, analyse, colour, labelled).
- **No em dashes or en dashes as punctuation.** Use commas, colons, full stops or brackets.

## Do not write

- Adjectives instead of analysis: strong, impressive, excellent, efficient, successful, solid.
- Filler: "This highlights the importance of", "This underscores the need for", "In today's
  competitive digital landscape", "This demonstrates the power of", "Moving forward, it is
  essential to", "These results showcase the effectiveness of", "It is worth noting that",
  "a testament to", "unlock potential", "holistic", "seamless", "delve", "leverage the power".
- Psychology: "attention spans", "consumers prefer", "the audience loved", "resonated".
- Unhedged causality: "drove", "caused", "led to", "resulted in", "thanks to", "due to" unless a
  controlled test supports it.
- Table restatements: "Meta delivered the highest CTR at 1.24%."

## Patterns that work (do not copy the sentences)

- **Tension:** two things that should move together and did not, and what that says about roles.
- **Hidden mix:** an aggregate that is really a statement about composition.
- **Price vs volume:** why a shortfall happened, which tells you who can fix it.
- **Marginal vs average:** what the last pound bought, not the average pound.
- **Role clarity:** what each platform or asset contributes to the system.
- **The disproved assumption:** what the client probably believes that the data does not support.

## Rewriting examples

Observation: "TikTok generated strong engagement."
Better: "TikTok produced 71% of all engagements on 30% of the budget, yet its link CTR was
below both Meta's and Pinterest's. On this evidence, engagement on TikTok is a measure of how well the
content works inside the feed, not of intent to visit the site, so it should not be read across
as a consideration signal."
(Numbers here would each be listed as claims and verified.)

## Turkish

When asked for Turkish, write it natively for a Turkish marketing audience; do not translate
English sentence structures literally.

- Use established Turkish industry usage. Common English terms are normally kept (CTR, CPM, reach
  or "erişim", frequency or "frekans", "gösterim", "tıklama", "izlenme tamamlama oranı").
  Follow the client's terminology file if present.
- Prefer clear, formal but not bureaucratic register ("-mektedir" chains sparingly).
- Avoid filler equivalents: "önemini vurgulamaktadır", "altını çizmektedir", "günümüzün rekabetçi
  dijital dünyasında", "gücünü göstermektedir".
- Hedging: "işaret ediyor", "düşündürüyor", "olabilir", "muhtemel"; association: "ile birlikte",
  "eşlik etti" rather than "neden oldu".
- Decimal separator: Turkish convention uses a comma (%1,24). Pass `"language": "tr"` to the
  validator; when using commas as decimals, also give the claim values so the validator can match.
  If a client prefers dots, follow the client.
- No em dashes.
