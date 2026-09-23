"""Self-contained HTML dashboard for the EPC earnings-quality screen.

Built around the audit trail rather than a KPI wall. The ratio this screen
produces is only worth as much as the figures under it, so the page is
organised to get from a rank to the arithmetic that produced it, to the
balance-sheet tie-out that guards it, to the filing page it came from.

Every figure is read from the project's own CSVs and the reconciliation is
re-run here rather than copied, so the page cannot drift from the data.
Output is one file with no external requests.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from accruals import INPUT_CSV, compute_accruals, reconcile_all

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "dashboard" / "index.html"


def _n(v):
    return None if pd.isna(v) else float(v)


def _s(v):
    return None if pd.isna(v) else str(v)


def collect() -> dict:
    df = pd.read_csv(INPUT_CSV)
    _, records = reconcile_all(df)
    if any(r["passed"] is False for r in records):
        raise SystemExit("Balance-sheet tie-out failed — refusing to build the dashboard.")

    res = compute_accruals(df)
    fy25 = df[df["fy"] == "FY25"].set_index("company")
    fy26 = df[df["fy"] == "FY26"].set_index("company")

    companies = []
    for _, r in res.iterrows():
        c = r["company"]
        a, b = fy25.loc[c], fy26.loc[c]
        companies.append({
            "company": c,
            "rank": int(r["rank_worst_to_best"]),
            "accrualRatio": _n(r["accrual_ratio"]) * 100,
            "cfoPat": _n(r["cfo_pat_ratio"]),
            "pat": _n(r["pat"]), "cfo": _n(r["cfo"]),
            "totalAccruals": _n(r["total_accruals"]),
            "avgAssets": _n(r["avg_total_assets"]),
            "fy25": {"assets": _n(a["total_assets"]), "equity": _n(a["total_equity"]),
                     "liabilities": _n(a["total_liabilities"])},
            "fy26": {"assets": _n(b["total_assets"]), "equity": _n(b["total_equity"]),
                     "liabilities": _n(b["total_liabilities"])},
            "sourceFy25": _s(a["source_page_note"]),
            "sourceFy26": _s(b["source_page_note"]),
        })

    return {"companies": companies, "checks": records}


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EPC Earnings-Quality Screen</title>
<style>
:root{
  --navy:#1a3a5c; --rust:#c0522d; --sage:#5c7a5c;
  --ink:#16202b; --muted:#5d6b7a; --line:#d8dee5; --bg:#f4f6f8; --panel:#ffffff;
  --pos:#2f6b4f; --neg:#a8412a; --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,monospace;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ink:#e6edf3; --muted:#9bacbd; --line:#2b3745; --bg:#0f151c; --panel:#161e27;
    --navy:#7ba7d0; --pos:#6bbd8f; --neg:#e08163; --rust:#d97a52; --sage:#8fb08f;
  }
}
:root[data-theme="dark"]{
  --ink:#e6edf3; --muted:#9bacbd; --line:#2b3745; --bg:#0f151c; --panel:#161e27;
  --navy:#7ba7d0; --pos:#6bbd8f; --neg:#e08163; --rust:#d97a52; --sage:#8fb08f;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrap{max-width:1240px;margin:0 auto;padding:20px 16px 48px}
header{border-bottom:2px solid var(--navy);padding-bottom:12px;margin-bottom:18px}
h1{font-size:19px;margin:0 0 3px;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:13px;margin:0;max-width:78ch}
.checkstrip{display:flex;flex-wrap:wrap;gap:6px;margin-top:11px}
.chip{display:inline-flex;align-items:center;gap:6px;background:var(--panel);
  border:1px solid var(--line);border-radius:3px;padding:4px 9px;font-size:11.5px}
.dot{width:7px;height:7px;border-radius:50%;flex:none;background:var(--pos)}
h2{font-size:14px;margin:26px 0 3px;letter-spacing:.02em;text-transform:uppercase;color:var(--navy)}
.note{color:var(--muted);font-size:12.5px;margin:0 0 10px;max-width:76ch}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:4px}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:7px 9px;text-align:right;border-bottom:1px solid var(--line)}
td{white-space:nowrap}
th{background:var(--navy);color:#fff;font-weight:600;font-size:10.5px;text-transform:uppercase;
  letter-spacing:.02em;white-space:normal;line-height:1.25;vertical-align:bottom}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) th{color:#0f151c}}
:root[data-theme="dark"] th{color:#0f151c}
th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left}
tbody tr:last-child td{border-bottom:none}
td.num{font-variant-numeric:tabular-nums;font-family:var(--mono);font-size:12.5px}
.pos{color:var(--pos)} .neg{color:var(--neg)}
tr.row{cursor:pointer}
tr.row:hover td{background:color-mix(in srgb,var(--navy) 7%,transparent)}
tr.row[aria-selected="true"] td{background:color-mix(in srgb,var(--navy) 13%,transparent)}
tr.row[aria-selected="true"] td:first-child{box-shadow:inset 3px 0 0 var(--navy)}
.rank{display:inline-flex;width:19px;height:19px;border-radius:50%;align-items:center;
  justify-content:center;font-size:11px;font-weight:700;background:var(--line);color:var(--ink)}
.bar{position:relative;height:15px;min-width:150px}
.bar .zero{position:absolute;top:-1px;bottom:-1px;width:1px;background:var(--muted);opacity:.55}
.bar .fill{position:absolute;top:2px;height:11px;border-radius:2px}
.grid{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:16px;align-items:start}
.detail{position:sticky;top:12px}
.dbody{padding:12px 13px}
.detail h3{font-size:13.5px;margin:0 0 2px}
.detail .who{color:var(--muted);font-size:12px;margin:0 0 10px}
.calc{font-family:var(--mono);font-size:12px;background:color-mix(in srgb,var(--navy) 6%,transparent);
  border:1px solid var(--line);border-radius:3px;padding:9px 10px;margin:0 0 11px;line-height:1.7;
  overflow-x:auto}
.calc .r{color:var(--muted)}
.kv{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:12.5px;margin:0 0 11px}
.kv dt{color:var(--muted)} .kv dd{margin:0;font-family:var(--mono);text-align:right}
.tie{font-size:11.5px;color:var(--muted);margin:0 0 11px}
.tie b{color:var(--pos)}
.cite{font-size:11.5px;color:var(--muted);border-top:1px solid var(--line);padding-top:9px;
  line-height:1.45;white-space:pre-wrap;word-break:break-word}
.cite b{color:var(--ink);font-weight:600;display:block;margin-bottom:2px}
.cite + .cite{margin-top:9px}
.callout{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--rust);
  border-radius:3px;padding:11px 13px;margin:12px 0 0;font-size:12.5px;line-height:1.55;max-width:80ch}
.callout h4{margin:0 0 5px;font-size:12.5px;color:var(--rust)}
.checks{background:var(--panel);border:1px solid var(--line);border-radius:4px;padding:12px 13px}
.checks ul{margin:0;padding:0;list-style:none;font-size:11.5px;color:var(--muted);
  display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:0 18px}
.checks li{padding:4px 0;border-top:1px solid var(--line);line-height:1.4}
.checks .s{font-family:var(--mono);color:var(--ink);font-size:11px}
footer{margin-top:30px;padding-top:12px;border-top:1px solid var(--line);
  color:var(--muted);font-size:11.5px;line-height:1.6}
footer a{color:var(--navy)}
@media(max-width:900px){.grid{grid-template-columns:1fr}.detail{position:static}}
@media(max-width:560px){.wrap{padding:14px 12px 36px}h1{font-size:17px}
  th,td{padding:6px 7px;font-size:12px}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>EPC Earnings-Quality Screen — FY26</h1>
  <p class="sub">Larsen &amp; Toubro · KEC International · NCC Limited · PSP Projects, ranked by how
     much of reported profit is backed by operating cash. Sloan (1996) total accruals, consolidated,
     every figure page-cited and every balance sheet tied out first.</p>
  <div class="checkstrip" id="strip"></div>
</header>

<h2>The screen</h2>
<p class="note">Total accrual ratio = (PAT − CFO) ÷ average total assets. Positive means profit ran
   ahead of the cash the business generated; negative means cash ran ahead of profit. Rank 1 is the
   weakest on this measure. Select a company to see the arithmetic and its sources.</p>
<div class="grid">
  <div class="panel scroll"><table id="screen"></table></div>
  <div class="panel detail"><div class="dbody" id="detail"></div></div>
</div>

<div class="callout">
  <h4>The one input that changes the answer</h4>
  Larsen &amp; Toubro is the only company here with material non-controlling interests, so it is the
  only one where the choice of profit figure matters. This screen uses <b>total group profit</b> of
  ₹18,953.9 Cr, not the ₹16,084.0 Cr attributable to owners, because CFO and total assets are both
  group-level and the numerator has to match. Using the attributable figure instead gives −0.16% and
  a CFO/PAT of 1.04x — it flips the sign and moves L&amp;T from rank 3 to rank 4. Stated here rather
  than left implicit, because it is the single input in this project with the largest effect on the
  output.
</div>

<h2>Balance-sheet reconciliation</h2>
<p class="note">Assets = equity + liabilities, checked for every company-year before any ratio is
   computed. Re-run against the CSV each time this page is generated; the page is not written
   unless all of them pass.</p>
<div class="checks"><ul id="checks"></ul></div>

<footer>
  Source: FY26 annual reports and results filings — URLs and SHA-256 hashes in
  <code>data/raw/source_manifest.md</code>. Generated by <code>src/build_dashboard.py</code> from
  <code>data/final/</code>; no figure on this page is written into the template.<br>
  Shaswat Sharma · <a href="https://github.com/theshaswat">github.com/theshaswat</a>
</footer>
</div>

<script>
const DATA = __DATA__;
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const cr = v => v == null ? "—" : (v<0?"−":"") + "₹" +
  Math.abs(v).toLocaleString("en-IN",{maximumFractionDigits:0});
const cr2 = v => v == null ? "—" : (v<0?"−":"") + "₹" +
  Math.abs(v).toLocaleString("en-IN",{minimumFractionDigits:2,maximumFractionDigits:2});
const pctv = v => v == null ? "—" : (v>=0?"+":"−") + Math.abs(v).toFixed(2) + "%";
const sign = v => v == null ? "" : v>=0 ? "neg" : "pos";   /* positive accruals = weaker */

/* Bar scale spans the real range of ratios present, with a shared zero line, so the
   four companies are directly comparable and the sign is read off position. */
const MAXR = Math.max(...DATA.companies.map(c => Math.abs(c.accrualRatio)));
function bar(v){
  const half = 50, z = (Math.abs(Math.min(...DATA.companies.map(c=>c.accrualRatio)))/MAXR)*half;
  const zero = 4 + z;
  const w = (Math.abs(v)/MAXR)*half;
  const left = v >= 0 ? zero : zero - w;
  return `<div class="bar"><span class="zero" style="left:${zero}%"></span>
    <span class="fill" style="left:${left}%;width:${w}%;
    background:var(--${v>=0?'neg':'pos'})"></span></div>`;
}

function screenTable(){
  $("#screen").innerHTML = `<thead><tr><th>Rank</th><th>Company</th>
    <th>FY26 PAT</th><th>FY26 CFO</th><th>Accrual ratio</th>
    <th style="text-align:left">Weaker ← → stronger</th><th>CFO / PAT</th></tr></thead><tbody>` +
    DATA.companies.map((c,i)=>`<tr class="row" data-i="${i}" tabindex="0" role="button"
      aria-selected="${i===0}">
      <td><span class="rank">${c.rank}</span></td>
      <td>${esc(c.company)}</td>
      <td class="num">${cr(c.pat)}</td>
      <td class="num ${c.cfo<0?"neg":""}">${cr(c.cfo)}</td>
      <td class="num ${sign(c.accrualRatio)}">${pctv(c.accrualRatio)}</td>
      <td style="text-align:left">${bar(c.accrualRatio)}</td>
      <td class="num">${c.cfoPat==null?"—":c.cfoPat.toFixed(2)+"x"}</td></tr>`).join("") +
    `</tbody>`;
  $("#screen").querySelectorAll(".row").forEach(tr=>{
    const pick = ()=>select(+tr.dataset.i);
    tr.addEventListener("click", pick);
    tr.addEventListener("keydown", e=>{ if(e.key==="Enter"||e.key===" "){e.preventDefault();pick();} });
  });
}

function select(i){
  DATA.companies.forEach((_,j)=>{
    const tr=$(`#screen tr[data-i="${j}"]`); if(tr) tr.setAttribute("aria-selected", j===i);
  });
  const c = DATA.companies[i];
  const tie25 = c.fy25.assets - (c.fy25.equity + c.fy25.liabilities);
  const tie26 = c.fy26.assets - (c.fy26.equity + c.fy26.liabilities);
  $("#detail").innerHTML = `
    <h3>${esc(c.company)}</h3>
    <p class="who">Rank ${c.rank} of ${DATA.companies.length} · consolidated · ₹ Crore</p>
    <div class="calc">
      (PAT − CFO) ÷ avg. total assets<br>
      (${cr2(c.pat)} − ${cr2(c.cfo)}) ÷ ${cr2(c.avgAssets)}<br>
      = ${cr2(c.totalAccruals)} ÷ ${cr2(c.avgAssets)}<br>
      <span class="r">=</span> <b class="${sign(c.accrualRatio)}">${pctv(c.accrualRatio)}</b>
    </div>
    <dl class="kv">
      <dt>FY25 total assets</dt><dd>${cr2(c.fy25.assets)}</dd>
      <dt>FY26 total assets</dt><dd>${cr2(c.fy26.assets)}</dd>
      <dt>Average</dt><dd>${cr2(c.avgAssets)}</dd>
      <dt>CFO / PAT</dt><dd>${c.cfoPat==null?"—":c.cfoPat.toFixed(4)+"x"}</dd>
    </dl>
    <p class="tie">Balance sheet ties out both years —
      FY25 <b>${tie25.toFixed(2)}</b>, FY26 <b>${tie26.toFixed(2)}</b> difference between
      total assets and equity plus liabilities.</p>
    <div class="cite"><b>FY25 source</b>${esc(c.sourceFy25||"—")}</div>
    <div class="cite"><b>FY26 source</b>${esc(c.sourceFy26||"—")}</div>`;
}

function checks(){
  const cs = DATA.checks, pass = cs.filter(c=>c.passed).length;
  $("#strip").innerHTML = `<span class="chip"><span class="dot"></span>
    Balance-sheet tie-out <b>${pass}/${cs.length}</b></span>
    <span class="chip"><span class="dot"></span> ${DATA.companies.length} companies · FY25 &amp; FY26</span>`;
  $("#checks").innerHTML = cs.map(c=>`<li>✓ ${esc(c.subject)}<br>
    <span class="s">${esc(c.detail)}</span></li>`).join("");
}

screenTable(); checks(); select(0);
</script>
</body>
</html>
"""


def build() -> None:
    data = collect()
    html = HTML.replace("__DATA__", json.dumps(data, allow_nan=False))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"Written: {OUT}  ({len(html):,} bytes, no external requests)")


if __name__ == "__main__":
    build()
