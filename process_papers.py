"""Process a CSV of papers to clean text, extract URLs, sort, and build an HTML page.

Steps implemented from the provided requirements:
1. Remove special characters from text fields.
2. Extract URLs from any column.
3. Perform multi-level sorting: presence of URL, presentation type order (oral, spotlight, poster),
   and author information.
4. Generate an HTML page listing paper titles with hyperlinks to their URLs.

The script is designed to work with CSV files that include at least a title column.
Optional columns such as type and authors are used when available.
"""
from __future__ import annotations

import argparse
import csv
import html
import re
import string
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


PRINTABLE = set(string.printable)
TYPE_PRIORITY: Dict[str, int] = {"oral": 0, "spotlight": 1, "poster": 2}
URL_PATTERN = re.compile(r'https?://[^\s)>"\']+')


def sanitize_text(value: str) -> str:
    """Remove non-printable or special characters while keeping standard punctuation."""
    return "".join(ch for ch in value if ch in PRINTABLE).strip()


def sanitize_row(row: Dict[str, str]) -> Dict[str, str]:
    return {key: sanitize_text(str(val)) for key, val in row.items()}


def find_column(row: Dict[str, str], candidates: Sequence[str]) -> str:
    """Find the first matching column name from candidates, case-insensitive."""
    lowered = {key.lower(): key for key in row.keys()}
    for name in candidates:
        if name in lowered:
            return lowered[name]
    return ""


def extract_urls(values: Iterable[str]) -> List[str]:
    urls = OrderedDict()
    for value in values:
        for match in URL_PATTERN.findall(value):
            # Strip trailing punctuation commonly attached to URLs.
            clean_url = match.rstrip(".,;:!?)\"]}")
            if clean_url and clean_url not in urls:
                urls[clean_url] = None
    return list(urls.keys())


def normalize_type(paper_type: str) -> str:
    return paper_type.strip().lower()


def type_rank(paper_type: str) -> int:
    normalized = normalize_type(paper_type) if paper_type else ""
    return TYPE_PRIORITY.get(normalized, len(TYPE_PRIORITY))


def build_sort_key(entry: Dict[str, str]) -> tuple:
    has_url_priority = 0 if entry["urls"] else 1
    type_priority = type_rank(entry.get("paper_type", ""))
    author_info = entry.get("authors", "") or entry.get("title", "")
    return (has_url_priority, type_priority, author_info.lower())


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [sanitize_row(row) for row in reader]


def process_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not rows:
        return []

    title_col = find_column(rows[0], ["title"])
    type_col = find_column(rows[0], ["type", "category", "presentation", "track"])
    author_col = find_column(rows[0], ["authors", "author", "author_info"])

    processed: List[Dict[str, str]] = []
    for row in rows:
        title = row.get(title_col, "Untitled") if title_col else row.get(next(iter(row)), "Untitled")
        paper_type = row.get(type_col, "") if type_col else ""
        authors = row.get(author_col, "") if author_col else ""

        urls = extract_urls(row.values())

        processed.append(
            {
                "title": title,
                "paper_type": paper_type,
                "authors": authors,
                "urls": urls,
            }
        )

    return sorted(processed, key=build_sort_key)


def generate_html(entries: List[Dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows_html = []
    for entry in entries:
        title = html.escape(entry["title"]) or "Untitled"
        paper_type = html.escape(entry.get("paper_type", ""))
        authors = html.escape(entry.get("authors", ""))

        if entry["urls"]:
            href = html.escape(entry["urls"][0])
            title_cell = f'<a href="{href}" target="_blank" rel="noopener noreferrer">{title}</a>'
        else:
            title_cell = title

        urls_display = "<br>".join(html.escape(url) for url in entry["urls"]) if entry["urls"] else ""

        rows_html.append(
            f"<tr><td>{title_cell}</td><td>{paper_type}</td><td>{authors}</td><td>{urls_display}</td></tr>"
        )

    rows_content = "\n      ".join(rows_html)

    body = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Paper Links</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; }}
    th {{ background: #f5f5f5; text-align: left; }}
    tr:nth-child(even) {{ background: #fafafa; }}
  </style>
</head>
<body>
  <h1>Paper Collection</h1>
  <p>Titles link to the first extracted URL for each paper when available.</p>
  <table>
    <thead>
      <tr><th>Title</th><th>Type</th><th>Authors</th><th>Extracted URLs</th></tr>
    </thead>
    <tbody>
      {rows_content}
    </tbody>
  </table>
</body>
</html>
"""

    output_path.write_text(body, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean paper metadata, extract URLs, and build an HTML page.")
    parser.add_argument("input_csv", type=Path, help="Path to the input CSV file containing paper metadata")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("papers.html"),
        help="Path for the generated HTML file (default: papers.html)",
    )
    args = parser.parse_args()

    rows = read_csv(args.input_csv)
    if not rows:
        raise SystemExit("Input CSV is empty or unreadable.")

    entries = process_rows(rows)
    generate_html(entries, args.output)
    print(f"Generated HTML with {len(entries)} papers at {args.output}")


if __name__ == "__main__":
    main()
