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


def extract_from_pdf(pdf_path: str) -> list[tuple[str, str, str, str]]:
    """
    Extracts LinkedIn connection data from a saved PDF.

    Args:
        pdf_path (str): Path to PDF saved via Ctrl+P → Save as PDF.

    Returns:
        list[tuple[str, str, str, str]]: (name, title, company, connected_date)
    """
    data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = [line.strip() for line in text.split('\n') if line.strip()]

            i = 0
            while i < len(lines):
                line = lines[i]

                # Skip metadata/header lines
                if line.startswith("Connections | LinkedIn") or \
                   "connections" in line.lower() or \
                   line.startswith("Sort by:"):
                    i += 1
                    continue

                # Skip page footer
                if line.endswith("PM") or "of" in line and "/" in line:
                    i += 1
                    continue

                # Name
                name = line
                i += 1

                # Gather all title/company lines until we hit 'Message'
                title_parts = []
                while i < len(lines) and lines[i] != "Message":
                    title_parts.append(lines[i])
                    i += 1
                title_company_str = " ".join(title_parts).strip()

                # Split into title and company if possible
                if ' @ ' in title_company_str:
                    title, company = title_company_str.split(' @ ', 1)
                elif ' at ' in title_company_str:
                    title, company = title_company_str.split(' at ', 1)
                else:
                    title, company = title_company_str, ""

                # Skip 'Message'
                if i < len(lines) and lines[i] == "Message":
                    i += 1

                # Connected date
                date_connected = ""
                if i < len(lines) and lines[i].startswith("Connected on"):
                    date_connected = lines[i].replace("Connected on ", "").strip()
                    i += 1

                data.append((name.strip(), title.strip(), company.strip(), date_connected))

    return data

    
def write_to_csv(data, output_file='LinkedOut_connections_from_pdf.csv'):
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Title', 'Company', 'Date_connected'])
        writer.writerows(data)
        

pdf_file = '../test_connections.pdf'

parsed_data = extract_from_pdf(pdf_file)
write_to_csv(parsed_data)