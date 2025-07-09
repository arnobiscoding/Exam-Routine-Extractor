#!/usr/bin/env python3
"""
Ultimate CSE Exam Routine Extractor
Robustly parses the CSE routine table (Summer 2025 format)
Outputs a flat list of {exam_type, day, slot, time_interval, course}
"""
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re
from collections import defaultdict
import os
import requests

GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8De-s8ewCelWhuSlfJBwp5Bgjg7oPYqXGIYAd8t72imOtU3X7XnJjibrhyQSR9oRLxDtnw6bkTWIv/pubhtml"

def get_html_content(html_file: str) -> str:
    if os.path.exists(html_file):
        with open(html_file, encoding='utf-8') as f:
            return f.read()
    resp = requests.get(GOOGLE_SHEETS_URL)
    resp.raise_for_status()
    return resp.text

def parse_cse_html_table(html_file: str) -> list:
    html = get_html_content(html_file)
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='waffle')
    if not table:
        raise ValueError('No table found in HTML')
    rows = table.find_all('tr')
    data = []
    # Time slot mapping for intervals
    slot_time_map = {
        'T1': '9:00 AM - 11:00 AM',
        'T2': '11:30 AM - 01:30 PM',
        'T3': '02:00 PM - 04:00 PM',
    }
    grouped = defaultdict(lambda: {'day': None, 'slot': None, 'time_interval': None, 'courses': []})
    r = 3  # Start from the first actual data row (skip header)
    while r < len(rows):
        if r + 2 >= len(rows):
            break
        block_day_row = rows[r]
        block_day_cells = block_day_row.find_all(['td', 'th'])
        if len(block_day_cells) < 4:
            r += 3
            continue
        day_label = block_day_cells[1].get_text(strip=True)
        slot = block_day_cells[2].get_text(strip=True)
        time = block_day_cells[3].get_text(strip=True)
        key = (day_label, slot, slot_time_map.get(slot, time))
        for col in range(4, len(block_day_cells)):
            course = block_day_cells[col].get_text(separator=' ', strip=True)
            if course and course not in {"Courses", "Day", "Time", "T1", "T2", "T3"} and course != day_label and not re.match(r"\d{1,2}(:|\.)\d{2} ?(-|–) ?\d{1,2}(:|\.)\d{2}", course):
                grouped[key]['day'] = day_label
                grouped[key]['slot'] = slot
                grouped[key]['time_interval'] = slot_time_map.get(slot, time)
                grouped[key]['courses'].append(course)
        for slot_offset in [1, 2]:
            cur_row = rows[r + slot_offset]
            cur_cells = cur_row.find_all(['td', 'th'])
            if len(cur_cells) < 3:
                continue
            slot = cur_cells[1].get_text(strip=True)
            time = cur_cells[2].get_text(strip=True)
            key = (day_label, slot, slot_time_map.get(slot, time))
            for col in range(3, len(cur_cells)):
                course = cur_cells[col].get_text(separator=' ', strip=True)
                if course and course not in {"Courses", "Day", "Time", "T1", "T2", "T3"} and course != day_label and not re.match(r"\d{1,2}(:|\.)\d{2} ?(-|–) ?\d{1,2}(:|\.)\d{2}", course):
                    grouped[key]['day'] = day_label
                    grouped[key]['slot'] = slot
                    grouped[key]['time_interval'] = slot_time_map.get(slot, time)
                    grouped[key]['courses'].append(course)
        r += 3
    return list(grouped.values())

def main():
    html_file = 'cse_routine_live.html'
    output_file = f'cse_routine_flat_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    data = parse_cse_html_table(html_file)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'✅ Parsed {len(data)} entries. Output: {output_file}')

if __name__ == '__main__':
    main()
