"""Extract DEPATISnet textpdf content: HTML or an embedded searchable text PDF.

python test_textpdf_connection.py --browser --patent DD000000105384A5 --save-txt result.txt
Requires: requests beautifulsoup4 PyMuPDF playwright (browser mode).
Complete CAPTCHA manually. No PDF or browser cookies are exported.
"""
import argparse
from pathlib import Path
import re
from urllib.parse import urlsplit, parse_qs

import requests
import pymupdf
from bs4 import BeautifulSoup

BASE = "https://depatisnet.dpma.de/DepatisNet/depatisnet"


def extract_text(markup, selector=None):
    soup = BeautifulSoup(markup, "html.parser")
    if (soup.select_one("form#captchaform, input[name=verify_str]")
            or (soup.title and "Sicherheitsabfrage" in soup.title.get_text())):
        raise RuntimeError("CAPTCHA still present; complete it manually before continuing")
    for tag in soup.select("script, style, noscript, nav, header, footer, form, #kopf, #hauptnavblock, #pfad, .dpma-fuss-container"):
        tag.decompose()
    candidates = [selector] if selector else ["pre", "#inhaltscontainer", "main", "[role=main]", "body"]
    for css in candidates:
        nodes = soup.select(css)
        text = "\n\n".join(node.get_text("\n", strip=True) for node in nodes)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if text:
            return text, css
    raise RuntimeError("No text found in selected content area")


def validate_url(url, patent):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "depatisnet.dpma.de":
        raise RuntimeError("Unexpected page host: " + url)
    ids = parse_qs(parsed.query).get("docid", [])
    if ids and any(value.upper() != patent for value in ids):
        raise RuntimeError("Page points to a different patent: " + url)


def read_text_pdf(context, url, referer):
    response = context.request.get(url, headers={"Referer": referer},
                                   timeout=60000, max_redirects=0)
    try:
        if not response.ok:
            raise RuntimeError(f"Text PDF request failed: HTTP {response.status}")
        length = response.headers.get("content-length", "")
        if length.isdigit() and int(length) > 80 * 1024 * 1024:
            raise RuntimeError("Text PDF exceeds 80 MiB")
        data = response.body()
        if len(data) > 80 * 1024 * 1024:
            raise RuntimeError("Text PDF exceeds 80 MiB")
        if not data.startswith(b"%PDF-"):
            # Detect CAPTCHA rather than saving the access page as patent text.
            extract_text(data)
            raise RuntimeError("Text PDF URL returned a non-PDF page")
        return pdf_to_text(data), url, "embedded text PDF (memory only)"
    finally:
        response.dispose()


def pdf_to_text(data):
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        texts = [page.get_text("text", sort=True) for page in doc]
    if not any(text.strip() for text in texts):
        raise RuntimeError("PDF has no extractable text; scan/OCR review needed")
    print("Text PDF pages:", len(texts))
    for number, text in enumerate(texts, 1):
        print(f"Page {number}: {len(text.strip())} text characters")
    return "\n\n".join(f"--- PAGE {i} ---\n{text}" for i, text in enumerate(texts, 1))


def browser_text(url, args):
    try:
        from playwright.sync_api import sync_playwright, Error
    except ImportError as exc:
        raise RuntimeError("Install: python -m pip install playwright") from exc
    try:
        with sync_playwright() as driver:
            browser = driver.chromium.launch(channel=args.channel, headless=False)
            try:
                context = browser.new_context(accept_downloads=False)
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                print("Complete CAPTCHA manually in the opened browser window.")
                print("Wait until patent text is visible. Keep this window open.")
                if input("Then press Enter here (q to cancel): ").strip().lower() == "q":
                    raise RuntimeError("Cancelled")
                # Read the actual verified browser DOM; do not issue a new HTTP request.
                validate_url(page.url, args.patent)
                frame = page.main_frame
                if args.frame_url_contains:
                    matches = [f for f in page.frames if args.frame_url_contains in f.url]
                    if len(matches) != 1:
                        raise RuntimeError("Frame selection must match exactly one frame")
                    frame = matches[0]
                    validate_url(frame.url, args.patent)
                # The real page embeds a searchable *_text.pdf, not HTML text.
                pdf_frames = [f for f in page.frames
                              if urlsplit(f.url).path.lower().endswith("_text.pdf")]
                if not args.selector and (not args.frame_url_contains or
                                           urlsplit(frame.url).path.lower().endswith(".pdf")):
                    if len(pdf_frames) > 1:
                        raise RuntimeError("Multiple text PDFs found; select one using --frame-url-contains")
                    target = frame if args.frame_url_contains else (pdf_frames[0] if pdf_frames else None)
                    if target is not None:
                        validate_url(target.url, args.patent)
                        return read_text_pdf(context, target.url, page.url)
                markup = frame.content()
                if not args.selector and not args.frame_url_contains and len(page.frames) > 1:
                    print("Frames present; if text is missing use --frame-url-contains:")
                    for item in page.frames:
                        print(item.url)
                text, selected = extract_text(markup, args.selector)
                return text, frame.url, selected
            finally:
                browser.close()
    except Error as exc:
        raise RuntimeError("Browser error: " + str(exc)) from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patent", default="DD000000105384A5")
    parser.add_argument("--browser", action="store_true")
    parser.add_argument("--channel", choices=["msedge", "chrome"], default="msedge")
    parser.add_argument("--selector", help="Optional CSS selector for patent content")
    parser.add_argument("--frame-url-contains", help="Select a text frame by part of its URL")
    parser.add_argument("--preview-chars", type=int, default=6000)
    parser.add_argument("--save-txt", type=Path, help="Optional UTF-8 output; never overwrites")
    args = parser.parse_args()
    args.patent = args.patent.strip().upper()
    if not re.fullmatch(r"DD\d{12}[A-Z]\d?", args.patent):
        parser.error("Invalid patent identifier")
    if args.preview_chars < 0:
        parser.error("--preview-chars must be nonnegative")
    if args.save_txt and args.save_txt.exists():
        parser.error("TXT already exists; choose a new filename")
    url = BASE + "?window=1&space=main&content=treffer&action=textpdf&docid=" + args.patent
    try:
        if args.browser:
            text, actual_url, selected = browser_text(url, args)
        else:
            with requests.Session() as session:
                response = session.get(url, timeout=(15, 60))
                response.raise_for_status()
                validate_url(response.url, args.patent)
                text, selected = extract_text(response.content, args.selector)
                actual_url = response.url
        print("Source:", actual_url)
        print("Content selector:", selected)
        print("Extracted characters:", len(text))
        print("\nTEXT PREVIEW:\n" + text[:args.preview_chars])
        print("\nVerify the preview is patent text, not a site notice. PDF bytes, if used, remain in memory.")
        print("No automatic spelling or OCR quality verdict has been made.")
        if args.save_txt:
            with args.save_txt.open("x", encoding="utf-8") as output:
                output.write(text)
            print("TXT saved:", args.save_txt.resolve())
    except (RuntimeError, requests.RequestException, OSError, ValueError, EOFError, KeyboardInterrupt, pymupdf.FileDataError) as exc:
        print("STOP:", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
