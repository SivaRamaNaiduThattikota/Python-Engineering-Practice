"""Check a built lesson page against its source.

    python build/verify.py m2_2

Prints every real output (examples and predict answers), timings and trace answers so the
prose can be checked against them, every "problem N" reference next to that problem's title,
and any `code` span from the source that does not appear exactly on the page.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
name = sys.argv[1]
lid = name.replace("_", "-")
page = (ROOT / "lessons" / f"{lid}.html").read_text(encoding="utf-8")
src = (ROOT / "src" / f"{name}.py").read_text(encoding="utf-8")
un = html.unescape

titles = [un(re.sub(r"<[^>]+>", "", t)) for t in re.findall(r"<h3>(.*?)</h3>", page)]
print("== problems")
for t in titles:
    print("  ", t)

print("== example outputs")
for lbl, out in re.findall(r'<span class="lbl">([^<]+)</span>(?:(?!<span class="lbl">).)*?<span class="ol">Output</span><pre>(.*?)</pre>', page, re.S):
    print(f"-- {lbl}\n{un(out)}")

print("== predict answers")
for block in re.split(r'<article class="prob"', page)[1:]:
    t = re.search(r"<h3>(.*?)</h3>", block)
    out = re.search(r'<span class="ol">Real output</span><pre>(.*?)</pre>', block, re.S)
    if out:
        print(f"-- {un(re.sub('<[^>]+>', '', t.group(1)))}\n{un(out.group(1))}")
    tm = re.findall(r"<tr><td>([A-Z])</td><td>([^<]+)</td></tr>", block)
    if tm:
        print(f"-- timing {un(re.sub('<[^>]+>', '', t.group(1)))}: {tm}")
    if 'data-type="trace"' in block:
        print(f"-- trace {un(re.sub('<[^>]+>', '', t.group(1)))}: {re.findall(r'data-a=\"([^\"]*)\"', block)}")

print("== problem references in the prose")
text = un(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|textarea)[\s\S]*?</\1>", "", page)))
by_num = {int(t.split(".")[0]): t for t in titles}
for n in sorted({int(x) for x in re.findall(r"problem (\d+)", text)}):
    ctx = re.findall(rf".{{0,60}}problem {n}\b.{{0,10}}", text)
    print(f"  problem {n} -> {by_num.get(n, 'MISSING')}")
    for c in ctx:
        print("      ...", re.sub(r"\s+", " ", c).strip())

flat = re.sub(r"\n\s+", " ", re.sub(r"(?m)^(term|lesson)\(.*$", "", src))
flat = re.sub(r'desc="[^"]*"', "", flat)
spans = set(re.findall(r"`([^`]+)`", flat))
codes = {un(c) for c in re.findall(r"<code>(.*?)</code>", page)}
miss = [s for s in spans if s.replace('\\"', '"') not in codes]
prose = re.sub(r"<(pre|script|textarea|svg)[\s\S]*?</\1>", "", page)
prose = un(re.sub(r"<[^>]+>", " ", re.sub(r"<code>.*?</code>", "", prose)))
print(f"== code spans: {len(spans)} checked, missing: {miss}")
print("== stray ** or backticks in prose:", re.findall(r".{0,20}(?:\*\*|`).{0,20}", prose))
