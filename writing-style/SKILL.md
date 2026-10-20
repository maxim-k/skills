---
name: writing-style
description: >
  Writing rules for documentation prose, drawn from the Google developer
  documentation style guide: prescriptive voice, tone, plain language for a
  global audience, jargon, accessible prose, headings, lists, procedures, and
  code samples. Apply them whenever you draft or edit prose for people to read —
  README, docs page, guide, tutorial, quickstart, how-to, design doc, runbook,
  release notes — and review existing prose against them when the user says
  "review my writing", "improve this prose", "make this clearer", "fix the
  tone", "is this well written", "style guide", "clean up these
  LLM-generated docs", or pastes a paragraph and asks what is wrong with it. Covers the judgment calls a linter cannot make; Vale
  (vale-google-style) handles the mechanical ones. Not for text inside Python
  source (python-style) or commit messages (conventional-commit).
---

These rules come from nine pages of the
[Google developer documentation style guide](https://developers.google.com/style):
accessibility, translation, jargon, prescriptive documentation, tone, headings,
lists, procedures, and code samples. They serve one reader: someone in a
hurry, possibly reading in a second language or through a screen reader, who
wants to finish a task. Every rule below is a way to waste less of that
reader's attention.

They are guidelines, not a checklist to apply at full weight. If a rule makes
a passage harder to read, leave the passage and say why. A forced fix is a
worse defect than the one it removes.

## Know the reader first

The Google guide is written for public product documentation, read by
strangers. Before applying a rule, name who reads this document and what they
already know; the document often says so, and its type tells you the rest.

- **Public docs** (README of a published tool, user guide, tutorial): apply
  the rules at full weight.
- **Internal engineering docs** (design doc, known-issues list, runbook,
  architecture notes, a lab's pipeline docs): the readers share the domain
  vocabulary and the codebase. Don't expand abbreviations they use daily
  (WGS, TMB, PR, CI). Code in a heading is right when the heading names a code
  defect ("`msisensor.py` raises `UnboundLocalError`"). Numbers in an issue
  list's headings are identifiers, not ordering — keep them.
- **Mixed audience** (a page that names clinicians *and* developers as
  readers): write for the least specialized reader the page names.

When a rule exists to serve a reader the document doesn't have, skip it
silently. Don't list it under "Left alone" either.

## Division of labor with Vale

`vale-google-style` lints every Markdown file after it is written. It catches
what a regex can: word swaps, Oxford commas, exclamation marks, sentence-case
headings, trailing heading periods, "will", Latin abbreviations, first person,
passive voice, date formats, ellipses, and similar. **Don't restate those
rules here and don't spend review findings on them** — Vale reports them
anyway. This skill covers the structural and semantic rules no regex can
check.

One conflict: the Google guide says to write "We recommend …", but Vale's
`We.yml` and `FirstPerson.yml` are at `warning` level here and the hook blocks
that phrasing. State a recommendation as a plain imperative ("Use X"), or as
"The recommended way is X" when the recommendation itself needs marking.

## Two modes

- **Drafting.** When you write prose, apply the rules as you write. Don't
  report them; the output is the report.
- **Review.** When the user asks you to review, check, or improve prose, work
  in the passes in [Review](#review) and use its output format.

## Prescriptive voice

Readers come to documentation to learn what to do, not to survey what is
possible.

- **Recommend one way.** Give one method for a task — the one that works for
  the most readers, is shortest, and needs only a keyboard where possible. Put
  alternatives on their own page, section, or tab. A list of equal options
  hands the decision back to the reader who came to have it made.
- **Base examples on the most likely case.** Show the commands and arguments
  that the common reader runs, not the full surface.
- **Give each document one purpose**, and make every heading serve it.
- **Match the verb to the obligation.**
  - Required: a plain imperative, or "must".
  - Optional: "can".
  - Possible outcome: "might".
  - Expected outcome: describe it in the present tense.
- **Avoid "should".** It blurs required and recommended, and translates
  badly. Use it only for a widely recognized practice.
  Recommended: "Ensure that the Classroom Share Button conforms to …"
  Not: "The Classroom Share Button should conform to …"
- **Don't write "should be" for a state.** Say who sets the value, or give the
  conditional step. Not: "The flag should be set to `true`." Recommended: "If
  the flag is `false`, set it to `true`."
- **Make clear who does each action.** If naming the actor needs a fact the
  text doesn't contain, that is a content gap: report it, don't invent it.

## Tone

Write like a knowledgeable friend explaining something to a colleague:
conversational and respectful, neither pushy nor pedantic, neither cute nor
dry.

- **Put the most important information first** — in the document, the
  section, and the paragraph.
- **Don't write exactly as you speak.** Speech is wordier and looser than
  good prose.
- **Don't say a task is easy.** Cut "simply", "just", "easy", "quickly",
  "it's that simple", "obviously". A reader who is struggling feels worse,
  and the word adds nothing for a reader who isn't.
- **Don't write "please" in instructions.** It makes an instruction sound
  optional and adds a word to every step.
  Recommended: "To view the document, click **View**."
  Not: "To view the document, please click **View**."
- **Cut filler**: "please note", "note that", "at this time", "it is
  important to", "basically", "actually".
- **No "let's"**, no cuteness, no humor, no pop-culture or regional
  references. Jokes don't survive translation and don't age.
- **Avoid figurative language** — metaphors, idioms, sports and war
  imagery, and ableist terms ("crazy", "cripple", "blind spot", "sanity
  check" where a plain word exists).
- **Vary sentence openings.** Don't start every sentence with "You can" or
  "To do this". Avoid both choppy runs of short sentences and long ones.
- **Use transitions sparingly.** Don't open every other sentence with
  "However" or "Additionally".

Tone, calibrated:
- Too informal: "Dude! This API is totally awesome!"
- Too formal: "The API documented by this page may enable the acquisition of
  information pertaining to user preferences."
- About right: "This API lets you collect data about what your users like."

## Plain language for a global audience

Many readers use machine translation or read English as a second language.
These rules make a sentence parse one way. **Use them on a sentence that can
be read two ways, or that a reader has to read twice.** A sentence that
already parses one way stays as it is: adding "that", "then", or a noun
before every keyword to a clear sentence makes it stiffer, not clearer, and
"it" is fine when only one thing could be meant.

- **Address the reader as "you".** Use "the user" only for the reader's own
  end users.
- **Keep sentences under about 26 words**, in subject-verb-object order, with
  the subject and verb early.
- **Put a condition before the instruction.** "If X, do Y", not "Do Y if X."
- **Use the simple word.** "use", not "utilize" or "leverage"; "start", not
  "commence"; "so", not "consequently"; "some" or "many", not "a number of".
- **Avoid phrasal verbs** where a single verb exists: "use", not "make use
  of"; "remove", not "get rid of". Common ones (set up, log in, sign in) are
  fine.
- **Use each word in one sense.** Watch "once" (one time vs. after), "since"
  (because vs. after), "while" (although vs. during), "as" (because vs.
  when). Don't use the same word as a noun and a verb close together.
- **Keep the helper words that translation tools need**: "that", "then",
  "of", and relative pronouns.
  Recommended: "If the attribute key is not found, then the default value is
  returned." / "Update the rules that you defined."
  Not: "If the attribute key is not found, the default value is returned." /
  "Update the rules you defined."
- **Repeat a word when it removes ambiguity.**
  Recommended: "If the VM has started and if you're able to connect …"
- **Don't stack more than two nouns before a noun.** Unstack with
  prepositions. Recommended: "A cloud-native DevSecOps pipeline in a hybrid
  environment." Not: "A hybrid cloud-native DevSecOps pipeline."
- **Put "only" immediately before what it limits.**
  Recommended: "Request no more than one token." Not: "Only request one
  token."
- **Replace an ambiguous pronoun with its noun.** If "it", "this", or "they"
  could point at two things, name the thing.
  Recommended: "… make sure that the ad is targeted."
  Not: "… make sure that it's targeted."
- **Avoid bare gerunds and participles.** Write "by using", "that uses", or
  "you use".
  Recommended: "This guide describes how to set up database replication."
  Not: "This guide describes setting up database replication."
- **Add a noun to a technical keyword**: "the `example.yaml` file", "the
  `--force` flag", "the `get` method".
- **Say what the reader can do**, not what they can't. Avoid double negatives
  and exceptions to exceptions.
  Recommended: "You can continue without a path."
  Not: "A missing path won't prevent you from continuing."
- **Use one term per concept**, with one capitalization, throughout. Synonyms
  make a reader wonder whether two things differ.
- **Don't form plurals with 's**, and don't make product names plural or
  possessive.
- **Give context; don't assume prior knowledge** the page hasn't given or
  linked.
- **Use diverse, culturally neutral example names**, and no holidays, seasons,
  or sports.

## Jargon

Jargon is a term only an in-group knows. It excludes everyone else and often
doesn't translate.

- **Write around the term if you can.**
  "Review what processes worked or didn't work", not "hold a post-mortem";
  "use an informal design process", not "back-of-the-envelope design".
- **Use a more specific word**: "affected area", not "blast radius";
  "import" or "load", not "ingest"; "ready-made", not "off-the-shelf".
- **If the term must stay** (the reader will meet it elsewhere, or searches
  for it):
  - Used once: describe it in plain words and put the term in parentheses.
    Recommended: "… to an earlier part of the process (also known as
    _shifting left_)."
  - Used throughout: define it in parentheses at first mention, or link to a
    trusted definition.
    Recommended: "… the same state as a _cold standby_ (a backup system that
    is not running until needed)."
- **A term from code** names only that code item, in code font.
  Recommended: "Add a user to the allowlist (`whitelist`) by entering …"
  Not: "Add a user to the whitelist by entering …"
- **Spell out an abbreviation on first use**, and again if it appears rarely.

## Accessible prose

The guide's accessibility page also covers site implementation (ARIA, CSS
contrast, DOM order, keyboard focus). Those belong to whoever builds the page;
the rules below are the ones a writer controls.

- **Write link text that makes sense out of context.** A screen reader can
  list every link on a page; "click here" and "this document" say nothing in
  that list. Introduce cross-references with "see".
  Recommended: "For details, see [Configure the cache](…)."
  Not: "For details, [click here](…)."
- **Don't rely on position, color, or shape alone.** Use "earlier",
  "preceding", or "following", not "above", "below", "left", or "right".
  Refer to a UI element by its label, not its icon.
  Recommended: "In the preceding diagram …" / "Click **Notifications**."
  Not: "In the diagram above …" / "Click the bell icon."
- **Give every image alt text that states its purpose**, and put any new
  information from an image in the text too. Never use an image of text, code,
  or terminal output.
- **Break up dense text** with paragraphs, headings, lists, and tables. Put
  the key point in a paragraph's first sentence.
- **Use parallel structure** for items that do the same job — list items,
  steps, table rows, headings at the same level.
- **Introduce every table** with a sentence before it. Don't use a table
  where a list will do, don't put one in the middle of a numbered procedure,
  and don't encode its information only in symbols.
- **Remove formatting that carries no meaning.** Bold marks the one thing a
  scanning reader must not miss; when every other phrase is bold, nothing is.
  A screen reader announces emoji by name and reads "→" as "right arrow".
  Cut decorative emoji, horizontal rules between sections that headings
  already separate, and bold used for emphasis rather than for UI labels or
  defined terms. Generated prose is especially prone to all of these — count
  them, and treat a high count as one structural finding, not many small ones.
- **Write words, not symbols, in prose.** "and", not "&" or "+"; "then" or a
  numbered list, not "→"; "and" or "or", not "/". Symbols are fine in a tight
  UI label, a table header, a diagram, or code.
- **Don't use a dash where a sentence break or a colon belongs.** A run of
  em dashes splices clauses that should be separate sentences.
- **Don't hard-wrap a sentence for display**, and don't use all caps or camel
  case for emphasis.

## Headings

- **Task headings start with a bare infinitive.**
  Recommended: "Create an instance". Not: "Creating an instance".
- **Concept headings are noun phrases** and don't open with "-ing".
  Recommended: "Migration to Google Cloud". Not: "Migrating to Google Cloud".
  A gerund with no alternative ("Billing", "Pricing") is fine, as is "-ing"
  later in the heading.
- **Mark an optional section with an "Optional:" prefix.**
  Recommended: "Optional: Customize your alias".
  Not: "Customize your alias (optional)".
- **Base the title on the document's purpose** and each heading on its
  section's content. Make headings descriptive and unique within the page.
- **Keep the hierarchy.** One `#` title per page, not repeated as a heading.
  Don't skip levels. Don't leave a heading empty: put an intro sentence
  between an `##` and its first `###`, using "The following sections …", not
  "This section" or "These sections".
- **No numbers, links, or code in headings.** If code is unavoidable, add a
  noun: "The `init` command".
- **Keep punctuation minimal.** A heading that needs much punctuation needs
  rewriting.
- **Use only well-known abbreviations in a heading**, and spell them out in
  the first paragraph after it.

## Lists

- **Choose the form by the content.** Numbered list when order matters;
  bulleted list when it doesn't; table when items have several properties;
  description list (or bold run-in headings) for terms and definitions. Never
  a list of one item.
- **Introduce a list with a complete sentence**, ending with a colon if the
  list follows directly, or a period if something comes between. Don't use a
  fragment that the items complete; use "the following".
  Recommended: "Use the **Submit** button for any of the following purposes:"
  Not: "Use the **Submit** button to:"
- **Make every item parallel** — same grammatical form, same kind of thing.
- **Capitalize the first word** of each item unless case carries meaning.
- **End each item with a period** if it is a sentence or contains a verb.
  Leave the period off single words, verb-less fragments, code, and link
  titles. If a list mixes the two, rewrite it so all items match.
- **For run-in headings, use a colon or a period, the same way throughout**,
  and a colon rather than a dash. After a colon, start lowercase.
  Recommended: "**Big**: a short word"
- **Don't end a list with "etc." or "and so on".** Signal in the intro that
  the list is not complete: "… such as the following:".
- **Say whether every bulleted item is required.**

## Procedures

- **Introduce the procedure with an imperative or a complete sentence**, not
  a fragment. Omit the intro if the heading says it all.
  Recommended: "To customize the buttons, follow these steps:"
  Not: "To customize the buttons:"
- **List prerequisites up front**: the hardware, software, access, and
  information the reader needs before step 1.
- **One action per step**, each starting with an imperative verb. Combine a
  menu path into one action: "Click **File > New > Document**."
  Recommended: "Clone the repository that contains the sample data."
  Not: "You need the project ID later in this document. Retrieve the project
  ID."
- **A one-step procedure is one sentence**, not a numbered list of one.
- **Order within a step: where, why, what, then the result.**
  - Location first: "In Cloud Shell, …", "In Google Docs, click …".
  - Goal before action: "To start a new document, click …". If "To …" makes
    the step sound optional, use a colon: "Start a new document: click …".
  - Action, then result, in one paragraph: "Click **Run**. The query results
    appear after the query runs."
  - Justification after the action: "Store the private key in a secure
    location. You need it later."
- **Start an optional step with "Optional:"**, not "(Optional)".
- **Name the tool or environment** each procedure runs in, and restate it when
  a procedure splits.
- **Say what a command does instead of "Run the following command".**
  Recommended: "In Cloud Shell, deploy the load generator:"
  Not: "Run the following command:"
- **Include pressing Enter** when the step needs it. Don't give keyboard
  shortcuts as the only path.
- **Link to a repeated procedure** instead of copying it.
- **Label sub-steps a, b, c**, then i, ii, iii.
- **Minimize steps and interruptions.** One decision for the reader per step.

## Code samples

- **Introduce each sample with a sentence about the sample**, ending with a
  colon if the code follows directly.
  Recommended: "The following code sample shows how to use the `get`
  method:"
  Not: "… For information about other methods, see [link]:"
- **Mark omitted code with a comment in the sample's language**, never `...`
  or `…` — a reader who copies the block gets a syntax error.
  Recommended: `# Several lines of code are omitted here.`
- **Indent with spaces**, two per level unless the language's style guide says
  otherwise. Wrap at 80 characters.
- **Follow the language's own style guide** inside the sample.

## Review

The rules in this skill are about wording, but wording is the cheapest thing
to get wrong. A reader who follows a false statement loses more than one who
rereads a long sentence. Review in three passes, in this order, and don't let
the third crowd out the first.

1. **Accuracy.** Does the text say anything false, or contradict itself?
   - A claim that the document's own evidence disproves ("bit-identical",
     then a section showing the files differ), or an absolute claim resting
     on one case.
   - A promise the document doesn't keep ("each entry gives the
     reproduction" when none does).
   - Prose that disagrees with the code, command, table, or diagram next to
     it: a proposed fix that doesn't do what its description says, a command
     that can't run from the directory the text names, "two dependencies"
     above a diagram with three.
   - Links and paths that don't resolve, when you can check them.
