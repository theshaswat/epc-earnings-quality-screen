"""Guards against published figures drifting from the data.

The L&T PAT correction in this project changed the sign of one accrual ratio
and reordered the ranking. Every chart, table and paragraph written before
that change kept the old number and still read as authoritative. These tests
re-read the CSVs and assert the README, the dashboard and the memo still
agree with them.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCREEN = pd.read_csv(ROOT / "data" / "final" / "accrual_screen.csv").set_index("company")
INPUTS = pd.read_csv(ROOT / "data" / "final" / "verified_inputs.csv")
README = (ROOT / "README.md").read_text()

COMPANIES = list(SCREEN.index)


@pytest.mark.parametrize("company", COMPANIES)
def test_readme_findings_row_matches_screen(company):
    row = next((l for l in README.splitlines()
                if f"| {company} |" in l and "₹" not in l), None)
    assert row, f"no README findings row for {company}"
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    pat, cfo, ratio, conv = cells[2], cells[3], cells[4], cells[5]
    f = lambda s: float(s.replace("−", "-").replace("+", "").replace(",", "")
                        .rstrip("%").rstrip("x"))
    assert f(pat) == pytest.approx(SCREEN.loc[company, "pat"], abs=0.1)
    assert f(cfo) == pytest.approx(SCREEN.loc[company, "cfo"], abs=0.1)
    assert f(ratio) == pytest.approx(SCREEN.loc[company, "accrual_ratio"] * 100, abs=0.01)
    assert f(conv) == pytest.approx(SCREEN.loc[company, "cfo_pat_ratio"], abs=0.01)


def test_lt_uses_group_profit_not_attributable():
    """The correction this project turned on: group PAT including
    non-controlling interests, to match group CFO and group assets."""
    lt = INPUTS[(INPUTS.company == "Larsen & Toubro") & (INPUTS.fy == "FY26")].iloc[0]
    assert lt["pat"] == pytest.approx(18953.88), (
        "L&T FY26 PAT is not the group figure — using profit attributable to owners "
        "against group CFO flips the sign of the accrual ratio")
    assert "non-controlling" in str(lt["source_page_note"]).lower(), (
        "the L&T row must record the NCI split it depends on")


def test_dashboard_matches_screen():
    html = (ROOT / "outputs" / "dashboard" / "index.html").read_text()
    data = json.loads(re.search(r"const DATA = (\{.*?\});\n", html, re.S).group(1))
    assert data["companies"]
    for c in data["companies"]:
        row = SCREEN.loc[c["company"]]
        assert c["accrualRatio"] == pytest.approx(row["accrual_ratio"] * 100)
        assert c["cfoPat"] == pytest.approx(row["cfo_pat_ratio"])
        assert c["rank"] == int(row["rank_worst_to_best"])


def test_dashboard_printed_arithmetic_is_self_consistent():
    """The detail panel prints (PAT − CFO) ÷ avg assets and then the result.
    The printed inputs must actually produce the printed result."""
    html = (ROOT / "outputs" / "dashboard" / "index.html").read_text()
    data = json.loads(re.search(r"const DATA = (\{.*?\});\n", html, re.S).group(1))
    for c in data["companies"]:
        assert (c["pat"] - c["cfo"]) / c["avgAssets"] * 100 == pytest.approx(
            c["accrualRatio"]), f"{c['company']}: printed arithmetic does not give printed ratio"


def test_balance_sheets_tie_out():
    bad = INPUTS[(INPUTS["total_assets"]
                  - (INPUTS["total_equity"] + INPUTS["total_liabilities"])).abs() > 1.0]
    assert bad.empty, f"balance sheet does not tie out:\n{bad[['company', 'fy']]}"


def test_every_input_row_carries_a_source_citation():
    missing = INPUTS[INPUTS["source_page_note"].isna()
                     | (INPUTS["source_page_note"].astype(str).str.strip() == "")]
    assert missing.empty, f"rows without a page citation:\n{missing[['company', 'fy']]}"


@pytest.mark.skipif(not (ROOT / "reports" / "methodology_memo.pdf").exists(),
                    reason="memo not built")
def test_memo_does_not_quote_the_superseded_lt_ratio():
    try:
        text = subprocess.run(
            ["pdftotext", str(ROOT / "reports" / "methodology_memo.pdf"), "-"],
            capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip("pdftotext unavailable")
    assert "+0.53%" in text, "memo does not quote L&T's corrected accrual ratio"
    # -0.16% may appear only where the memo explains the rejected alternative
    for para in text.split("\n\n"):
        if "−0.16%" in para or "-0.16%" in para:
            assert "attributable" in para.lower(), (
                "the superseded −0.16% appears without the explanation of why it is wrong")
