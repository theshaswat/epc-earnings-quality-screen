"""EPC earnings-quality screener workbook — a live, formula-driven version
of accruals.py's computation, not a paste of the CSV output. Anyone opening
this in Excel should be able to trace every ratio back to an input cell."""
from __future__ import annotations

import datetime as dt
import re
import shutil
import zipfile
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
INPUTS_CSV = ROOT / "data" / "final" / "verified_inputs.csv"
OUT_XLSX = ROOT / "outputs" / "screener" / "epc_earnings_quality_screener.xlsx"

NAVY = "1A3A5C"
LIGHT_NAVY = "DCE6EE"
WHITE = "FFFFFF"

header_font = Font(bold=True, color=WHITE, size=10)
header_fill = PatternFill("solid", fgColor=NAVY)
title_font = Font(bold=True, size=14, color=NAVY)
subtitle_font = Font(italic=True, size=9, color="6B6B6B")
thin_border = Border(*(Side(style="thin", color="BFBFBF"),) * 4)
label_font = Font(bold=True, size=10)


def style_header_row(ws, row: int, ncols: int) -> None:
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border


def autosize(ws, widths: dict[str, int]) -> None:
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


# Deterministic build. The date is arbitrary and carries no meaning beyond
# being fixed -- the retrieval dates that do mean something live in
# data/raw/source_manifest.md.
EPOCH = dt.datetime(2026, 1, 1, 0, 0, 0)


def _make_reproducible(path: Path) -> None:
    """Rewrite the .xlsx so two builds of the same data produce the same bytes.

    Three things vary between runs and none is part of the analysis. Python's
    zipfile stamps every entry with the wall clock; openpyxl overwrites
    dcterms:modified at save time regardless of what the workbook properties
    say, which is why setting wb.properties.modified alone is not enough; and
    deflate output differs between zlib builds, so the same XML compresses to
    different bytes on Linux than on macOS. The first two are normalised. The
    third is sidestepped by storing the archive uncompressed -- 41 KB against
    12 KB, which is nothing next to the source filings in data/raw, and it
    buys a byte guarantee that actually holds across platforms instead of only
    on the machine that built it. Every sheet's XML is identical either way.
    """
    tmp = path.with_suffix(".xlsx.tmp")
    stamp = (EPOCH.year, EPOCH.month, EPOCH.day, EPOCH.hour, EPOCH.minute, EPOCH.second)
    fixed = EPOCH.strftime("%Y-%m-%dT%H:%M:%SZ").encode()
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(
        tmp, "w", zipfile.ZIP_STORED
    ) as dst:
        for item in sorted(src.infolist(), key=lambda i: i.filename):
            data = src.read(item.filename)
            if item.filename == "docProps/core.xml":
                data = re.sub(
                    rb"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)",
                    rb"\g<1>" + fixed + rb"\g<2>",
                    data,
                )
            info = zipfile.ZipInfo(item.filename, date_time=stamp)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = item.external_attr
            dst.writestr(info, data)
    shutil.move(str(tmp), str(path))


