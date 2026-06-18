#!/usr/bin/env python3
"""Insert ZWSP at Thai word boundaries for proper line breaking in typst."""
import sys, re
from pythainlp.tokenize import word_tokenize

ZWSP = "​"

def has_thai(text):
    return bool(re.search(r'[฀-๿]', text))

def insert_zwsp(text):
    if not has_thai(text):
        return text
    parts = re.split(r'(`[^`]+`)', text)
    result = []
    for part in parts:
        if part.startswith('`'):
            result.append(part)
        elif has_thai(part):
            segments = re.split(r'([฀-๿]+)', part)
            for seg in segments:
                if has_thai(seg):
                    result.append(ZWSP.join(word_tokenize(seg, engine="newmm")))
                else:
                    result.append(seg)
        else:
            result.append(part)
    return ''.join(result)

if __name__ == "__main__":
    for fpath in sys.argv[1:]:
        with open(fpath, 'r') as f:
            for line in f:
                print(insert_zwsp(line), end='')
