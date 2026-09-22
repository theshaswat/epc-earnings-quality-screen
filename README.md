# EPC Earnings-Quality Screen

Four listed EPC/infrastructure companies — Larsen & Toubro, KEC International,
NCC Limited, PSP Projects — ranked by how much of their FY26 reported profit
is actually backed by operating cash, using Sloan (1996) total accruals.
Every input is hand-extracted from a specific, cited page of a real annual
report or results filing, and every balance sheet is reconciled before any
ratio is computed.

Full writeup: [`reports/methodology_memo.pdf`](reports/methodology_memo.pdf).

## The question

Profit and cash are not the same thing, and in a working-capital-heavy
business — retention money held back by clients, receivables that sit for
quarters, unbilled revenue booked ahead of collection — the gap between them
is exactly where earnings quality breaks down first. This asks: for FY26,
whose profit is backed by operating cash, and whose isn't?

## Findings

| Rank | Company | FY26 PAT (₹ Cr) | FY26 CFO (₹ Cr) | Accrual Ratio | CFO / PAT |
|---|---|---|---|---|---|
| 1 (worst) | NCC Limited | 724.0 | −458.5 | +5.03% | −0.63x |
| 2 | KEC International | 605.6 | −414.1 | +4.31% | −0.68x |
| 3 | Larsen & Toubro | 16,084.0 | 16,741.0 | −0.16% | 1.04x |
| 4 (best) | PSP Projects | 55.5 | 322.8 | −9.82% | 5.81x |

Worst = most profit relative to assets, least cash behind it. Best = cash
generation running ahead of reported profit. See the memo for what each of
these numbers actually means per company — a high or low ratio isn't a
verdict on its own.

## Why this is 4 companies and 1 year, not a sector-wide screen

SEBI's quarterly disclosure norms (LODR Regulation 33) don't require a cash
flow statement at Q1, Q2, or Q3 — only at year-end. The accrual ratio this
project depends on needs CFO, so this had to be an FY26 annual-report screen,
not a running quarterly one. The universe is 4 companies because those were
the ones with genuinely retrievable, unmodified, machine-extractable annual
reports at the time this was built — not a target sample size chosen in
advance. See [`LIMITATIONS.md`](LIMITATIONS.md) for what a larger version of
this project would need.

## Project structure

```
epc-earnings-quality-screen/
├── data/
│   ├── raw/
│   │   ├── annual_reports/       # 4 real, unmodified source PDFs
│   │   └── source_manifest.md    # URL, retrieval date, SHA-256 per file
│   ├── processed/
│   │   └── reconciliation_log.md # balance-sheet tie-out results
│   └── final/
│       ├── verified_inputs.csv   # hand-extracted, page-cited figures
│       └── accrual_screen.csv    # computed ratios and ranking
├── src/
│   ├── accruals.py               # reconciliation + accrual computation
│   ├── build_charts.py           # the 3 exhibits in outputs/charts/
│   ├── build_excel.py            # live formula-driven screener workbook
│   └── build_pdf.py              # the methodology memo
├── outputs/
│   ├── charts/                   # 3 PNG exhibits, no overlap in content
│   └── screener/                 # Excel workbook
├── reports/
│   └── methodology_memo.pdf      # full writeup — read this first
├── requirements.txt
├── DATA_DICTIONARY.md
├── LIMITATIONS.md
├── LICENSE
└── README.md
```

## How to run

```bash
# from the parent directory containing both this repo and indfin/
pip install -r epc-earnings-quality-screen/requirements.txt
cd epc-earnings-quality-screen
python src/accruals.py       # reconciles inputs, computes accrual_screen.csv
python src/build_charts.py   # writes outputs/charts/*.png
python src/build_excel.py    # writes outputs/screener/*.xlsx
python src/build_pdf.py      # writes reports/methodology_memo.pdf
```

Requires [`indfin`](https://github.com/theshaswat/indfin) cloned as a sibling
directory (`../indfin`) — the shared reconciliation/extraction library this
project and [`bank-nim-credit-cost-bridge`](https://github.com/theshaswat/bank-nim-credit-cost-bridge)
both depend on.

## Data / sources

Company FY26 annual reports and results filings, downloaded directly from
each company's investor-relations page or NSE's archive. Full URLs, retrieval
timestamps, and SHA-256 hashes for every source file: `data/raw/source_manifest.md`.

## Limitations

See [`LIMITATIONS.md`](LIMITATIONS.md) — most importantly, this is a
comparative screen across 4 companies, not a scored/backtested model, and it
deliberately doesn't attempt a Modified Jones discretionary-accruals
regression, Beneish M-score, or Piotroski F-score.

## Author

Shaswat Sharma — [github.com/theshaswat](https://github.com/theshaswat)