def build() -> None:
    df = pd.read_csv(INPUTS_CSV)
    companies = sorted(df["company"].unique())

    wb = Workbook()

    # ---------- Sheet 1: Inputs (raw, cited figures) ----------
    ws_in = wb.active
    ws_in.title = "Inputs"
    ws_in["A1"] = "EPC Earnings-Quality Screen — Verified Inputs"
    ws_in["A1"].font = title_font
    ws_in["A2"] = "Every figure below is hand-extracted from a cited page of a real, downloaded filing. See source_page_note for the exact citation."
    ws_in["A2"].font = subtitle_font
    ws_in.merge_cells("A1:I1")
    ws_in.merge_cells("A2:I2")

    cols = ["company", "basis", "fy", "total_assets", "total_equity", "total_liabilities", "pat", "cfo", "source_page_note"]
    headers = ["Company", "Basis", "FY", "Total Assets (₹ Cr)", "Total Equity (₹ Cr)",
               "Total Liabilities (₹ Cr)", "PAT (₹ Cr)", "CFO (₹ Cr)", "Source / Page Note"]
    start_row = 4
    for j, h in enumerate(headers, start=1):
        ws_in.cell(row=start_row, column=j, value=h)
    style_header_row(ws_in, start_row, len(headers))

    for i, (_, row) in enumerate(df.sort_values(["company", "fy"]).iterrows(), start=start_row + 1):
        for j, col in enumerate(cols, start=1):
            val = row[col]
            cell = ws_in.cell(row=i, column=j, value=val)
            cell.border = thin_border
            if col in ("total_assets", "total_equity", "total_liabilities", "pat", "cfo") and pd.notna(val):
                cell.number_format = "#,##0.00"

    autosize(ws_in, {"A": 20, "B": 14, "C": 8, "D": 16, "E": 16, "F": 18, "G": 12, "H": 12, "I": 60})
    ws_in.freeze_panes = "A5"

    # ---------- Sheet 2: Reconciliation (live formulas checking the tie-out) ----------
    ws_r = wb.create_sheet("Reconciliation")
    ws_r["A1"] = "Balance-Sheet Tie-Out — Assets = Equity + Liabilities"
    ws_r["A1"].font = title_font
    ws_r["A2"] = "Live formula check, independent of src/accruals.py's Python reconciliation (data/processed/reconciliation_log.md) — both must agree."
    ws_r["A2"].font = subtitle_font
    ws_r.merge_cells("A1:G1")
    ws_r.merge_cells("A2:G2")

    r_headers = ["Company", "FY", "Total Assets", "Total Equity", "Total Liabilities", "Equity + Liabilities", "Diff (should be ~0)"]
    for j, h in enumerate(r_headers, start=1):
        ws_r.cell(row=4, column=j, value=h)
    style_header_row(ws_r, 4, len(r_headers))

    df_sorted = df.sort_values(["company", "fy"]).reset_index(drop=True)
    n = len(df_sorted)
    for i in range(n):
        excel_row = 5 + i
        input_row = start_row + 1 + i  # matching row on Inputs sheet
        ws_r.cell(row=excel_row, column=1, value=f"=Inputs!A{input_row}")
        ws_r.cell(row=excel_row, column=2, value=f"=Inputs!C{input_row}")
        ws_r.cell(row=excel_row, column=3, value=f"=Inputs!D{input_row}").number_format = "#,##0.00"
        ws_r.cell(row=excel_row, column=4, value=f"=Inputs!E{input_row}").number_format = "#,##0.00"
        ws_r.cell(row=excel_row, column=5, value=f"=Inputs!F{input_row}").number_format = "#,##0.00"
        ws_r.cell(row=excel_row, column=6, value=f"=D{excel_row}+E{excel_row}").number_format = "#,##0.00"
        ws_r.cell(row=excel_row, column=7, value=f"=C{excel_row}-F{excel_row}").number_format = "#,##0.0000"
        for c in range(1, 8):
            ws_r.cell(row=excel_row, column=c).border = thin_border

    autosize(ws_r, {"A": 20, "B": 8, "C": 16, "D": 16, "E": 18, "F": 20, "G": 16})
    ws_r.freeze_panes = "A5"

    # ---------- Sheet 3: Accrual Screen (the live model) ----------
    ws_s = wb.create_sheet("Accrual Screen")
    ws_s["A1"] = "FY26 Accrual-Ratio Screen — Sloan (1996) Total Accruals"
    ws_s["A1"].font = title_font
    ws_s["A2"] = "Total Accrual Ratio = (PAT − CFO) / Average Total Assets. Positive = profit exceeds cash generated (lower quality). Negative = cash-backed profit (higher quality)."
    ws_s["A2"].font = subtitle_font
    ws_s.merge_cells("A1:H1")
    ws_s.merge_cells("A2:H2")

    s_headers = ["Company", "FY26 Total Assets", "FY25 Total Assets", "Avg. Total Assets",
                 "FY26 PAT", "FY26 CFO", "Total Accruals (PAT−CFO)", "Accrual Ratio %"]
    for j, h in enumerate(s_headers, start=1):
        ws_s.cell(row=4, column=j, value=h)
    style_header_row(ws_s, 4, len(s_headers))

    # Build a lookup of Inputs-sheet row numbers per (company, fy)
    row_lookup = {}
    for i, (_, row) in enumerate(df_sorted.iterrows(), start=start_row + 1):
        row_lookup[(row["company"], row["fy"])] = i

    for k, company in enumerate(companies):
        excel_row = 5 + k
        fy26_row = row_lookup[(company, "FY26")]
        fy25_row = row_lookup[(company, "FY25")]
        ws_s.cell(row=excel_row, column=1, value=company)
        ws_s.cell(row=excel_row, column=2, value=f"=Inputs!D{fy26_row}").number_format = "#,##0.00"
        ws_s.cell(row=excel_row, column=3, value=f"=Inputs!D{fy25_row}").number_format = "#,##0.00"
        ws_s.cell(row=excel_row, column=4, value=f"=AVERAGE(B{excel_row}:C{excel_row})").number_format = "#,##0.00"
        ws_s.cell(row=excel_row, column=5, value=f"=Inputs!G{fy26_row}").number_format = "#,##0.00"
        ws_s.cell(row=excel_row, column=6, value=f"=Inputs!H{fy26_row}").number_format = "#,##0.00"
        ws_s.cell(row=excel_row, column=7, value=f"=E{excel_row}-F{excel_row}").number_format = "#,##0.00"
        ws_s.cell(row=excel_row, column=8, value=f"=G{excel_row}/D{excel_row}").number_format = "0.00%"
        for c in range(1, 9):
            ws_s.cell(row=excel_row, column=c).border = thin_border

    last_row = 4 + len(companies)
    autosize(ws_s, {"A": 20, "B": 16, "C": 16, "D": 16, "E": 12, "F": 12, "G": 20, "H": 14})
    ws_s.freeze_panes = "A5"

    chart = BarChart()
    chart.title = "FY26 Accrual Ratio by Company"
    chart.y_axis.title = "Accrual Ratio %"
    chart.x_axis.title = "Company"
    data = Reference(ws_s, min_col=8, min_row=4, max_row=last_row)
    cats = Reference(ws_s, min_col=1, min_row=5, max_row=last_row)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.height = 9
    chart.width = 18
    ws_s.add_chart(chart, f"A{last_row + 3}")

    # ---------- Sheet 4: Read Me ----------
    ws_readme = wb.create_sheet("Read Me", 0)
    ws_readme["A1"] = "EPC Earnings-Quality Screener"
    ws_readme["A1"].font = Font(bold=True, size=16, color=NAVY)
    lines = [
        "",
        "What this is: a live, formula-driven version of the accrual-quality screen"
        " in src/accruals.py, covering 4 listed EPC/infrastructure companies —",
        "Larsen & Toubro, KEC International, NCC Limited, PSP Projects — FY25 and FY26,",
        "consolidated basis.",
        "",
        "How to use it:",
        "  1. Inputs — the raw, page-cited figures. Nothing here is a formula; every",
        "     cell traces to a specific annual report page (see source_page_note).",
        "  2. Reconciliation — a live check that Total Assets = Total Equity +",
        "     Total Liabilities for every company-year, independent of the Python",
        "     reconciliation already run in src/accruals.py.",
        "  3. Accrual Screen — the actual model. Change any figure on the Inputs",
        "     sheet and every ratio here recalculates automatically.",
        "",
        "Methodology: Sloan (1996) total accrual ratio, computed via the cash-flow",
        "method: (PAT − CFO) / Average Total Assets. See reports/methodology_memo.pdf",
        "for the full writeup, including why this is a comparative screen across four",
        "companies rather than a scored/ranked universe, and what it deliberately",
        "does not attempt (Modified Jones discretionary accruals, Beneish M-score,",
        "Piotroski F-score — see LIMITATIONS.md).",
        "",
        "Author: Shaswat Sharma (github.com/theshaswat)",
    ]
    for i, line in enumerate(lines, start=2):
        ws_readme.cell(row=i, column=1, value=line)
    ws_readme.column_dimensions["A"].width = 95

    OUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    # Fixed document timestamps. openpyxl otherwise stamps the current time into
    # docProps, which is the only thing that differs between two builds of the
    # same data -- every sheet's XML is already identical. Pinning it lets CI
    # check the committed workbook byte for byte instead of taking it on trust.
    wb.properties.created = EPOCH
    wb.properties.modified = EPOCH
    wb.save(OUT_XLSX)
    _make_reproducible(OUT_XLSX)
    print(f"Written: {OUT_XLSX}")


if __name__ == "__main__":
    build()
