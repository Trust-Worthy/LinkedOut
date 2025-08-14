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


def extract_from_pdf(pdf_path: str) -> list[str]:
    """
    Extracts text data from pdf file
    
    Args:
        pdf_path (str): path to pdf
    """
    
    data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            i = 0
            while i < len(lines) - 1:
                name = lines[i]
                title_company = lines[i + 1]
                date_connected = lines[i + 2]
                
                if 'at' in title_company:
                    title, company = title_company.split(' at ', 1)
                else:
                    title = title_company
                    company = ""
                
                data.append((name, title.strip(), company.strip()))
                
                i += 2 # Move to next person
    return data

    
def write_to_csv(data, output_file='LinkedOut_connections_from_pdf.csv'):
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Title', 'Company'])
        writer.writerows(data)
        

pdf_file = '../test_connections.pdf'

parsed_data = extract_from_pdf(pdf_file)
write_to_csv(parsed_data)