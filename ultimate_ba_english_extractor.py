#!/usr/bin/env python3
"""
Ultimate BA English Exam Routine Extractor
Parses the BA English routine table (Summer 2025 format)
Outputs a flat list of {day, slot, time_interval, course_code, course_name}
"""
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os
import requests

GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7Mauw19PwY7LNhFoDPwtvNO63tpYS89tyLMW06iSARp5xPA5u6VuaRqtDbt9SAD_obYdsIorcqq0C/pubhtml"

def get_html_content(html_file: str) -> str:
    if os.path.exists(html_file):
        with open(html_file, encoding='utf-8') as f:
            return f.read()
    resp = requests.get(GOOGLE_SHEETS_URL)
    resp.raise_for_status()
    html = resp.text
    # Do NOT cache to disk
    return html

def parse_ba_english_html_table(html_file: str) -> list:
    html_content = get_html_content(html_file)
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_='waffle')
    if not table:
        raise ValueError('No table found in HTML')
    rows = table.find_all('tr')
    # Slot/time mapping from screenshot/footer
    slot_time_map = {
        'Morning (Time 1)': '09:00 am - 11:00 am',
        'Noon (Time 2)': '11:30 am - 01:30 pm',
        'Afternoon (Time 3)': '02:00 pm - 04:00 pm',
    }
    slot_names = ['Morning (Time 1)', 'Noon (Time 2)', 'Afternoon (Time 3)']
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
        # fallback: use row index 4 (5th row), as in the HTML
        header_row = rows[4] if len(rows) > 4 else None
        if not header_row:
            raise ValueError('Header row not found')
    # Data starts after header row
    data = []
    start_idx = rows.index(header_row) + 1
    for r in range(start_idx, len(rows)):
        cells = rows[r].find_all(['td', 'th'])
        if len(cells) < 10:
            continue
        day_val = cells[1].get_text(strip=True)
        if not day_val.isdigit():
            continue
        day = day_val
        # Morning
        course_code = cells[2].get_text(strip=True)
        course_name = cells[3].get_text(strip=True)
        if course_code:
            data.append({
                'day': day,
                'slot': 'Morning (Time 1)',
                'time_interval': slot_time_map['Morning (Time 1)'],
                'course_code': course_code,
                'course_name': course_name
            })
        # Noon
        course_code = cells[5].get_text(strip=True)
        course_name = cells[6].get_text(strip=True)
        if course_code:
            data.append({
                'day': day,
                'slot': 'Noon (Time 2)',
                'time_interval': slot_time_map['Noon (Time 2)'],
                'course_code': course_code,
                'course_name': course_name
            })
        # Afternoon
        course_code = cells[8].get_text(strip=True)
        course_name = cells[9].get_text(strip=True)
        if course_code:
            data.append({
                'day': day,
                'slot': 'Afternoon (Time 3)',
                'time_interval': slot_time_map['Afternoon (Time 3)'],
                'course_code': course_code,
                'course_name': course_name
            })
    return data

def main():
    html_file = 'ba_english_routine.html'
    output_file = f'ba_english_routine_flat_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    data = parse_ba_english_html_table(html_file)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'✅ Parsed {len(data)} entries. Output: {output_file}')

if __name__ == '__main__':
    main() 