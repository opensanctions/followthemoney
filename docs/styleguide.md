# Documentation Style Guide

This guide defines the voice, word choices, and formatting conventions for documentation across the FollowTheMoney (FtM) stack: `followthemoney`, `rigour`, `nomenklatura`, `zavod`, and `yente`. It applies to prose on the docs sites of each project, and to README files where they exceed a stub.

The scope is deliberately narrow. The guide covers how to write, not how to organize sites or operate the doc process. Each repo keeps its own conventions for page structure, versioning, and PR review. When projects disagree on a rule here, document the deviation in that project's contributor guide.

A reference like [Diátaxis](https://diataxis.fr/) is a useful lens for deciding what belongs on a page — distinguishing tutorials, how-to guides, reference material, and explanations — but this guide does not mandate its structure.

Write for a **fairly technical audience**: developers integrating these libraries into a product, data engineers running pipelines, investigators and analysts using the CLI or an HTTP API, researchers working with FtM-format data. They're comfortable on a command line and can read a code example, but not all of them write Python daily or have deep software-engineering backgrounds.

Do not assume Python fluency in prose outside of Python API reference. In tutorials and how-to content, explain what a code example does before showing it, and keep examples small enough to be transcribed rather than deeply understood. Reserve deeper software-engineering vocabulary (generators, `__slots__`, async, typing nuances) for reference and contributor docs where the audience is narrower.

---

## Voice

### No first-person "we"

Do not use "we", "our", or "us" in documentation. The stack has multiple maintainers across multiple repos with outside contributors, and "we" introduces ambiguity that readers reasonably stumble on.

Use one of three alternatives, depending on who or what is acting:

- **The reader is acting** — address them directly with "you" and imperatives.
- **The software is acting** — name the system explicitly ("the parser", "`EntityProxy.add()`", "the API").
- **Nobody specific is acting** — use the imperative or passive construction.

<!-- styleguide-examples -->

- **Correct:** "Use `ValueEntity` for new code."
- **Correct:** "The parser raises `InvalidData` on malformed input."
- **Correct:** "You can filter entities by schema."
- **Wrong:** "We recommend `ValueEntity` for new code."
- **Wrong:** "We'll parse the input and raise on errors."

This applies to tutorials and walkthroughs too. "We'll install the dependencies" becomes "Install the dependencies." The loss of companionship is small; the gain in consistency is large.

### Signaling authority

Without "we recommend", you need clear conventions for signaling how strong a piece of guidance is. Use this ladder:

- **Bare imperative** — a hard rule or default. "Use absolute imports."
- **"Prefer X over Y"** — a softer preference where the alternative is sometimes appropriate. "Prefer generators over materializing lists for large datasets."
- **"Consider X"** — the weakest form, for contexts where the reader has to judge. "Consider `__slots__` when the class appears in hot loops."
- **"must" / "must not"** — reserved for genuine requirements (API contracts, stability guarantees). Do not inflate.

### Register

The target register sits between a well-written README and a senior engineer explaining something at a whiteboard. Direct, precise, and occasionally warm — but never cute, and never hedging for politeness.

- Use contractions ("don't", "you'll", "it's") where they read naturally.
- Address the reader directly. Acknowledge choice where there is choice: "If you need all entities, stream from `store.iterate()`. For a one-off lookup, use `store.get()`."
- Explanations can be discursive when they earn it. When a design is counterintuitive, say so and walk through why — don't hide behind a terse reference tone that forces the reader to reconstruct your reasoning.
- Don't strain for informality. "Here's a fun trick" reads worse than the trick itself.
- Don't apologize. A known limitation is a known limitation, stated plainly, not "unfortunately we haven't yet..."

### Spelling

Use **American English**: "color", "normalize", "organization", "license", "analyze". This aligns with the wider OpenSanctions docs and is the common default for technical writing read globally.

Technical identifiers (schema names, field names, code symbols) preserve whatever spelling was used when they were defined. Do not change `Organization`, `normalise_name`, or similar identifiers to match prose.

### Word precision

**can / may / might** are not interchangeable:

- **can** — the system or the reader is able to do something. "You can filter by schema."
- **may** — something is permitted, or it is possible. "An entity may have multiple names."
- **might** — a weaker possibility, usually in explanatory prose. "Deduplication might merge entities that are actually distinct."

Do not use "may" when you mean "can".

**will** — describe existing system behavior in the present tense, not the future: "the parser returns a list", not "the parser will return a list". Reserve "will" for a consequence the reader is choosing to trigger: "If you pass `cleaned=True`, `add()` will skip validation."

### Conditional instructions

Put the **condition before the action**. Readers who don't match the condition can skip the sentence immediately.

- **Correct:** "If you need all entities, set `limit=0`."
- **Wrong:** "Set `limit=0` if you need all entities."

### What to avoid

- **Marketing language** — "powerful", "blazing-fast", "seamless", "robust", "cutting-edge". Cut. These do not tell the reader anything verifiable.
- **Adjectives of difficulty** — "simply", "easily", "just", "straightforward", "obviously", "trivially". They assert that the reader should find the task easy, which is presumptuous and unhelpful when they don't.
- **Hedging without reason** — "may potentially", "could possibly", "in some cases" as filler. If a caveat is real, state it; if it isn't, drop it.
- **"Please"** in technical instructions. "Please pass the API key" → "Pass the API key". It adds no politeness and weakens directness.
- **Exclamation marks** in prose. Remove them.
- **"whitelist" / "blacklist"** — use "allowlist" / "denylist".
- **Throat-clearing intros** — "Before diving into the details, let's first consider..." Lead with the point.
- **Lecturing** — "It is crucial that you understand..." State the thing.

---

## Terminology

Use these terms consistently across all five projects. Consistency matters more than variety — do not reach for synonyms to avoid repetition.

| Use this | Not this |
|---|---|
| entity | record, item, object, row |
| schema | type, class, entity type |
| property | field, attribute, column (in FtM context) |
| property type | field type, datatype |
| dataset | source, feed, provider, data source |
| catalog | collection of datasets (when referring to a `DataCatalog`) |
| statement | claim, fact, assertion (in the statement-based model) |
| identifier | ID, id (except when naming the literal `id` field) |
| match / matching | compare, score, scoring (when the task is pairing two entities) |
| deduplication | de-duplication, dedup, de-dup |
| canonical ID | master ID, resolved ID |
| territory | country (prefer in new writing; see below) |
| jurisdiction | territory (when referring specifically to a rule-making entity) |
| crawler | scraper, harvester, importer (in zavod context) |
| FollowTheMoney / FtM | followthemoney, ftm (in prose) |
| yente | Yente, YENTE |
| rigour, nomenklatura, zavod | capitalized forms in prose |

**Territory, jurisdiction, country** are not synonyms. **Territory** is the broadest — political geographies including dependencies, disputed areas, and non-UN entities (Hong Kong, Kosovo). **Jurisdiction** is narrower: a territory with rule-making authority relevant to incorporation or legal accountability. **Country** refers to UN member states. Prefer "territory" in new writing; use the more specific terms when precision matters.

**FollowTheMoney** is written in full on first use per page, with "(FtM)" after it if the abbreviation is used later. Subsequent mentions can use "FtM".

**yente** is always lowercase. It is a product name, not a common noun.

**Package and module names** — `followthemoney`, `rigour`, `nomenklatura`, `zavod` — are lowercase in code and in backticks. In running prose, the capitalized project names (FollowTheMoney, Rigour, Nomenklatura, Zavod) are acceptable, but lowercase is also fine. Pick one convention per page.

**Schema and property names** are always rendered in backticks: `Person`, `Organization`, `birthDate`, `weakAlias`. Do not put the generic words "schema" or "property" in backticks unless you are naming a specific one.

### Cross-project references

When prose in one project mentions a concept defined in another, link to the upstream definition on first use per page. Don't redefine the concept unless the downstream project genuinely refines its meaning — in which case, link out and then explain the refinement.

---

## Page conventions

### Summary sentence

Every documentation page should open with a one-sentence summary: 15–25 words, written as if the page URL is not visible, describing what the reader will be able to do or understand. It is used in search results and link previews.

- Do not use "this page" or "below".
- Do not repeat the page title.
- Do not defer — "This page explains X" → "X is…".

**Correct:** "An entity is a JSON-shaped record with a `schema`, an `id`, and a set of multi-valued string properties."
**Wrong:** "Below is an explanation of the entity data model."

### Context paragraph

Follow the summary with a brief paragraph on why this matters, or when to reach for this. Skip it when the title plus summary are enough.

### Recommendations lead the section

When a section's main point is a recommendation, lead with it. Do not walk the reader through four paragraphs of context before stating what they should do.

- **Correct:** "**Use `ValueEntity` for new code.** It provides the same interface as the legacy `EntityProxy`, plus dataset and temporal metadata…"
- **Wrong:** Three paragraphs of history, then "…so, in most cases, `ValueEntity` is the right choice."

### Code examples after prose

Explain what the example does before showing it. Readers skip to code and skip back to prose; both should work, but the prose should set up the code, not the other way around.

---

## Formatting

### Headers

- `##` for main sections, `###` for sub-sections.
- No `#` (h1) in body content — the page title provides that.
- Sentence case: "Configuring the namespace", not "Configuring The Namespace".
- No punctuation at the end of headers.
- Prefer headers that state the conclusion or key fact, not just the topic. "Property values are always lists of strings" is better than "Property values". A reader scanning headers should learn the argument of the page, not just a table of contents.

### Emphasis

- **Bold** for the introduction of a defined term, or for the key action in a numbered step.
- *Italic* for titles of external systems or works. Use sparingly.
- Do not use bold for general emphasis. If something is important, restructure the sentence so it leads.

### Lists

- Use bullet lists for sets of items without a natural order.
- Use numbered lists only for actual sequences where order matters.
- Avoid lists of one item. Avoid lists where each item is a full paragraph — break those into sub-sections.
- When list items share parallel structure worth scanning, lead each with a **bolded noun or verb phrase**. Plain bullets are fine for shorter enumerations.
- Use the serial (Oxford) comma consistently: "a, b, and c".

### Numbers

Spell out numbers one through twelve in prose: "two datasets", "one exception". Use numerals for 13 and above: "142 orphan IDs".

Always use numerals in technical contexts where the number is a parameter, measurement, or value: "set `limit=5`", "a 6-month window", "100 results".

### Verb tense

Describe system behavior in **present tense**: the function returns, the parser raises, the API accepts.

- **Correct:** "The parser raises `InvalidData` on malformed input."
- **Wrong:** "The parser will raise `InvalidData` on malformed input."

Use future tense only when describing a consequence the reader is choosing to trigger: "If you pass `cleaned=True`, `add()` will skip validation."

### Code blocks

Every code block specifies a language: ` ```python `, ` ```yaml `, ` ```bash `, ` ```json `.

Placeholders — values the reader must substitute — use `ALL_CAPS` inside angle brackets:

```bash
ftm map <MAPPING_FILE> > entities.ijson
```

Introduce each placeholder in the surrounding prose: "Replace `<MAPPING_FILE>` with the path to your mapping YAML."

Do not use `your_mapping`, `xxx`, or `...` as placeholders.

**Python examples** in the stack should:

- Use real-looking values, not `"string"` or `"foo"`.
- Show imports at the top when they aren't obvious.
- Use explicit keyword arguments when they aid readability.
- Follow the project's docstring convention — don't reinvent one in examples.

### Tables

Use tables for reference data with three or more columns (property listings, flag descriptions, type codes). For two-column key-value pairs, a list usually reads better.

### Admonitions

Use admonitions sparingly. Overused callouts stop working. Pick from this small palette:

- `note` — side information that is not on the critical path but is worth knowing.
- `warning` — something that will silently produce wrong results, or will surprise an experienced reader.
- `danger` — data loss, security risk, or irreversible action. Reserve for genuine hazards.

Do not invent admonition types beyond these three. If the content doesn't fit, promote it into the prose or into a sub-section.

A short inline note in bold is often better than a dedicated admonition:

> **Note:** `cleaned=True` bypasses type validation.

### Images

- Alt text must describe the content and its purpose in under 125 characters.
- Do not start alt text with "Image of" or "Screenshot of" — just describe what matters.
- Use captions on the line below the image in plain markdown italic, not HTML:

```markdown
![Entity graph with three persons connected to one company via ownership edges](graph.png)
*Ownership graph derived from the Moldovan companies dataset.*
```

For purely decorative images, use `alt=""`.

### Internal links

Link on first use of any term that has its own page. Every technical concept defined elsewhere should be reachable with one click.

**Always use relative links** for internal pages: `/docs/identifiers/`, not `https://followthemoney.tech/docs/identifiers/`.

**Link text must describe the destination.** Never use "click here", "here", or "read more". The link text should make sense read aloud in isolation — screen readers and search engines index it independently.

- **Correct:** "See the [matching guide](/docs/matching/) for scoring details."
- **Wrong:** "For scoring details, [click here](/docs/matching/)."

Do not link the same destination more than twice on a single page.

### Emoji

Do not use emoji in documentation prose. They are acceptable in release notes, changelogs, and social media posts where they serve a clear signaling purpose.

---

## Reviewing AI-assisted drafts

AI-generated writing has recognizable patterns that flatten prose and reduce precision. When reviewing a draft produced with AI assistance — whether your own or from a contributor — check for the following. This list is adapted from observable patterns in current LLM output (Wikipedia's [signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) is a useful longer reference).

### Sentence-level

- **Em-dash interjections** — mid-sentence asides set off by em-dashes that could be a separate sentence or cut entirely. "The parser — which runs at ingestion time — rejects malformed input" → split or rewrite.
- **"Not just X, but Y"** — artificial attention-getters. Say Y if Y is the point.
- **Rule of three** — three parallel clauses where two would do. "The system is fast, reliable, and scalable" is almost always padding.
- **Uniform sentence length** — every sentence roughly the same length reads as machine-produced. Introduce a short sentence for emphasis.

### Vocabulary

- **Fluffy verbs and adjectives** — *delve*, *underscore* (figurative), *harness*, *leverage* (verb), *nuanced*, *multifaceted*, *transformative*, *pivotal*, *intricate*, *testament*. Replace with the specific verb or adjective you mean, or cut.
- **Avoidance of "is/are"** — "serves as", "stands as", "marks a" where a plain copula would do. Usually a hallmark of summarizing rather than writing.
- **Hollow transitions** — *Furthermore*, *Moreover*, *Additionally*, *In conclusion* used to simulate flow. Cut or earn them. Also: "It is worth noting that", "It is important to note that".
- **Empty adverbs** — *simply*, *effectively*, *carefully*, *seamlessly*, *easily*, *quickly*. Cut or make the claim specific.

### Reference and rhetoric

- **Vague demonstratives** — "this approach", "these methods", "this solution" with no named antecedent. Force the rewrite: *which* approach?
- **Both-sides neutrality** — "While some prefer X, others prefer Y" with no recommendation. Technical documentation needs a position.
- **Restated conclusions** — a closing paragraph summarizing what was just said without adding anything. Cut it.
- **Fluent-sounding gaps** — sentences that read confidently but skip the reasoning. Ask: does this sentence explain *why*, or does it just assert?
- **Formulaic openers** — "From X to Y, ...", "Whether you are X or Y, ...", "In today's [landscape], ...". These delay the point. Start with the point.

### Formatting

- **Over-bulleting** — bullet lists where a sentence would do. Lists are for parallel, enumerable things, not for breaking up any content with more than one idea.
- **Decorative bolding** — bold text scattered through paragraphs to simulate structure. If everything is emphasized, nothing is.
- **Title case in headings** — the stack uses sentence case. Watch for "Configuring The Parser" creeping in.
- **Curly quotes** — typographic quotes (""") and apostrophes inside code-adjacent prose. Use straight quotes consistently.
- **Excessive admonitions** — if half the page is `!!! note` blocks, the drafter used callouts to structure the content. Promote into prose.

---

## Contributions and disagreements

This guide is a working document. Where it is silent or the rule is wrong for a specific case, use judgment and prefer clarity over conformance. Propose changes by opening a PR against this file.

Where a project's existing docs disagree with this guide, alignment happens incrementally — fix what the current PR touches, open issues for the rest. Do not open sweeping style-cleanup PRs across the stack unless coordinated with the maintainers of each affected project.
