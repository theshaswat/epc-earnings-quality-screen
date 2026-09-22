# Source Manifest — EPC Earnings-Quality Screen

Every file in `data/raw/` is logged here on download: exact URL, retrieval
timestamp, and a SHA-256 hash. If a company re-uploads a "corrected" filing
later, the hash changes and the pipeline should fail loudly rather than
silently analysing different numbers than the ones reconciled against.

| File | Company | Period | URL | Retrieved | SHA-256 |
|---|---|---|---|---|---|
| annual_reports/KEC_AR_FY26.pdf | KEC International Ltd | FY26 (year ended 31-Mar-2026) | https://www.kecrpg.com/public/media/annualReportMedia/KEC_Annual_Report_2025-26.pdf | 2026-09-23T00:49 IST | `ba638897313ac1fe5b7da42d7a95dac5f9efec1d1a203f88d9f963622ba3c820` |
| annual_reports/LT_FY26_Results.pdf | Larsen & Toubro Ltd | FY26 (year ended 31-Mar-2026) | https://2025prodstorageaccount-eqdyc8g8hpccdfez.a02.azurefd.net/ltprod/media/dryh21pu/2026-05-05-financial-results-for-the-year-ended-march-31-2026.pdf | 2026-09-23T01:08 IST | `b5f603a79efd02d44dfc54fd2a2bdbe133bc2ef795866bb6c251b6b1ca2a90f1` |
| annual_reports/NCC_AR_FY26.pdf | NCC Ltd | FY26 (year ended 31-Mar-2026) | https://www.ncclimited.com/annual-reports/NCCAnnualReport202526.pdf | 2026-09-23T01:08 IST | `d1166c9806d223190b2ee72874cdcccdf7b040aab1355000c0d568e875a78337` |
| annual_reports/PSP_AR_FY26.pdf | PSP Projects Ltd | FY26 (year ended 31-Mar-2026) | https://nsearchives.nseindia.com/annual_reports/AR_29288_PSPPROJECT_2025_2026_A_19303721_28052026184411.pdf | 2026-09-23T01:08 IST | `249341afe9f8c96fa033604a79eed8cdaa55327cce1585e4a4b845b4bda0900a` |

All four hashes re-verified against the files in `annual_reports/` at build
time (`shasum -a 256`) — match, no drift since download.

## Notes on this filing (Phase 0 gate findings)

- 215 pages, genuine Integrated Annual Report, PDF 1.7.
- **Layout note — corrected after direct testing (`indfin/tests/
  test_extract_integration.py`), leaving the correction visible here rather
  than quietly editing history:** the financial-statements section
  (pp. ~112–180) is typeset as merged two-page spreads inside single PDF
  pages — e.g. the PDF page carrying printed pages "340–341" holds the
  Statement of Changes in Equity on its left half and the Statement of Cash
  Flows on its right half. It was initially assumed a naive
  `page.extract_text()` interleaves both halves into nonsense and that a
  half-page crop was required to recover the cash-flow section. Verified
  directly: **that's not what happens.** `extract_text()` on the full,
  uncropped page returns the complete, correctly-ordered cash-flow
  statement — it's preceded by ~2,700 characters of garbled text from the
  rotated equity table, but the two blocks are sequential, not interleaved.
  No crop is needed to recover the cash-flow statement on this page.
- What IS still broken: the Statement of Changes in Equity itself — a
  rotated/vertical table that extracts as reversed, unusable text by any
  method tried (a crop doesn't fix a glyph-rotation problem). Not needed
  for this project; left unfixed and flagged rather than spending time on
  a statement nothing downstream consumes.
- Balance sheet line `Contract assets` (Note 20): `12,127.56` (FY26) vs
  `11,043.51` (FY25), ₹ Crore — ties to the note.
- Note 20 breaks out `Amount receivable from customers for contract works`
  (`7,408.59`) separately from `Retention receivables` (`4,922.51`) — the
  retention-ageing split the EPC overlay module needs is genuinely disclosed,
  not something to be estimated.
- Cash flow statement, Operating section: `Contract assets (775.86)` as a
  working-capital adjustment for FY26 — this is the line the whole accrual
  measure depends on, and it extracts as a clean signed number.
- Consolidated basis available; standalone also available; both figures
  extractable side by side — use consolidated per the project standard,
  logged.

## Notes on the other three filings

- **L&T (`LT_FY26_Results.pdf`)** is the standalone regulatory results
  filing (14 pages), not the full integrated annual report — L&T's FY26
  annual report runs several hundred pages and wasn't needed here; the
  results filing carries the audited consolidated balance sheet, P&L, and
  cash flow statement in full, which is all this screen uses.
- **NCC (`NCC_AR_FY26.pdf`)** is the full 343-page integrated annual
  report. Balance sheet and P&L on pp. 249–250; cash flow statement on
  pp. 254–255.
- **PSP Projects (`PSP_AR_FY26.pdf`)** is the full 304-page annual report.
  Reports in ₹ Lakh, not ₹ Crore like the other three — every figure pulled
  from this filing was converted (`/100`) before entering
  `data/final/verified_inputs.csv`, and that conversion is noted inline in
  the CSV's `source_page_note` column.

## Scope note

This screen covers 4 listed EPC/infrastructure names (L&T, KEC
International, NCC, PSP Projects) across FY25–FY26, chosen because all
four disclose full audited cash flow statements at year-end (SEBI LODR
Reg. 33 doesn't require this quarterly) and were retrievable as genuine,
unmodified filings. A larger universe was considered and set aside — most
mid-cap EPC names either don't publish machine-extractable annual reports
or require registration-gated access that would break the reproducibility
this project is built around.
