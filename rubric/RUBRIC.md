# Documentation quality rubric

Version 3. Rendered from `rubric/rubric.json`; do not edit by hand.

Every criterion is a yes/no question. A verdict must quote the passage that justifies it, or, when it rests on something being absent, say what was looked for and where.

Page types: tutorial, how-to, reference, explanation, readme, quickstart, landing, other.

## Page structure

### C1. Does the page keep to one job: teaching, guiding a task, lookup, or explanation?

Diátaxis separates tutorials, how-to guides, reference and explanation (https://diataxis.fr). Fail when a substantial passage belongs to a different type, such as background theory inside numbered steps or instructions inside a reference entry. A sentence or two of context is not a failure. Quote the passage that belongs elsewhere.

Applies to: tutorial, how-to, reference, explanation; prose, pdf-section. Added in version 1.

### C2. Does the opening say what the page covers and who it is for?

Pass when the title and first paragraph let a reader decide whether to keep reading. Fail when the page starts with detail before saying what it is about. Quote the opening.

Applies to: all page types; prose, pdf-section. Added in version 1.

### C3. Are prerequisites stated before the first step?

The Good Docs Project how-to and tutorial templates put prerequisites ahead of the steps (https://www.thegooddocsproject.dev/template). Pass when required tools, versions, access or prior knowledge are listed before step one, or the page says there are none. If nothing is stated, record an absence.

Applies to: tutorial, how-to, quickstart; prose, pdf-section. Added in version 1.

### C4. Are the steps in the order the reader performs them?

Fail when a step depends on something a later step or a later optional section introduces. Quote the step that is out of order.

Applies to: tutorial, how-to, quickstart; prose, pdf-section. Added in version 1.

### C5. Does the page say what the reader will have or see when they finish?

Pass when an end state is described: what was built, what now works, or how to confirm success. If the page just stops after the last step, record an absence.

Applies to: tutorial, how-to, quickstart; prose, pdf-section. Added in version 1.

### C6. Do the reference entries present the same kinds of facts in the same order?

Diátaxis asks reference material to be consistent and to mirror the thing it describes (https://diataxis.fr/reference/). Fail when some entries give a type, default and description and others give only a name. Quote an entry that breaks the pattern.

Applies to: reference; prose, pdf-section. Added in version 1.

### C7. Do the headings describe their sections well enough to find a topic by scanning?

Fail on headings such as Overview, Notes or Misc that do not say what the section holds, or a heading whose section is about something else. Quote the heading.

Applies to: all page types; prose, pdf-section. Added in version 1.

### C8. Does the README say what the project is and show how to install or run it?

The Good Docs Project README template leads with what the project does and how to start (https://www.thegooddocsproject.dev/template). Pass when both are present. Record an absence for whichever is missing.

Applies to: readme; prose, pdf-section. Added in version 1.

### C23. Is each action set out as its own step rather than run together in a paragraph?

Pass when actions are numbered items or separately headed steps. Fail when one paragraph runs several actions together. Quote the paragraph.

Applies to: tutorial, how-to, quickstart; prose, pdf-section. Added in version 2.


## Usability by reading

### C9. Is every term the page relies on defined, linked, or safely assumed for its stated audience?

Read as someone new to this product who knows the general field. Terms standard in that field are safely assumed, even where a newcomer to the product might not know them. Fail when a term the product or its publisher coined, or uses in its own sense, appears without definition or link. Quote the first undefined use and say why it is product-specific.

Applies to: all page types; prose, pdf-section, code-comment. Added in version 1.

### C10. Can each step be carried out without guessing a value, a location, or a command?

Follow the steps literally. Fail when a step says to configure, set up or update something without saying where or with what. Do not fill the gap from your own knowledge of the tool. Quote the step.

Applies to: tutorial, how-to, quickstart; prose, pdf-section. Added in version 1.

### C11. Does each step, command or code sample come with its expected result?

Applies to steps in a user interface as well as to commands and code. Pass when the reader can tell whether each action worked: sample output, a described change on screen, or a check to run. Navigation steps whose result is self-evident (Go to the Samples tab) need none. Fail when some actions that change something state a result and others do not. Quote an action that has no stated result, or record an absence if none do.

Applies to: tutorial, how-to, quickstart; prose, pdf-section. Added in version 1.

### C12. Do the examples use concrete values and make clear which parts the reader must replace?

Fail on examples made only of placeholders such as foo, or on examples where it is unclear which parts are literal. Pages with no examples fail only if one is plainly needed to act on the page; then record an absence.

Applies to: all page types; prose, pdf-section, code-comment. Added in version 1.

### C13. Does the page link to, or name, what the reader needs when it depends on information held elsewhere?

Fail on phrases such as see the docs or as described earlier with no link or name. Quote the dangling pointer.

Applies to: all page types; prose, pdf-section. Added in version 1.

### C14. Does the page say what to do when something it describes commonly goes wrong?

Pass when at least the likeliest failure has a stated symptom and remedy, or a link to troubleshooting. Vague advice such as check your configuration does not count. A stated limit or precondition (You can't pay out until the balance meets the minimum) does not count unless the page also says what the reader will see and what to do about it. Record an absence when nothing is offered.

Applies to: how-to, tutorial, quickstart, reference; prose, pdf-section. Added in version 1.

### C15. Does the comment say what the code is for or why it exists, beyond restating its name?

Fail on comments that repeat the identifier, such as Frob x on a function named frob. Quote the comment.

Applies to: all page types; code-comment. Added in version 1.

### C16. Are parameters, return values and errors described wherever a caller needs them?

Judge public functions, classes and modules. Pass when a caller could use the code without reading its body. Quote a documented signature for a pass; record an absence naming the undocumented function for a fail.

Applies to: all page types; code-comment. Added in version 1.


## Sentence-level clarity

### C17. Can every sentence be understood on first reading?

Fail when a sentence must be reread to parse: stacked clauses, a buried subject, or several ideas joined with and. Quote the sentence. For a pass, record what you searched.

Applies to: all page types; prose, pdf-section, code-comment. Added in version 1.

### C18. Is each thing called by the same name throughout?

Fail when the page switches between names for one thing, such as workspace, project and environment, without saying they are the same. Quote both uses.

Applies to: all page types; prose, pdf-section, code-comment. Added in version 1.

### C19. Are instructions written as direct commands to the reader?

Pass on Run the installer, and on You can deactivate a link by setting active to false, which names the action and how to do it. Fail on passives (The installer should be run) and hedges (You may want to consider running). Judge the actions the page asks the reader to perform. A recommendation or a stated limit beside the steps (We recommend checking the template first) does not fail the page on its own. Quote the indirect instruction.

Applies to: tutorial, how-to, quickstart, readme; prose, pdf-section. Added in version 1.

### C20. Is the page free of sentences that could be deleted without losing information?

Fail on filler: a sentence or lead-in that only restates the heading above it (To create a project: under Create a project), announcing what the next sentence will say, or history the reader does not need for the page's job. Quote the sentence.

Applies to: all page types; prose, pdf-section, code-comment. Added in version 1.

### C21. Is it clear what every it, this, that and they refers to?

Fail when a reader could plausibly attach a pronoun or the thing to the wrong noun, or to nothing named. A pronoun whose only sensible referent is the subject of its own sentence, table row or entry is clear. Quote the sentence and name the two readings.

Applies to: all page types; prose, pdf-section, code-comment. Added in version 1.

### C22. Are abbreviations spelled out the first time they appear?

Common abbreviations for the audience, such as API, URL and CSV, need no expansion. Fail on product or domain abbreviations used without one. Quote the first use.

Applies to: all page types; prose, pdf-section, code-comment. Added in version 1.
