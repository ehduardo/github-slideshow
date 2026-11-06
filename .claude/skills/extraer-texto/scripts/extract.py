#!/usr/bin/env python3
"""Extract text verbatim from PDFs, Office files and images.

Usage: extract.py <file> [<file> ...] --out <dir>

For each input it writes, into <dir>/<name>/:
  raw.txt      text in reading order (the word-for-word reference)
  layout.txt   text with the page's columns kept (PDF only)
  pages/*.png  page images, only when a PDF page has no text layer
It prints a short report per file, so you know which method worked.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def have(tool):
    return shutil.which(tool) is not None


def ocr_image(img: Path) -> str | None:
    if not have("tesseract"):
        return None
    r = run(["tesseract", str(img), "-", "-l", "spa+eng"])
    if r.returncode != 0:  # Spanish pack missing: retry with the default
        r = run(["tesseract", str(img), "-"])
    return r.stdout if r.returncode == 0 else None


def pdf(src: Path, out: Path) -> str:
    if not have("pdftotext"):
        sys.exit("pdftotext not found: install poppler-utils")
    raw = run(["pdftotext", "-enc", "UTF-8", str(src), "-"]).stdout
    layout = run(["pdftotext", "-enc", "UTF-8", "-layout", str(src), "-"]).stdout
    pages = raw.split("\f")
    empty = [i + 1 for i, p in enumerate(pages) if p.strip() == ""][: len(pages)]
    # The last split item after the final form feed is always empty.
    if pages and pages[-1].strip() == "":
        empty = [n for n in empty if n != len(pages)]

    note = f"{len(pages) - (1 if pages[-1].strip() == '' else 0)} page(s), text layer"
    if empty:
        pdir = out / "pages"
        pdir.mkdir(exist_ok=True)
        ocr_parts = []
        for n in empty:
            base = pdir / f"page-{n:03d}"
            run(["pdftoppm", "-r", "300", "-png", "-singlefile",
                 "-f", str(n), "-l", str(n), str(src), str(base)])
            text = ocr_image(base.with_suffix(".png"))
            if text is not None:
                ocr_parts.append(f"[page {n} - OCR]\n{text}")
        if ocr_parts:
            raw += "\n" + "\n".join(ocr_parts)
            note += f"; OCR on pages {empty}"
        else:
            note += (f"; pages {empty} have NO text (scanned). No OCR here: "
                     f"read the images in {pdir} visually")
    (out / "layout.txt").write_text(layout, encoding="utf-8")
    (out / "raw.txt").write_text(raw, encoding="utf-8")
    return note


def office(src: Path, out: Path) -> str:
    ext = src.suffix.lower()
    if ext in {".docx", ".odt", ".rtf", ".epub", ".html", ".htm"} and have("pandoc"):
        r = run(["pandoc", str(src), "-t", "gfm", "--wrap=none"])
        if r.returncode == 0:
            (out / "raw.txt").write_text(r.stdout, encoding="utf-8")
            return "pandoc (markdown, keeps headings, bold and lists)"
    if have("markitdown"):
        r = run(["markitdown", str(src)])
        if r.returncode == 0 and r.stdout.strip():
            (out / "raw.txt").write_text(r.stdout, encoding="utf-8")
            return "markitdown"
    sys.exit(f"no converter for {src.name}: install pandoc or 'markitdown[all]'")


def image(src: Path, out: Path) -> str:
    text = ocr_image(src)
    if text is None:
        return "no OCR here: read the image visually and transcribe it"
    (out / "raw.txt").write_text(text, encoding="utf-8")
    return "tesseract OCR (check numbers and accents by eye)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    for src in args.files:
        out = args.out / src.stem
        out.mkdir(parents=True, exist_ok=True)
        ext = src.suffix.lower()
        if ext == ".pdf":
            note = pdf(src, out)
        elif ext in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".heic"}:
            note = image(src, out)
        else:
            note = office(src, out)
        raw = out / "raw.txt"
        words = len(raw.read_text(encoding="utf-8").split()) if raw.exists() else 0
        print(f"{src.name}: {note}; {words} words -> {out}")


if __name__ == "__main__":
    main()
