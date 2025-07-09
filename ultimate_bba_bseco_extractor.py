#!/usr/bin/env python3
"""
Ultimate BBA, BBA in AIS, BSECO Exam Routine Extractor (Summer 2025)
Parses the BBA/BSECO routine table and outputs a flat list of {day, slot, time_interval, course_code, course_name}
"""
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRdMs34aiZHn81jF6pAcEZ979ZryLqF36H6ZD9BVNhWufNbO4CstNym8Qa0yiVVtjbP8kMyn5HbfISN/pubhtml"
HTML_FILE = "bba_bseco_routine.html"

slot_time_map = {
    'Morning (Time 1)': '9:00 AM - 11:00 PM',
    'Noon (Time 2)': '11:30 PM - 1:30 PM',
    'Afternoon (Time 3)': '2:00 PM - 4:00 PM',
}

def get_html_content(html_file: str) -> str:
    if os.path.exists(html_file):
        with open(html_file, encoding='utf-8') as f:
            return f.read()
    resp = requests.get(GOOGLE_SHEETS_URL)
    resp.raise_for_status()
    html = resp.text
    return html

def parse_bba_bseco_html_table(html: str) -> list:
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='waffle')
    if not table:
        raise ValueError('No table found in HTML')
    rows = table.find_all('tr')
    # Find the header row (with 'Day', 'Morning', 'Noon', 'Afternoon')
    header_row = None
    for row in rows:
        cells = row.find_all(['td', 'th'])
        for cell in cells:
            if 'day' in cell.get_text(strip=True).lower():
                header_row = row
                break
        if header_row:
            break
    if not header_row:
        header_row = rows[4] if len(rows) > 4 else None
        if not header_row:
            raise ValueError('Header row not found')
    start_idx = rows.index(header_row) + 1
    grouped = {}
    for r in range(start_idx, len(rows)):
        cells = rows[r].find_all(['td', 'th'])
        if len(cells) < 10:
            continue
        day_val = cells[1].get_text(strip=True)
        if not day_val.isdigit():
            continue
        day = day_val
        slot_defs = [
            ('Morning (Time 1)', 2, 3),
            ('Noon (Time 2)', 5, 6),
            ('Afternoon (Time 3)', 8, 9)
        ]
        for slot, code_idx, name_idx in slot_defs:
            course_code = cells[code_idx].get_text(strip=True)
            course_name = cells[name_idx].get_text(strip=True)
            if course_code:
                key = (day, slot, slot_time_map[slot])
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append({
                    'course_code': course_code,
                    'course_name': course_name
                })
    # Convert grouped to list of dicts
    result = []
    for (day, slot, time_interval), courses in grouped.items():
        result.append({
            'day': day,
            'slot': slot,
            'time_interval': time_interval,
            'courses': courses
        })
    return result

def main():
    html = get_html_content(HTML_FILE)
    data = parse_bba_bseco_html_table(html)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_file = f'bba_bseco_routine_flat_{ts}.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Extracted {len(data)} grouped slots. Output written to {out_file}")

if __name__ == '__main__':
    main() 