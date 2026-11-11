# Documentation review: https://docs.stripe.com/get-started/use-cases/startup

2026-11-11 · rubric version 1

> **Untested rubric.** No version of this rubric has passed a held-out test. Treat every verdict below as provisional.

## What was reviewed

| Kind | Found | Reviewed |
|---|---|---|
| Prose pages | 1 | 1 |
| PDF sections | 0 | 0 |
| Source files with comments | 0 | 0 |

## Summary

10 of 17 judged criteria failed across 1 items.

| Criterion | Question | Failed on |
|---|---|---|
| C3 | Are prerequisites stated before the first step? | 1 of 1 items |
| C4 | Are the steps numbered and in the order the reader performs them? | 1 of 1 items |
| C9 | Is every term the page relies on defined, linked, or safely assumed for its stated audience? | 1 of 1 items |
| C10 | Can each step be carried out without guessing a value, a location, or a command? | 1 of 1 items |
| C11 | Does each command or code sample come with its expected result? | 1 of 1 items |
| C14 | Does the page say what to do when something it describes commonly goes wrong? | 1 of 1 items |
| C17 | Can every sentence be understood on first reading? | 1 of 1 items |
| C18 | Is each thing called by the same name throughout? | 1 of 1 items |
| C19 | Are instructions written as direct commands to the reader? | 1 of 1 items |
| C20 | Is the page free of sentences that could be deleted without losing information? | 1 of 1 items |

## Findings by item

### https://docs.stripe.com/get-started/use-cases/startup (quickstart)

**Failed**

- **C3. Are prerequisites stated before the first step?**
  Looked for a prerequisites list or a statement that there are none (for example what business, tax or bank information to have ready, or a product to sell) in the whole page, especially the opening paragraph and the text before the first step under 'Create a Stripe account'; not found.

- **C4. Are the steps numbered and in the order the reader performs them?**
  > Click the copy icon next to an existing link on the Payment Links page, or go to the payment link’s details page.

- **C9. Is every term the page relies on defined, linked, or safely assumed for its stated audience?**
  > In the Dashboard, click Verify your email.

- **C10. Can each step be carried out without guessing a value, a location, or a command?**
  > Fill out your business profile.

- **C11. Does each command or code sample come with its expected result?**
  > Click Create link.

- **C14. Does the page say what to do when something it describes commonly goes wrong?**
  Looked for a symptom and remedy for any likely failure (verification email not arriving, account verification rejected, payment link not working) or a link to troubleshooting in the whole page, including the 'Go live' and 'Next steps' sections; not found.

- **C17. Can every sentence be understood on first reading?**
  > Management fulfillment for your orders and view metrics.

- **C18. Is each thing called by the same name throughout?**
  > After you activate your profile, Stripe updates you from sandbox mode to live mode.

- **C19. Are instructions written as direct commands to the reader?**
  > You can optionally add automatic tax collection or revenue-based climate donations.

- **C20. Is the page free of sentences that could be deleted without losing information?**
  > Before integrating with Stripe, create a Stripe account.

**Passed:** C2, C5, C7, C12, C13, C21, C22

## Changing a criterion

This report applies the rubric as it stands and does not change it. If a verdict here looks wrong, the criterion may need rewording: run `refine-rubric` on a public doc set to test and revise it.