2. **Structure and purpose.** Does the document serve one reader with one
   purpose, in the order that reader needs?
   - History or maintainer notes in a user-facing page; the same fact in
     several places, especially when the copies disagree.
   - Siblings that should share a shape and don't (entries with missing
     fields, procedures without prerequisites).
   - The consequence buried after the mechanism; the most important
     information last.
   - Formatting that carries no meaning, counted (see
     [Accessible prose](#accessible-prose)).
3. **Wording.** The rule sections of this skill, filtered through
   [Know the reader first](#know-the-reader-first).

### Review output

Write the review in three parts, in this order.

1. **Findings**, under three headings: Accuracy, Structure, Wording. Within
   each, order findings by how much they cost the reader, worst first. One
   line per finding:

   > "quoted passage" — rule broken → suggested fix

   Quote just enough to locate the passage. When the same rule fires more than
   twice, give it one line with a count and the worst example. Keep Wording to
   about fifteen lines; past that, list the remaining rules with counts only.
   Skip anything Vale reports (see
   [Division of labor](#division-of-labor-with-vale)).
2. **Revised text**, with every finding applied. Keep the author's meaning,
   facts, and structure unless a finding is about structure. For a document
   longer than about 200 lines, revise only the sections that have findings
   and name the sections you left as they were. If the prose is in a file,
   write the revision to that file only when the user asks.
3. **Left alone**, one line each:
   - Text you deliberately didn't touch: code blocks, inline code, quotations,
     and examples of what *not* to write.
   - Findings whose fix needs a fact the text doesn't contain — a missing
     actor, an unstated prerequisite, an unnamed recommended option. Name the
     missing fact; don't invent it.
   - Rules you chose not to apply because the fix would read worse, with the
     reason.

If the prose has no findings, say so in one line. Don't invent findings to
fill the format.
