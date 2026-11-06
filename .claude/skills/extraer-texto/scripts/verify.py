#!/usr/bin/env python3
"""Check that a cleaned-up Markdown file kept every word of the source.

Usage: verify.py <raw.txt> <final.md>

Markdown markup (#, *, |, -, >, links) is ignored (so is a literal *), and so is word order.
It compares the words themselves and lists any word that was dropped,
added or changed. Lines you add on purpose are skipped in the final file:
page headings "## Página N" and notes starting "> Nota:".
Exit code 0 = same words, 1 = differences.
"""
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

MARKUP = re.compile(r"(\*\*|__|<u>|</u>|<br>|`|^#+\s|^>\s?|^\s*[-*+]\s|^\s*\d+\.\s|\||^-{3,}$|:?-{3,}:?)", re.M)


def words(text: str) -> Counter:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\\|", " ").replace("\f", " ")
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # [label](url) -> label
    text = MARKUP.sub(" ", text)
    text = text.replace("*", "")  # emphasis marks, even mid-word like (01/*2024
    text = re.sub(r"(?<!\w)_+|_+(?!\w)", " ", text)
    text = text.replace("\\", "")
    return Counter(t for t in text.split() if re.search(r"\w", t))


def main():
    raw, final = (Path(p).read_text(encoding="utf-8") for p in sys.argv[1:3])
    final = re.sub(r"^(## Página \d+|> Nota:.*)$", "", final, flags=re.M)
    a, b = words(raw), words(final)
    missing, added = a - b, b - a
    total = sum(a.values())
    print(f"source words: {total} | final words: {sum(b.values())}")
    if not missing and not added:
        print("OK: every word kept, none added")
        return 0
    if missing:
        print(f"MISSING in final ({sum(missing.values())}):",
              ", ".join(f"{w} x{n}" if n > 1 else w for w, n in missing.most_common()))
    if added:
        print(f"ADDED in final ({sum(added.values())}):",
              ", ".join(f"{w} x{n}" if n > 1 else w for w, n in added.most_common()))
    return 1


if __name__ == "__main__":
    sys.exit(main())
