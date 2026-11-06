---
name: extraer-texto
description: Extract the text of an uploaded PDF, Word/Office file, or photo exactly as written (no reworded sentences, no added or dropped words) and present it as clean, readable Markdown. Use when the user uploads a document or image and asks to "extraer texto", "sacar el texto", transcribe it, convert it to text/Markdown, or copy its contents verbatim.
---

# Extraer texto verbatim

Goal: the user gets **every word of the document, unchanged**, laid out so it
reads in a sensible order. You may move blocks, add headings/tables/line
breaks, and join lines; you may **not** paraphrase, fix spelling, translate,
summarize, or "improve" anything.

## 1. Extract

Run (paths quoted; output goes to the scratchpad, never next to the upload):

```bash
python3 -I .claude/skills/extraer-texto/scripts/extract.py "<file>" [...] --out "<scratchpad>/extraer"
```

It prints one line per file saying which method it used. Per file it writes:

- `raw.txt` — reading-order text. **This is the word-for-word reference.**
- `layout.txt` (PDF) — same text with columns kept in place. Use it to see
  which label goes with which value (e.g. `PRICE   70.00`).
- `pages/*.png` — only for scanned pages with no text layer.

Why not MarkItDown alone: on PDFs it uses pdfminer, which in testing glued
words together and dropped whole fields (names, prices, confirmation codes).
`pdftotext` (poppler) kept all of them. MarkItDown is only the fallback for
formats pandoc cannot read (pptx, xlsx). Install if missing:
`apt-get install poppler-utils pandoc` / `pip install 'markitdown[all]'`.

**Scanned PDFs and photos:** the script runs tesseract OCR if installed. If it
says there is no OCR, open the image with the Read tool and transcribe it
yourself, character by character. Tell the user that part came from reading
the image, and flag anything you could not read as `[ilegible]` rather than
guessing.

## 2. Arrange (do not rewrite)

Read both `raw.txt` and `layout.txt`, then write `<name>.md`:

- Put label/value pairs back together (tables or `**Label:** value`).
- Join lines that a PDF broke mid-sentence; keep real paragraph breaks.
- Put side columns and boxes after the main text, under their own heading.
- Mark pages with `## Página N`. If pages repeat with small changes, still
  write each one in full, and add one `> Nota: ...` line saying what differs
  (e.g. a barcode number). These two are the only lines you may write in
  your own words; the verifier skips them.
- Keep the original language, capitals, accents, symbols (®, ©, ••••),
  numbers and dates exactly.
- Headings you add must use words already in the document. If you need a
  word that is not there, don't add it.
- Drop nothing, including boilerplate and legal fine print.
- Leave text that is only inside images (logos, barcodes) out, and say so.

## 3. Verify

```bash
python3 -I .claude/skills/extraer-texto/scripts/verify.py "<out>/<name>/raw.txt" "<out>/<name>.md"
```

It ignores Markdown markup and word order and lists words that were dropped,
added or changed. Fix the `.md` until it prints `OK`. The only acceptable
differences are ones you can explain (a word split by a line-end hyphen
rejoined, a hidden duplicate text layer removed); list those to the user.

## 4. Deliver

Give the user the `.md` (or paste it if short), plus one line per file: method
used, verification result, and anything not extracted (images, unreadable
parts). Save files where the user can open them (the scratchpad or the
working directory).
