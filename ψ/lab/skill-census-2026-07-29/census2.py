#!/usr/bin/env python3
"""Fast skill-usage census: 4 capture regexes over each file, not 120 per-skill ones."""
import os, re, glob, json, sys
from collections import Counter, defaultdict
from datetime import datetime

S = os.path.expanduser('~/.claude/skills')
skills = sorted(d for d in os.listdir(S) if os.path.isdir(os.path.join(S, d)))
skillset = set(skills)

# Anchored CAPTURE patterns — pull the invoked name out, then intersect with real skills
RX = [
    re.compile(r'<command-name>/([A-Za-z0-9:_-]+)</command-name>'),
    re.compile(r'"skill"\s*:\s*"([A-Za-z0-9:_-]+)"'),
    re.compile(r'Launching skill: ([A-Za-z0-9:_-]+)'),
    re.compile(r'skills/([A-Za-z0-9:_-]+)/SKILL\.md'),
]

calls = Counter()
sessions = defaultdict(set)
last = {}
unknown = Counter()          # invoked but not a global skill (plugins etc.)

files = glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl'))
print(f"scanning {len(files)} files...", file=sys.stderr, flush=True)

for i, fp in enumerate(files, 1):
    if i % 50 == 0:
        print(f"  {i}/{len(files)}", file=sys.stderr, flush=True)
    try:
        text = open(fp, errors='ignore').read()
    except Exception:
        continue
    day = datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%Y-%m-%d')
    found = Counter()
    for rx in RX:
        for name in rx.findall(text):
            found[name] += 1
    for name, n in found.items():
        base = name.split(':')[-1]
        if name in skillset:
            key = name
        elif base in skillset:
            key = base
        else:
            unknown[name] += n
            continue
        calls[key] += n
        sessions[key].add(fp)
        if key not in last or day > last[key]:
            last[key] = day

rows = [{'skill': s, 'calls': calls.get(s, 0), 'sessions': len(sessions.get(s, ())),
         'last': last.get(s, '-')} for s in skills]
rows.sort(key=lambda r: (-r['calls'], r['skill']))

json.dump({'rows': rows,
           'unknown_top': unknown.most_common(25),
           'files_scanned': len(files)},
          open(os.path.join(os.path.dirname(__file__), 'census2.json'), 'w'), indent=1)
print("done", file=sys.stderr)
