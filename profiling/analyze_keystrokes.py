#!/usr/bin/env python3
"""Per-keystroke QML cost from a qmlprofiler trace (.qtd) of the kicker dashboard.

For every key press it prints the time until the next key press ("gap"), the
QML time spent in between, and how many ItemGridView delegates were created.
A gap below 1 ms means the key was queued while the UI thread was blocked.

Usage: analyze_keystrokes.py trace.qtd
"""
import sys
import xml.etree.ElementTree as ET

QML_TYPES = ("Binding", "Creating", "Javascript", "HandlingSignal", "Compiling")

events = {}
ranges = []
for _, el in ET.iterparse(sys.argv[1], events=("end",)):
    if el.tag == "event":
        events[int(el.get("index"))] = {c.tag: (c.text or "") for c in el}
        el.clear()
    elif el.tag == "range":
        ranges.append((int(el.get("startTime")), int(el.get("duration") or 0),
                       int(el.get("eventIndex")), dict(el.attrib)))
        el.clear()
ranges.sort(key=lambda r: r[0])


def is_tile(i):
    e = events[i]
    return (e.get("type") == "Creating" and e.get("filename", "").endswith("ItemGridView.qml")
            and e.get("line") == "233")  # the ItemGridDelegate in ItemGridView's delegate


# merge overlapping QML ranges into busy spans, so nested events are not counted twice
spans = []
for s, d, i, _ in ranges:
    if not d or events[i].get("type") not in QML_TYPES:
        continue
    if spans and s <= spans[-1][1]:
        spans[-1][1] = max(spans[-1][1], s + d)
    else:
        spans.append([s, s + d])
tiles = [s for s, d, i, _ in ranges if is_tile(i)]

# input event type 0 = key press, data1 = Qt key code
presses = [(s, a) for s, d, i, a in ranges if events[i].get("type") == "Event" and a.get("type") == "0"]
rows = []
for n, (s, a) in enumerate(presses):
    nxt = presses[n + 1][0] if n + 1 < len(presses) else s + 1e9
    busy = sum(min(b, nxt) - a_ for a_, b in spans if s <= a_ < nxt)
    created = sum(1 for t in tiles if s <= t < nxt)
    k = int(a.get("data1"))
    rows.append((s, k, nxt - s, busy, created))
    key = chr(k) if 32 <= k < 127 else hex(k)
    print(f"{s / 1e9:8.3f}s  key {key:>9}  gap {(nxt - s) / 1e6:7.1f} ms  qml {busy / 1e6:6.1f} ms  tiles {created}")

active = [r for r in rows if r[4] > 0]
if rows and active:
    queued = sum(1 for r in rows if r[2] < 1e6)
    print(f"\n{len(rows)} keys, {queued} queued ({100 * queued / len(rows):.0f}%); "
          f"tiles/key avg {sum(r[4] for r in active) / len(active):.0f} max {max(r[4] for r in rows)}; "
          f"qml/key avg {sum(r[3] for r in active) / len(active) / 1e6:.0f} ms max {max(r[3] for r in rows) / 1e6:.0f} ms")
