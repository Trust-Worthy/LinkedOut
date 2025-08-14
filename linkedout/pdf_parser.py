"""
pdf_parser.py

Extracts names, job titles, and companies from LinkedIn connection PDFs
saved via 'Ctrl+P → Save as PDF'. Uses pdfplumber for text extraction and
outputs structured data for export.

Part of the LinkedOut project — a 100% offline, privacy-focused
LinkedIn connection exporter for the FOSS community.

Author: Trust-Worthy
License: MIT (see LICENSE file for details)
"""
import pdfplumber
import csv
import re
import pdfplumber



# def extract_from_pdf(pdf_path: str) ->list[tuple[str, str, str, str]]:
#     """
#     Extracts LinkedIn connection data from a saved PDF.

#     Args:
#         pdf_path (str): Path to PDF saved via Ctrl+P → Save as PDF.

#     Returns:
#        list[tuple[str, str, str, str]]: (name, title, company, connected_date)
#     """
#     data = []

#     with pdfplumber.open(pdf_path) as pdf:
#         for page in pdf.pages:
#             text = page.extract_text()
#             if not text:
#                 continue

#             lines = [line.strip() for line in text.split('\n') if line.strip()]

#             i = 0
#             while i < len(lines):
#                 line = lines[i]

#                 # Skip metadata/header lines
#                 if line.startswith("Connections | LinkedIn") or \
#                    "connections" in line.lower() or \
#                    line.startswith("Sort by:"):
#                     i += 1
#                     continue

#                 # Skip page footer
#                 if line.endswith("PM") or "of" in line and "/" in line:
#                     i += 1
#                     continue

#                 # Name
#                 name = line
#                 i += 1

#                 # Gather all title/company lines until we hit 'Message'
#                 title_parts = []
#                 while i < len(lines) and lines[i] != "Message":
#                     title_parts.append(lines[i])
#                     i += 1
#                 title_company_str = " ".join(title_parts).strip()

#                 # Split into title and company if possible
#                 if ' @ ' in title_company_str:
#                     title, company = title_company_str.split(' @ ', 1)
#                 elif ' at ' in title_company_str:
#                     title, company = title_company_str.split(' at ', 1)
#                 else:
#                     title, company = title_company_str, ""

#                 # Skip 'Message'
#                 if i < len(lines) and lines[i] == "Message":
#                     i += 1

#                 # Connected date
#                 date_connected = ""
#                 if i < len(lines) and lines[i].startswith("Connected on"):
#                     date_connected = lines[i].replace("Connected on ", "").strip()
#                     i += 1

#                 data.append((name.strip(), title.strip(), company.strip(), date_connected))

#     return data

"""
pdf_parser.py

Parse LinkedIn connection PDFs (printed via Ctrl+P → Save as PDF) into
(Name, Title, Company, Date_connected) rows, fully offline.

Assumptions:
- Each connection appears as:
    Name
    [one or more title/company lines, possibly with "|" and multiple "@ ..."]
    [optional "Message" button text, sometimes inline]
    Connected on <Month DD, YYYY>
- PDF pages may include headers/footers like:
    "Connections | LinkedIn ...", "509 connections", "Sort by: ...",
    "1 of 1 8/13/25, 9:11 PM" — these are ignored.

Returns:list[tuple[str, str, str, str]]
"""


HEADER_PATTERNS = (
    re.compile(r"^Connections\s+\|\s+LinkedIn", re.I),
    re.compile(r"^\d+\s+connections$", re.I),
    re.compile(r"^Sort by:", re.I),
)
FOOTER_PATTERN = re.compile(r"^\d+\s+of\s+\d+\s+[\d/,: ]+(AM|PM)$", re.I)
CONNECTED_ON = re.compile(r"^Connected on\s+", re.I)


def _drop_header_footer_and_message(raw_lines:list[str]) ->list[str]:
    """Remove headers/footers and the 'Message' token (even when inline)."""
    cleaned:list[str] = []
    for line in raw_lines:
        s = line.strip()
        if not s:
            continue

        # Skip known headers
        if any(p.search(s) for p in HEADER_PATTERNS):
            continue
        # Skip page footer like "1 of 1 8/13/25, 9:11 PM"
        if FOOTER_PATTERN.search(s):
            continue

        # Remove standalone or inline 'Message' buttons
        s = re.sub(r"\bMessage\b", "", s).strip()
        if not s:
            continue

        cleaned.append(s)
    return cleaned


def _split_title_company(title_company: str) -> tuple[str, str]:
    """
    Split Title vs Company on the first ' @ ' (preferred) or ' at '.
    Keeps everything after the first split as Company (pipes included).
    """
    tc = re.sub(r"\s+", " ", title_company).strip()
    if not tc:
        return "", ""

    # Prefer ' @ ' since LinkedIn often uses '@ Company'
    if " @ " in tc:
        title, company = tc.split(" @ ", 1)
        return title.strip().strip("|").strip(), company.strip().strip("|").strip()

    # Fallback to ' at '
    if " at " in tc:
        title, company = tc.split(" at ", 1)
        return title.strip().strip("|").strip(), company.strip().strip("|").strip()

    # Couldn’t split → treat everything as Title
    return tc, ""


def extract_from_pdf(pdf_path: str) ->list[tuple[str, str, str, str]]:
    """
    Extract LinkedIn connections from a saved PDF.

    Args:
        pdf_path: Path to PDF.

    Returns:
       list of (name, title, company, date_connected).
    """
    rows:list[tuple[str, str, str, str]] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = [ln for ln in text.split("\n")]
            lines = _drop_header_footer_and_message(lines)

            i = 0
            while i < len(lines):
                # Skip accidental leading date lines
                if CONNECTED_ON.match(lines[i]):
                    i += 1
                    continue

                # Assume next non-date line is the Name
                name = lines[i].strip()
                i += 1

                # Accumulate title/company lines until a 'Connected on ...'
                buf:list[str] = []
                while i < len(lines) and not CONNECTED_ON.match(lines[i]):
                    buf.append(lines[i])
                    i += 1
                title_company_str = " ".join(buf).strip()
                title, company = _split_title_company(title_company_str)

                # Date (if present)
                date_connected = ""
                if i < len(lines) and CONNECTED_ON.match(lines[i]):
                    date_connected = re.sub(r"^Connected on\s+", "", lines[i]).strip()
                    i += 1

                # Basic sanity: if name looks like a header or empty, skip
                if not name or HEADER_PATTERNS[0].search(name) or FOOTER_PATTERN.search(name):
                    continue

                rows.append((name, title, company, date_connected))

    return rows


    
def write_to_csv(data, output_file='LinkedOut_connections_from_pdf.csv'):
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Title', 'Company', 'Date_connected'])
        writer.writerows(data)
        

pdf_file = '../test_connections.pdf'

parsed_data = extract_from_pdf(pdf_file)
write_to_csv(parsed_data)