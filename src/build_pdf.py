"""Methodology + findings memo, as a PDF. Registers DejaVu Sans (via
matplotlib's bundled copy) so the ₹ glyph renders — reportlab's built-in
fonts render it as a missing-glyph box."""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "outputs" / "charts"
OUT_PDF = ROOT / "reports" / "methodology_memo.pdf"

mpl_fonts = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DejaVuSans", str(mpl_fonts / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(mpl_fonts / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique", str(mpl_fonts / "DejaVuSans-Oblique.ttf")))

NAVY = colors.HexColor("#1a3a5c")
RUST = colors.HexColor("#c0522d")
SAGE = colors.HexColor("#5c7a5c")
GREY = colors.HexColor("#6b6b6b")

styles = {
    "title": ParagraphStyle("title", fontName="DejaVuSans-Bold", fontSize=20, leading=24, textColor=NAVY, spaceAfter=4),
    "subtitle": ParagraphStyle("subtitle", fontName="DejaVuSans-Oblique", fontSize=10.5, leading=14, textColor=GREY, spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName="DejaVuSans-Bold", fontSize=14, leading=18, textColor=NAVY, spaceBefore=16, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="DejaVuSans-Bold", fontSize=11.5, leading=15, textColor=NAVY, spaceBefore=10, spaceAfter=6),
    "body": ParagraphStyle("body", fontName="DejaVuSans", fontSize=10, leading=15, spaceAfter=8),
    "small": ParagraphStyle("small", fontName="DejaVuSans", fontSize=8, leading=11, textColor=GREY, spaceAfter=6),
    "caption": ParagraphStyle("caption", fontName="DejaVuSans-Oblique", fontSize=8.5, leading=11, textColor=GREY, spaceAfter=14, alignment=1),
}


def P(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, styles[style])


