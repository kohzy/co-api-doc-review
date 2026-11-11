# Run record: Isometric Certify docs, 2026-11-11

Rubric version 3 was produced by a `refine-rubric` run on Isometric's public Certify user guides. This file records which documentation that was. The run directory itself (`runs/2026-11-11-isometric-certify-refine-rubric/`) holds copies of Isometric's page text and is not committed, so the changelog's evidence pointers resolve only where that directory exists locally.

## Run

- Date: 2026-11-11
- Mode: refine-rubric
- Rubric: version 1 judged, version 3 out (commit 0ed3813). Version 2 was applied from the Stripe Payments run while this run was in progress, so the evaluators here read the version 1 wording. The version 2 wordings of C4, C14, C19 and C21 were not tested by this run, and C23 was not judged.
- Seed: 4711
- Doc set: all 34 pages under https://docs.isometric.com/user-guides/certify/, as listed in https://docs.isometric.com/sitemap.xml and matching https://docs.isometric.com/llms.txt, fetched as rendered HTML and reduced to text. The snapshots include the site's navigation and search chrome around each page body.
- Sample: none drawn. All 34 pages were judged: 12 typed how-to, 11 typed reference, 9 typed explanation, 1 typed landing, 1 typed tutorial
- Evaluators: newcomer, practitioner, editor; 1,458 valid verdicts, none set aside
- Overall agreement (AC1): 0.80
- User spot-checks: agreed with 2 of 3 unanimous items and 4 of 7 contested items; 2 of 12 items skipped (s07, s09). Long pages were shown as excerpts, and on s05 the sentence the evaluators quoted lay outside the excerpt.
- Thresholds in `rubric/config.json` were confirmed unchanged after this run.

## Changes accepted

- C9 reworded: terms standard in the page's field are assumed; only terms the product coined or uses in its own sense fail (p022, p012, p009, p011)
- C11 reworded: covers steps in a user interface as well as commands and code (p014, p018, p028, p008)
- C20 reworded: a lead-in that only restates the heading above it is filler (p014, p028, p013, p021)
- C19 reworded, on top of the version 2 text: a recommendation or stated limit beside the steps does not fail a page on its own (p023, p024, p030)

## Pages judged

| Item | Type | URL |
|---|---|---|
| p001 | how-to | https://docs.isometric.com/user-guides/certify/add-feedstock |
| p002 | explanation | https://docs.isometric.com/user-guides/certify/attribution |
| p003 | reference | https://docs.isometric.com/user-guides/certify/component-blueprint-library |
| p004 | how-to | https://docs.isometric.com/user-guides/certify/create-project |
| p005 | reference | https://docs.isometric.com/user-guides/certify/data-visibility |
| p006 | reference | https://docs.isometric.com/user-guides/certify/datapoint-precision |
| p007 | explanation | https://docs.isometric.com/user-guides/certify/datapoint-sharing |
| p008 | how-to | https://docs.isometric.com/user-guides/certify/field-measurements |
| p009 | reference | https://docs.isometric.com/user-guides/certify/geospatial/lidar |
| p010 | explanation | https://docs.isometric.com/user-guides/certify/geospatial/principles |
| p011 | reference | https://docs.isometric.com/user-guides/certify/geospatial/rasters |
| p012 | reference | https://docs.isometric.com/user-guides/certify/geospatial/shapefiles |
| p013 | how-to | https://docs.isometric.com/user-guides/certify/ghg-entry |
| p014 | how-to | https://docs.isometric.com/user-guides/certify/ghg-statement |
| p015 | explanation | https://docs.isometric.com/user-guides/certify/identifying-components |
| p016 | landing | https://docs.isometric.com/user-guides/certify/introduction |
| p017 | explanation | https://docs.isometric.com/user-guides/certify/key-certify-concepts |
| p018 | tutorial | https://docs.isometric.com/user-guides/certify/lca |
| p019 | explanation | https://docs.isometric.com/user-guides/certify/log-of-issues |
| p020 | reference | https://docs.isometric.com/user-guides/certify/measurement-samples |
| p021 | explanation | https://docs.isometric.com/user-guides/certify/modifying-resources |
| p022 | reference | https://docs.isometric.com/user-guides/certify/project-assets/activities-reference |
| p023 | how-to | https://docs.isometric.com/user-guides/certify/project-assets/add-activities |
| p024 | how-to | https://docs.isometric.com/user-guides/certify/project-assets/add-sites |
| p025 | explanation | https://docs.isometric.com/user-guides/certify/project-assets/introduction |
| p026 | reference | https://docs.isometric.com/user-guides/certify/project-assets/sites-reference |
| p027 | how-to | https://docs.isometric.com/user-guides/certify/project-design |
| p028 | how-to | https://docs.isometric.com/user-guides/certify/project-emissions |
| p029 | how-to | https://docs.isometric.com/user-guides/certify/sensitivity-analysis |
| p030 | how-to | https://docs.isometric.com/user-guides/certify/storage-sites |
| p031 | reference | https://docs.isometric.com/user-guides/certify/supplier-reference-id |
| p032 | how-to | https://docs.isometric.com/user-guides/certify/time-series-data-upload |
| p033 | reference | https://docs.isometric.com/user-guides/certify/tree-measurements |
| p034 | explanation | https://docs.isometric.com/user-guides/certify/validation |
