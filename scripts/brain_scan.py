#!/usr/bin/env python3
"""Redraws the last year of GitHub contributions as an animated EEG 'brain scan'.
Standard library only. Usage: python scripts/brain_scan.py <username> <output.svg>"""
import re, sys, math, random, urllib.request
from datetime import date

USER = sys.argv[1] if len(sys.argv) > 1 else "Suman-Maitreya"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/brain-scan.svg"

def fetch(user):
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions",
                                 headers={"User-Agent": "brain-scan-bot"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    dates = dict(re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"\s+id="([^"]+)"', html))
    if not dates:  # attribute order fallback
        dates = {d: i for i, d in re.findall(r'id="(contribution-day-component-[^"]+)"[^>]*?data-date="([^"]+)"', html)}
        dates = {v: k for k, v in dates.items()} if dates else {}
    tips = dict(re.findall(r'for="(contribution-day-component-[^"]+)"[^>]*>([^<]*)</tool-tip>', html))
    days = []
    for d, cid in dates.items():
        m = re.match(r"(\d+) contribution", tips.get(cid, ""))
        days.append((d, int(m.group(1)) if m else 0))
    return sorted(days)

def stats(days):
    counts = [c for _, c in days]
    total = sum(counts)
    best = run = 0
    for c in counts:
        run = run + 1 if c else 0
        best = max(best, run)
    # current streak allowing today to be empty
    cur, seq = 0, counts[:]
    if seq and seq[-1] == 0: seq = seq[:-1]
    for c in reversed(seq):
        if not c: break
        cur += 1
    return total, max(counts or [0]), cur, best

def build(days):
    W, H, D = 1200, 300, 10
    x0, x1, base, top = 60, 1140, 190, 95
    n = max(len(days), 1)
    peak = max([c for _, c in days] + [1])
    rnd = random.Random(42)
    step = (x1 - x0) / n
    pts = []
    for i, (_, c) in enumerate(days):
        x = x0 + i * step
        noise = lambda: rnd.uniform(-1.6, 1.6)
        if c == 0:
            pts += [(x, base + noise()), (x + step / 2, base + noise())]
        else:
            a = (base - top) * (0.25 + 0.75 * math.log1p(c) / math.log1p(peak))
            pts += [(x, base + a * 0.18), (x + step * 0.35, base - a), (x + step * 0.7, base + a * 0.35)]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) if pts else f"M{x0},{base} L{x1},{base}"
    total, mx, cur, best = stats(days)
    # month ticks
    ticks, last = [], None
    for i, (ds, _) in enumerate(days):
        m = ds[:7]
        if m != last:
            ticks.append((x0 + i * step, date.fromisoformat(ds).strftime("%b"))); last = m
    font = "font-family=\"Consolas,'SF Mono',Menlo,'Courier New',monospace\""
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
         '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#0B1026"/><stop offset="55%" stop-color="#141A3F"/><stop offset="100%" stop-color="#2A1458"/></linearGradient>',
         '<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#FFFFFF" stroke-opacity="0.035"/></pattern>',
         '<linearGradient id="tr" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#38BDF8"/><stop offset="100%" stop-color="#C084FC"/></linearGradient>',
         '<filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="2.5"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
         f'<clipPath id="reveal"><rect x="0" y="0" width="0" height="{H}"><animate attributeName="width" values="{x0};{x1};{x1};{x0}" keyTimes="0;0.7;0.97;1" dur="{D}s" repeatCount="indefinite"/></rect></clipPath></defs>',
         f'<rect width="{W}" height="{H}" rx="16" fill="url(#bg)"/><rect width="{W}" height="{H}" rx="16" fill="url(#grid)"/>',
         f'<text x="36" y="46" {font} font-size="15" fill="#7DD3FC">brain_activity.eeg</text>',
         f'<text x="210" y="46" {font} font-size="13" fill="#94A3B8">// my last 365 days of GitHub commits, recorded as brainwaves · auto-updated daily</text>',
         f'<line x1="{x0}" y1="{base}" x2="{x1}" y2="{base}" stroke="#FFFFFF" stroke-opacity="0.06"/>',
         f'<path d="{d}" fill="none" stroke="#FFFFFF" stroke-opacity="0.07" stroke-width="1.2"/>',
         f'<path d="{d}" fill="none" stroke="url(#tr)" stroke-width="1.6" stroke-linejoin="round" clip-path="url(#reveal)" filter="url(#glow)"/>',
         f'<line y1="{top-10}" y2="{base+20}" stroke="#F0ABFC" stroke-width="1.5" stroke-opacity="0.8"><animate attributeName="x1" values="{x0};{x1};{x1};{x0}" keyTimes="0;0.7;0.97;1" dur="{D}s" repeatCount="indefinite"/><animate attributeName="x2" values="{x0};{x1};{x1};{x0}" keyTimes="0;0.7;0.97;1" dur="{D}s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.7;0.72;1" dur="{D}s" repeatCount="indefinite"/></line>']
    for x, lab in ticks[1:]:
        o.append(f'<text x="{x:.0f}" y="{base+40}" {font} font-size="11" fill="#64748B">{lab}</text>')
    items = [(f"{total}", "contributions"), (f"{mx}", "peak day"), (f"{cur}", "day streak"), (f"{best}", "longest streak")]
    for k, (v, lab) in enumerate(items):
        x = 60 + k * 270
        o.append(f'<text x="{x}" y="{H-26}" {font} font-size="20" font-weight="bold" fill="#E2E8F0">{v}</text>'
                 f'<text x="{x + 14 * len(v) + 10}" y="{H-26}" {font} font-size="13" fill="#94A3B8">{lab}</text>')
    o.append('</svg>')
    return "\n".join(o)

if __name__ == "__main__":
    days = fetch(USER)
    open(OUT, "w").write(build(days))
    print(f"wrote {OUT} from {len(days)} days")
