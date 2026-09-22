# Limitations

Stated plainly, not hedged into vagueness — this is what would need to change
for a more rigorous version of this project, and why it wasn't done here.

## Sample size and what it rules out

Four companies is enough to compute and compare a ratio, not enough to
estimate a statistical model. Specifically, this project does **not**
attempt:

- **Modified Jones discretionary accruals** — the standard approach
  regresses total accruals against revenue change and PP&E within an
  industry-year to separate "normal" from "discretionary" accruals. That
  regression needs on the order of 80–120 company-years per industry-year to
  produce stable coefficients. Four companies, one year, can't support it —
  running it anyway would produce a number that looks precise and means
  nothing.
- **Beneish M-score** — needs two consecutive years of eight separate
  sub-ratios per company (DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA), most
  of which require line items (SG&A, depreciation schedules, specific asset
  categories) not extracted here because this screen's inputs were scoped
  to exactly what the accrual ratio needs.
- **Piotroski F-score** — a 9-point fundamental checklist across
  profitability, leverage, and efficiency trends. Same issue: needs more
  years and more line items than were extracted for this project.
- **A formal backtest** — whether a high accrual ratio actually predicted
  weaker subsequent stock performance or a later restatement. That needs a
  multi-year panel across many companies with forward returns, which this
  4-company, single-year screen has no way to construct.

All four were part of an earlier, more ambitious version of this project's
plan. They were cut deliberately when it became clear the real, retrievable
data universe was 4 companies, not 80+ — not discovered late and hidden.

## Universe selection

The 4 companies (L&T, KEC International, NCC, PSP Projects) were chosen
because their FY26 annual reports/results filings were genuinely retrievable
and machine-extractable at the time this was built, not selected to hit a
target sample size or a specific finding. A meaningfully larger EPC/
infrastructure universe exists in India; most of it either doesn't publish
a machine-extractable annual report or sits behind registration-gated
investor portals that would have compromised this project's reproducibility
standard (every figure traceable to a specific, downloadable, hash-verified
page).

## Extraction gaps

- **KEC International's Statement of Changes in Equity** extracts as
  reversed, unusable text — the table is typeset rotated/vertical in the
  source PDF, a glyph-orientation problem no extraction method tried could
  fix. Not used anywhere in this screen's calculations, so it didn't block
  anything, but it's a genuine, documented gap in what can currently be
  pulled from that file. See `data/raw/source_manifest.md`.
- **PSP Projects' FY25 PAT** required a manual adjustment (subtracting a
  ₹1.54 Crore JV share-of-loss from the raw PBT-derived figure) that a
  naive automated extraction would have missed. Caught by manual review
  before the computation ran — flagged here as a reminder that automated
  extraction at this scale still needs a human check, not because it's
  unresolved.

## Basis and comparability

- All four companies are compared on a **consolidated** basis, per this
  project's stated standard — but "consolidated" doesn't mean identical
  scope. Each company's consolidation boundary (subsidiaries, JVs, associates
  included) differs, and this project doesn't attempt to normalize for that.
- L&T's FY26 PAT includes a one-time exceptional provision tied to the new
  labour codes, disclosed on the same page as the PAT figure used here. It's
  left inside the number rather than adjusted out, because the point of this
  screen is what was actually reported and actually converted to cash — but
  it does mean L&T's −0.16% accrual ratio isn't a clean read on recurring
  operations alone.

## What would fix each of these

A larger universe (30+ companies in the sector, multiple years) would enable
the Modified Jones regression and a real backtest. Extracting a wider set of
line items per company (SG&A, depreciation, asset composition) would enable
Beneish and Piotroski. Neither is a small extension of this project — both
are closer to a second project built on the same `indfin` library.
