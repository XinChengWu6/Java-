# Paper CSV Processor

This repository contains a Python utility that cleans paper metadata stored in a CSV file, extracts URLs, sorts the entries, and produces an HTML page with hyperlinked titles.

## Features
- Removes non-printable/special characters from CSV text fields.
- Extracts URLs from any column, deduplicating them per paper.
- Sorts papers by presence of URL, preferred type order (oral → spotlight → poster), and author information.
- Generates a simple HTML table where the title links to the first extracted URL.

## Usage
1. Ensure you have Python 3.8+ available.
2. Run the script against your CSV file. For example, using the included sample data:

```bash
python process_papers.py papers_sample.csv --output papers.html
```

The generated `papers.html` can be opened in a browser to navigate to each paper's extracted URL.

## Input expectations
The script looks for case-insensitive column names:
- `title` for the paper title.
- `type`, `category`, `presentation`, or `track` for the presentation type.
- `authors`, `author`, or `author_info` for author details.

If a column is missing, that piece of data is left blank, and the script still produces an output row.
