# Run record: Stripe Payments docs, 2026-11-11

Rubric version 2 was produced by a `refine-rubric` run on Stripe's public Payments documentation. This file records which documentation that was. The run directory itself (`runs/2026-11-11-stripe-payments-refine-rubric/`) holds copies of Stripe's page text and is not committed, so the changelog's evidence pointers resolve only where that directory exists locally.

## Run

- Date: 2026-11-11
- Mode: refine-rubric
- Rubric: version 1 in, version 2 out (commit 1f901f9)
- Seed: 4217
- Doc set: 36 pages from docs.stripe.com, fetched as Stripe's markdown (`.md`) rendering: the guides in the Payments section of https://docs.stripe.com/llms.txt, plus API reference pages for PaymentIntents, PaymentMethods, SetupIntents, Refunds, Charges and errors
- Sample: 12 pages, 7 typed reference and 5 typed how-to
- Evaluators: newcomer, practitioner, editor; 543 valid verdicts, none set aside
- Overall agreement (AC1): 0.79
- User spot-checks: agreed with 2 of 4 unanimous items and 3 of 8 contested items. One unanimous item (s11) was shown with a truncated excerpt and is unreliable.

## Changes accepted

- C19 reworded: "You can X by doing Y" counts as a direct instruction (p009, p010, p011)
- C4 split: step order, and a new criterion on setting out each action as its own step (p008 to p012)
- C14 reworded: a bare limit or precondition is not a symptom and remedy (p012)
- C21 reworded: fail only on pronouns a reader could plausibly misattach (p007, p003)

## Sampled pages

| Item | Type | URL |
|---|---|---|
| p001 | reference | https://docs.stripe.com/api/payment_intents/create.md |
| p002 | reference | https://docs.stripe.com/api/payment_intents/object.md |
| p003 | reference | https://docs.stripe.com/api/payment_intents/retrieve.md |
| p004 | reference | https://docs.stripe.com/api/payment_methods/attach.md |
| p005 | reference | https://docs.stripe.com/api/refunds/object.md |
| p006 | reference | https://docs.stripe.com/api/setup_intents/create.md |
| p007 | reference | https://docs.stripe.com/declines/codes.md |
| p008 | how-to | https://docs.stripe.com/payment-links/post-payment.md |
| p009 | how-to | https://docs.stripe.com/payment-links/share.md |
| p010 | how-to | https://docs.stripe.com/payments/accept-a-payment.md?payment-ui=checkout&ui=stripe-hosted |
| p011 | how-to | https://docs.stripe.com/payments/save-and-reuse.md?payment-ui=elements |
| p012 | how-to | https://docs.stripe.com/payouts/multi-currency-settlement.md |

## Pages in the doc set but not sampled

- https://docs.stripe.com/api/charges.md
- https://docs.stripe.com/api/charges/object.md
- https://docs.stripe.com/api/errors.md
- https://docs.stripe.com/api/payment_intents.md
- https://docs.stripe.com/api/payment_intents/cancel.md
- https://docs.stripe.com/api/payment_intents/capture.md
- https://docs.stripe.com/api/payment_intents/confirm.md
- https://docs.stripe.com/api/payment_intents/list.md
- https://docs.stripe.com/api/payment_intents/update.md
- https://docs.stripe.com/api/payment_methods.md
- https://docs.stripe.com/api/payment_methods/create.md
- https://docs.stripe.com/api/payment_methods/detach.md
- https://docs.stripe.com/api/payment_methods/object.md
- https://docs.stripe.com/api/refunds.md
- https://docs.stripe.com/api/refunds/create.md
- https://docs.stripe.com/api/setup_intents.md
- https://docs.stripe.com/api/setup_intents/object.md
- https://docs.stripe.com/payment-links/buy-button.md
- https://docs.stripe.com/payments/payment-intents.md
- https://docs.stripe.com/payments/payment-intents/verifying-status.md
- https://docs.stripe.com/payments/payment-methods.md
- https://docs.stripe.com/payments/payment-methods/integration-options.md
- https://docs.stripe.com/payments/place-a-hold-on-a-payment-method.md
- https://docs.stripe.com/payments/save-during-payment.md?payment-ui=elements