def build_table(data, col_widths, header=True) -> Table:
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style_cmds = [
        ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        style_cmds += [
            ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]
    t.setStyle(TableStyle(style_cmds))
    return t


def build() -> None:
    screen = pd.read_csv(ROOT / "data" / "final" / "accrual_screen.csv")
    screen = screen.sort_values("rank_worst_to_best")

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                             topMargin=2.2 * cm, bottomMargin=2.2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    story = []

    story.append(P("EPC Earnings-Quality Screen, FY26", "title"))
    story.append(P("Larsen &amp; Toubro · KEC International · NCC Limited · PSP Projects — "
                    "which company's FY26 profit is actually backed by cash, and which is running on accruals?", "subtitle"))
    story.append(P("Shaswat Sharma &nbsp;·&nbsp; github.com/theshaswat &nbsp;·&nbsp; September 2026", "small"))
    story.append(Spacer(1, 6))

    story.append(P("The question", "h1"))
    story.append(P(
        "Four EPC/infrastructure companies reported FY26 profit growth this year. Profit and cash "
        "are not the same thing, and in a working-capital-heavy business — retention money held back "
        "by clients, receivables that sit for quarters, unbilled revenue booked ahead of collection — "
        "the gap between them is exactly where earnings quality breaks down first. This screen asks a "
        "narrow, answerable question: for FY26, whose profit is backed by operating cash, and whose "
        "isn't?", "body"))
    story.append(P(
        "It doesn't score creditworthiness, doesn't forecast anything, and doesn't claim any of these "
        "four are cooking their books. A high accrual ratio is a flag to look closer, not a verdict.", "body"))

    story.append(P("Method", "h1"))
    story.append(P(
        "Total accrual ratio, following Sloan (1996), computed the cash-flow way:", "body"))
    story.append(P(
        "<b>Accrual Ratio = (PAT − CFO) / Average Total Assets</b>", "body"))
    story.append(P(
        "PAT and CFO both consolidated, FY26. Average total assets is the mean of FY25 and FY26 "
        "closing balance sheets, so the ratio isn't distorted by a company that simply grew its "
        "balance sheet fast. A positive ratio means profit exceeded operating cash generated — "
        "further from cash, lower quality by this measure. Negative means the opposite: cash "
        "generation ran ahead of reported profit.", "body"))
    story.append(P(
        "Every input — total assets, equity, liabilities, PAT, CFO — is hand-extracted from a specific, "
        "cited page of each company's own FY26 filing (annual report or, for L&amp;T, the standalone "
        "results filing), not pulled from a data vendor. Every balance sheet ties out: Total Assets = "
        "Total Equity + Total Liabilities, checked programmatically for all 8 company-years (FY25 and "
        "FY26 each), diff under ₹0.01 Crore in every case — see <font name='DejaVuSans-Oblique'>"
        "data/processed/reconciliation_log.md</font>.", "body"))
    story.append(P(
        "One honest limitation up front: SEBI's quarterly disclosure norms (LODR Regulation 33) don't "
        "require a cash flow statement at Q1, Q2, or Q3 — only at year-end. That's why this is a "
        "single-year, FY26 annual-report screen and not a running quarterly one; the cash-flow number "
        "this whole ratio depends on simply doesn't exist mid-year for any of these four.", "body"))

    table_data = [["Rank", "Company", "FY26 PAT (₹ Cr)", "FY26 CFO (₹ Cr)", "Accrual Ratio", "CFO / PAT"]]
    for _, r in screen.iterrows():
        table_data.append([
            str(int(r["rank_worst_to_best"])), r["company"],
            f"{r['pat']:,.1f}", f"{r['cfo']:,.1f}",
            f"{r['accrual_ratio']*100:+.2f}%", f"{r['cfo_pat_ratio']:.2f}x",
        ])
    story.append(KeepTogether([
        P("What the four numbers say", "h1"),
        build_table(table_data, [1.6 * cm, 4.2 * cm, 3.3 * cm, 3.3 * cm, 3 * cm, 2.6 * cm]),
    ]))
    story.append(Spacer(1, 10))

    story.append(KeepTogether([
        Image(str(CHARTS / "01_accrual_ratio_ranking.png"), width=15.5 * cm, height=9.5 * cm),
        P("Figure 1. FY26 accrual ratio, all four companies. Worst (least cash-backed) at top.", "caption"),
    ]))

    story.append(PageBreak())

    story.append(P("Company by company", "h1"))

    story.append(KeepTogether([
        P("NCC Limited — worst of the four", "h2"),
        P(
            "NCC's FY26 PAT was ₹724 Crore against a CFO of <b>negative</b> ₹459 Crore — the company "
            "reported growing profit while operating cash flow ran the other way entirely. Total assets "
            "grew 23.8% year on year, the second-fastest of the four, which is consistent with a company "
            "still funding growth largely out of working capital rather than converting it. An accrual "
            "ratio of +5.03% is the highest in this set. Worth checking before assuming this is simply "
            "growth-phase noise: NCC has flagged working-capital pressure in past cycles, so this isn't a "
            "one-off pattern for the company, though FY26 specifically is the year in front of us.", "body"),
    ]))

    story.append(KeepTogether([
        P("KEC International — close behind", "h2"),
        P(
            "Same shape as NCC on a smaller base: PAT of ₹606 Crore, CFO of negative ₹414 Crore, accrual "
            "ratio +4.31%. KEC's FY26 annual report is also the one filing in this set with a genuinely "
            "difficult extraction layout — its financial-statements section is typeset as merged two-page "
            "spreads, and the Statement of Changes in Equity extracts as reversed, unusable text no matter "
            "which extraction method is tried (a rotated-table problem, not a crop problem). That statement "
            "isn't used anywhere in this screen, so it didn't block the analysis, but it's flagged in "
            "<font name='DejaVuSans-Oblique'>data/raw/source_manifest.md</font> rather than quietly worked "
            "around.", "body"),
    ]))

    story.append(KeepTogether([
        P("Larsen &amp; Toubro — close to neutral, and the one figure worth checking twice", "h2"),
        P(
            "L&amp;T's accrual ratio is +0.53% — PAT of ₹18,954 Crore against CFO of ₹16,741 Crore, a "
            "CFO/PAT ratio of 0.88x. At ₹4.5 lakh Crore of consolidated assets, a ratio this close to zero "
            "says profit and operating cash are broadly moving together at scale rather than diverging, "
            "which is the main thing this screen is looking for.", "body"),
        P(
            "Which PAT goes in the numerator matters more here than anywhere else in this screen, and it "
            "is worth being explicit about. L&amp;T's FY26 results report ₹16,084 Crore of profit "
            "attributable to owners and ₹18,954 Crore of total group profit, the difference being "
            "₹2,870 Crore of non-controlling interests. CFO and total assets are both group-level figures, "
            "so the numerator has to be group-level too. Using the attributable figure against group cash "
            "flow gives −0.16% and a CFO/PAT ratio of 1.04x — it flips the sign of the ratio and moves "
            "L&amp;T from third to fourth in the ranking. The group figure is used here, consistent with "
            "the other three companies, and the split is recorded in the source note on that row.", "body"),
        P(
            "One caveat worth stating plainly: FY26 PAT includes a one-time exceptional provision related "
            "to the new labour codes, disclosed on the same results page as the PAT figure used here. It "
            "is left inside the number rather than adjusted out, because the point of this screen is what "
            "was actually reported and actually converted to cash, not a normalised figure.", "body"),
    ]))

    story.append(KeepTogether([
        P("PSP Projects — best of the four, and worth a second look for why", "h2"),
        P(
            "PSP's accrual ratio is −9.82%, the most negative here — CFO of ₹323 Crore against a PAT of "
            "just ₹56 Crore, a CFO/PAT ratio of 5.8x. That's not a typo: PSP's FY26 profit was small next "
            "to its cash generation, mostly because FY25's PAT was itself depressed by a JV share-of-loss "
            "of ₹1.54 Crore that FY26 didn't repeat, and because PSP is also the smallest company in this "
            "set by a wide margin (₹3,089 Crore total assets vs. L&amp;T's ₹4.5 lakh Crore) — a swing that "
            "looks dramatic in ratio terms can come from a genuinely small base. A 5.8x CFO/PAT ratio "
            "deserves the same scrutiny as a bad one: it's either a real, durable strength in working-"
            "capital discipline, or a one-year number this large won't repeat. This screen doesn't have a "
            "second year of PSP data to tell which — that would need FY27's numbers.", "body"),
    ]))

    story.append(KeepTogether([
        Image(str(CHARTS / "02_cfo_vs_pat_fy26.png"), width=16 * cm, height=7.2 * cm),
        P("Figure 2. PAT vs CFO, FY26, independent scales per company — L&amp;T's absolute size would otherwise flatten the other three to invisible bars.", "caption"),
    ]))

    story.append(PageBreak())

    story.append(KeepTogether([
        Image(str(CHARTS / "03_balance_sheet_growth.png"), width=15.5 * cm, height=9.6 * cm),
        P("Figure 3. FY25 → FY26 total-assets growth, for context — the two companies growing fastest (PSP, NCC) sit at opposite ends of the accrual ranking, which is itself worth noting: fast growth alone doesn't predict earnings quality here.", "caption"),
    ]))

    story.append(KeepTogether([
        P("What this deliberately doesn't do", "h1"),
        P(
            "This is a 4-company, 1-year screen, not a sector-wide ranking system. It doesn't run a "
            "Modified Jones discretionary-accruals regression (needs 80+ companies per industry-year to "
            "estimate reliably — four is nowhere close), doesn't compute a Beneish M-score or Piotroski "
            "F-score, and doesn't backtest whether a high accrual ratio actually predicted anything in "
            "these companies' subsequent stock performance or restatements. All three were part of an "
            "earlier, more ambitious version of this project; they were cut, not hidden — a forced "
            "regression on four data points would have produced a number that looks precise and means "
            "nothing. See LIMITATIONS.md for the complete list, including what a larger version of this "
            "project would need to do them properly.", "body"),
    ]))

    story.append(Spacer(1, 10))
    story.append(P(
        "Data: company FY26 annual reports / results filings (see data/raw/source_manifest.md for URLs "
        "and file hashes). Code: src/accruals.py, using the indfin library's balance-sheet reconciliation "
        "module. Repository: github.com/theshaswat/epc-earnings-quality-screen.", "small"))

    doc.build(story)
    print(f"Written: {OUT_PDF}")


if __name__ == "__main__":
    build()
