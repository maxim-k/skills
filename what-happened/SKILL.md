---
name: what-happened
description: >
  Briefing standard for reporting problems to the project lead: a coherent
  story of what broke, why, what it costs and what decision it needs, without
  line-level code detail. Use whenever you report a problem — a bug you
  found, code-review findings, the result of a diagnosis, why something
  broke — in chat, and whenever you write or edit a problem document: a
  known-issues list, a bug write-up, a review report.
---

Report a problem the way a senior developer briefs their lead in a 1-on-1.
The lead knows the project, its goal, and that problems exist. The lead has
not read the code line by line and has not seen your reasoning. Give them a
story they can follow once, top to bottom, and leave the meeting able to make
a decision.

General prose rules (voice, plain language, jargon, lists) come from the
`writing-style` skill. This skill adds what is specific to problem reports.

## Steps

1. **Order the problems.** With three or more, open with a short list: one
   line per problem, a symptom-first title, most severe first. Problems with
   one cause become one entry that says so.
2. **Brief each problem in full before the next**, in this order:
   1. **Headline**: the symptom someone sees, in one sentence ("The clinical
      report never flags a tumour as HRD-high"), not the defect in the code.
   2. **Background**: just enough of how this part of the system works for
      the rest to make sense.
   3. **What's wrong**: the mechanism, told as a story. Follow the main path;
      leave the side branches out.
   4. **Effects**: what readers of the output, users or the data get wrong,
      for whom, and since when.
   5. **Cause**: why the defect could exist, the structural reason behind it.
   6. **Options**, only when they exist: each with what it does and what it
      costs, in the lead's terms. Give the recommendation's reasons in the
      same terms: what changes for users, the data or the schedule. Function
      signatures, schemas, module layouts and code-level trade-offs (an
      extra query, a duplicated helper) belong to the implementer.
   7. **What I need from you**: a decision, an approval, a question for
      someone else, or "Nothing needed, this is for your information."
3. **Size by the detail test, not by length.** A detail stays in the story
   only if it changes what the lead understands or decides, or if the lead
   needs it to find the problem in the code. Everything else goes to the
   implementer block (documents) or stays with you until asked (chat). A
   convoluted problem gets as many paragraphs as its story needs.
4. **Reread against the checklist** below and fix every miss. The report is
   done when every item holds.

In chat, write the briefing as plain paragraphs in this order, with bold
labels only for Options and What I need from you. In a document, bold labels
on each part are fine.

## Words

Use only terms the lead already uses, or terms you define in plain words the
first time they appear. A definition uses words the lead knows; a definition
that leans on another undefined term is no definition. Terms that
professionals in the field use every day (WGS, ETL, SV, t-SNE) need no
definition and no expansion. Name each thing by what it does ("the step that
writes the final report"), and
keep the labels you coined while reasoning out of the report: the lead never
saw them. A new name earns its place only when the report defines it at first
use and needs it again.

Address the lead as "you"; the person you are talking to is the lead.

Give history only when it changes the decision, and give it as a date or an
impact ("broken since July 2024, so every clinical report since then"), not
as commit hashes or branch names.

## Code in text

Use code where plain words cannot point at the thing; use plain words
everywhere else.

- Name modules, tools and analyses by their plain name: "Battenberg", "the
  WGS POST ETL", "the manifest writer". Leave out the class and the path when
  the plain name already finds them.
- Quote code when the code *is* the story: the inverted condition, the
  literal `"N/A"` string, the one line that sends every report down the
  wrong path.
- Name a file once when plain words could mean several files ("the clinical
  summary template, `patient_summary.html.jinja`").
- Give a line number only when the line itself is the finding.

Format code items the way the
[Google code-in-text guide](https://developers.google.com/style/code-in-text)
says:

- Code font for identifiers, file names, paths, literal values, and commands;
  ordinary font for product, project and organization names.
- Introduce a code item with a noun: "the `close` method", "the
  `settings.h` file".
- Inflect the noun, never the code item: "the `ADDRESS` constant's value",
  not "`ADDRESS`'s value"; "send a `POST` request", not "`POST` the data".
- Omit the class from a method name unless it is ambiguous.
- Text that the product shows on screen goes in quotes, not code font: the
  page says "Unmatched", the MSI cell says "HAS NOT BEEN RUN".

## Documents

A problem document serves the lead and also hands the work to whoever
implements the fix, often Claude. In a document:

- The entry's heading is the headline, so it names the symptom.
- The last part is labeled **Decision needed**.

Write the briefing for the lead, then end each entry with a collapsed
implementer block:

```markdown
<details>
<summary>For the implementer</summary>

...

</details>
```

The block holds what the implementer needs and the lead does not:
locations (files, functions, line numbers where they help), code sketches of
the options, how to verify the fix (tests, comparisons against a baseline),
commit hashes and branch names, and any design analysis. Code can be dense
here. Every other Words rule still holds, design vocabulary included: a term
like "seam" or "deep module" gets its definition at first use in the
document, or a pointer to the skill or document that defines it. An undefined term helps no reader,
Claude included.

## Checklist

1. The headline names a symptom someone sees.
2. Every term is one the lead uses or is defined in plain words at first use.
3. Every code item points at something plain words cannot, in Google
   code-in-text format.
4. Line numbers appear only where the line is the finding.
5. Problems come one at a time, most severe first.
6. Options appear only where options exist.
7. The report ends with what you need from the lead.

## Example

> **The clinical report never flags a tumour as HRD-high.**
>
> Each tumour on the clinical page opens with a Specimen Summary, a row with
> purity, ploidy, coverage, MSI and HRD. The HRD score has a High or Low tag
> next to it. The WGS POST ETL hands over the two HRD scores, HRDetect and
> CHORD, as text, and writes a missing score as the string `"N/A"`. The
> clinical summary template (`patient_summary.html.jinja`) then picks the
> tag itself, with its own copy of the thresholds: High if HRDetect is at
> least 0.7 or CHORD is at least 0.5.
>
> The template picks the tag the wrong way round. Its first test should mean
> "if both scores are missing, show N/A", but it says "if both are present":
>
> ```jinja
> ("N/A", "") if (hrdetect_score is not none and chord_score is not none)
> ```
>
> A July 2024 fix for missing HRD results dropped the negation. Since then,
> every tumour with HRD scores gets an "N/A" tag, and no tumour has been
> tagged High on the clinical page. The test could not catch a missing score
> anyway, because the ETL never sends an empty value. It sends `"N/A"`.
>
> Two smaller effects come from the same block. The page prints only
> HRDetect, so a tumour that is high on CHORD alone does not show up. A
> tumour with no WGS POST run shows "None, Low", which looks like a measured
> negative, and nothing marks it as a failure. The research page rates both
> scores correctly, so the two pages can disagree about the same tumour.
>
> The cause is that the High/Low rule lives in two places, the ETL and the
> template. The only check between them confirms that each score is text,
> and `"N/A"` is text.
>
> **Options.** The first is to patch only the template: treat `"N/A"` as
> missing and fix the test. It is small and changes only the HTML, but
> leaves two copies of the thresholds. The second is to have the WGS POST
> ETL make the High/Low call and the template just display it. That leaves
> one copy of the rule, but adds a field to the report data, so the parity
> comparison will flag every tumour with HRD scores.
>
> **What I need from you:** pick an option. Neither can be fully checked
> yet. The comparison script does not look at the HTML, so the template
> patch needs a check of the rendered page. And our only local baseline
> patient currently comes out unmatched (Issue 10), so it has no HRD scores
> to compare.

The faulty line is quoted because it is the finding. The template file is
named because "the clinical template" could mean several files. The class
name, the module path and the line numbers are left out because the plain
names already find them.
