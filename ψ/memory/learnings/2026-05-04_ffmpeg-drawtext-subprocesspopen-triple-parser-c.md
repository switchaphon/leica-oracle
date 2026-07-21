---
title: ffmpeg drawtext + subprocess.Popen triple-parser conflict: When Popen list mode 
tags: [ffmpeg, drawtext, subprocess, popen, escaping, strftime, alpine, python]
created: 2026-05-04
source: rrr --deep: nodered-simulator
---

# ffmpeg drawtext + subprocess.Popen triple-parser conflict: When Popen list mode 

ffmpeg drawtext + subprocess.Popen triple-parser conflict: When Popen list mode (no shell), ffmpeg filter option parser, and %{localtime} expansion parser all use colons as metacharacters, escaping is unsolvable. Solution: use expansion=strftime:text=%d/%m/%Y %X — eliminates the expansion parser layer entirely. %X is strftime shorthand for HH:MM:SS with zero colons in source. Cost of learning: 5 attempts, 2 hours, 8 MRs.

---
*Added via Oracle Learn*
