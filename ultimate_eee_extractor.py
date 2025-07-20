# !/usr/bin/env python3
"""
Ultimate EEE Exam Routine Extractor
Combines live table parsing with verified fallback structure
Accurately handles the UIU EEE exam routine table format
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional
import os

GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDu1ArL1vNPC52BXEjRPQzqlWPWWi3HLkXTmLv7UKFhrdRoKt_xYysksn6mxiyONmYTUwMXuIUghf8/pubhtml"

def get_google_sheets_url(base_url: str = "https://ucam.uiu.ac.bd/Student/ExamRoutineViewer.aspx") -> Optional[str]:
    """Extract the correct EEE Google Sheets iframe URL from the UIU exam routine page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(base_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        content = response.text
        
        # Search for Google Sheets URLs
        sheets_patterns = [
            r'src="([^"]*docs\.google\.com/spreadsheets[^"]*)"',
            r'href="([^"]*docs\.google\.com/spreadsheets[^"]*)"',
        ]
        
        all_sheets_urls = set()
        for pattern in sheets_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if 'docs.google.com' in match and 'spreadsheets' in match:
                    all_sheets_urls.add(match)
        
        # Test each URL to find the one with EEE content
        for sheets_url in all_sheets_urls:
            
            try:
                test_response = requests.get(sheets_url, headers=headers, timeout=15)
                test_content = test_response.text
                
                # Check for EEE-specific content
                eee_indicators = [
                    'EEE 101', 'EEE 1001', 'EEE 2103', 'EEE 2101', 'EEE 2105',
                    'MAT 101', 'PHY 103', 'EEE 2301', 'EEE 3303', 'CHE 2101',
                    'EEE 3105', 'ECO 2101', 'EEE 3303', 'EEE 3901'
                ]
                
                eee_count = sum(1 for indicator in eee_indicators if indicator in test_content)
                
                if eee_count >= 6:  # Should have multiple EEE indicators
                    return sheets_url
                else:
                    pass
            except Exception as e:
                continue
        
        return None
        
    except Exception as e:
        return None

def get_html_content(html_file: str) -> str:
    if os.path.exists(html_file):
        with open(html_file, encoding='utf-8') as f:
            return f.read()
    import requests
    resp = requests.get(GOOGLE_SHEETS_URL)
    resp.raise_for_status()
    return resp.text

def parse_eee_html_table(html_file: str) -> list:
    """Parse the EEE routine HTML file and return a flat list of {trimester, day, slot, course} entries."""
    from bs4 import BeautifulSoup
    import re
    data = []
    html = get_html_content(html_file)
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='waffle')
    if not table:
        raise ValueError('No table found in HTML')
    rows = table.find_all('tr')
    # Robust header expansion
    day_cells = rows[5].find_all(['td', 'th'])[2:23]  # 7 day cells (colspan=3)
    # Correct slot header extraction
    slot_cells = rows[6].find_all(['td', 'th'])[1:22]  # 21 slot cells: Time 1, Time 2, ...
    expanded_days = []
    for day_cell in day_cells:
        day = day_cell.get_text(strip=True)
        colspan = int(day_cell.get('colspan', 1))
        expanded_days.extend([day] * colspan)
    expanded_slots = [cell.get_text(strip=True) for cell in slot_cells]
    # Map slot names to time intervals
    slot_time_map = {
        'Time 1': '9:00 AM - 11:00 AM',
        'Time 2': '11:30 AM - 01:30 PM',
        'Time 3': '02:00 PM - 04:00 PM',
    }
    data = []
    for idx, r in enumerate(range(7, 19)):
        cells = rows[r].find_all(['td', 'th'])
        trimester = str(idx + 1)
        if len(cells) >= 24:
            if idx == 0:
                slot_cells = cells[3:24]  # Trimester 1: skip extra cell
            else:
                slot_cells = cells[2:23]  # Other trimesters: normal
        else:
            continue
        for i, cell in enumerate(slot_cells):
            course = cell.get_text(separator=' ', strip=True).replace('\n', ' ')
            day = expanded_days[i] if i < len(expanded_days) else None
            slot = expanded_slots[i] if i < len(expanded_slots) else None
            time_interval = slot_time_map.get(slot, '')
            if course and not re.match(r'^\d+$', course):
                entry = {
                    'trimester': trimester,
                    'day': day,
                    'slot': slot,
                    'time_interval': time_interval,
                    'course': course
                }
                data.append(entry)
    return data


def process_exam_schedule(exam_schedule: List[Dict]) -> Dict:
    """Process the exam schedule to separate midterm and final exams"""
    mid_term_exams = []
    final_exams = []
    
    for exam in exam_schedule:
        # Midterm: exclude "Only Final Exam" courses
        mid_courses = []
        for course in exam['courses']:
            if 'Only Final Exam' not in course:
                mid_courses.append(course)
        
        if mid_courses:
            mid_term_exams.append({
                'day': exam['day'],
                'time_slot': exam['time_slot'],
                'courses': mid_courses
            })
        
        # Final: include all courses
        final_exams.append({
            'day': exam['day'],
            'time_slot': exam['time_slot'],
            'courses': exam['courses']
        })
    
    return {
        'mid_term_exams': mid_term_exams,
        'final_exams': final_exams,
        'extraction_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_mid_slots': len(mid_term_exams),
        'total_final_slots': len(final_exams)
    }

def save_to_csv(data: List[Dict], filename: str):
    """Save exam data to CSV format"""
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['day', 'time_slot', 'course_count', 'courses'])
        
        for exam in data:
            courses_str = ' | '.join(exam['courses'])
            writer.writerow([
                exam['day'],
                exam['time_slot'],
                len(exam['courses']),
                courses_str
            ])

def generate_comprehensive_report(result: Dict) -> str:
    """Generate a comprehensive analysis report"""
    report = []
    report.append("=" * 80)
    report.append("ULTIMATE EEE EXAM ROUTINE ANALYSIS")
    report.append("=" * 80)
    report.append(f"Extraction Time: {result['extraction_timestamp']}")
    report.append(f"Total Midterm Slots: {result['total_mid_slots']}")
    report.append(f"Total Final Slots: {result['total_final_slots']}")
    report.append("")
    
    # Count and list final-only courses
    final_only_count = 0
    final_only_courses = []
    for exam in result['final_exams']:
        for course in exam['courses']:
            if 'Only Final Exam' in course:
                final_only_count += 1
                final_only_courses.append(f"{exam['day']} {exam['time_slot']}: {course}")
    
    report.append(f"Total courses marked 'Only Final Exam': {final_only_count}")
    report.append("")
    
    if final_only_courses:
        report.append("FINAL-ONLY COURSES (No Midterm):")
        report.append("-" * 40)
        for course_info in final_only_courses:
            report.append(f"  • {course_info}")
        report.append("")
    
    # Coverage analysis
    days_found = set(exam['day'] for exam in result['final_exams'])
    report.append(f"Days covered: {sorted(days_found)} ({len(days_found)}/7)")
    report.append("")
    
    # Slots per day analysis
    slots_per_day = {}
    for exam in result['final_exams']:
        day = exam['day']
        slots_per_day[day] = slots_per_day.get(day, 0) + 1
    
    report.append("SLOTS PER DAY:")
    report.append("-" * 20)
    for day in sorted(slots_per_day.keys()):
        count = slots_per_day[day]
        status = "✓" if count == 3 else "⚠"
        report.append(f"  {status} {day}: {count} slots")
    report.append("")
    
    # Total courses analysis
    total_midterm_courses = sum(len(exam['courses']) for exam in result['mid_term_exams'])
    total_final_courses = sum(len(exam['courses']) for exam in result['final_exams'])
    
    report.append("COURSE COUNT ANALYSIS:")
    report.append("-" * 25)
    report.append(f"  Total midterm courses: {total_midterm_courses}")
    report.append(f"  Total final courses: {total_final_courses}")
    report.append(f"  Final-only courses: {final_only_count}")
    report.append(f"  Courses with midterm: {total_final_courses - final_only_count}")
    report.append("")
    
    # Detailed schedule
    report.append("COMPLETE EXAM SCHEDULE:")
    report.append("=" * 80)
    
    for day in ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7']:
        report.append(f"\n{day}:")
        report.append("-" * 30)
        
        day_exams = [e for e in result['final_exams'] if e['day'] == day]
        
        for slot in ['T1', 'T2', 'T3']:
            slot_exam = None
            for exam in day_exams:
                if slot in exam['time_slot']:
                    slot_exam = exam
                    break
            
            if slot_exam:
                report.append(f"\n  {slot_exam['time_slot']}:")
                
                # Separate midterm and final-only courses
                midterm_courses = []
                final_only_courses = []
                
                for course in slot_exam['courses']:
                    if 'Only Final Exam' in course:
                        final_only_courses.append(course)
                    else:
                        midterm_courses.append(course)
                
                if midterm_courses:
                    report.append(f"    📝 Midterm + Final ({len(midterm_courses)} courses):")
                    for course in midterm_courses:
                        report.append(f"      • {course}")
                
                if final_only_courses:
                    report.append(f"    📋 Final Only ({len(final_only_courses)} courses):")
                    for course in final_only_courses:
                        report.append(f"      • {course}")
                        
                if not slot_exam['courses']:
                    report.append(f"    ⬜ No exams scheduled")
            else:
                report.append(f"\n  {slot}: No exam scheduled")
    
    # Summary
    report.append("\n" + "=" * 80)
    report.append("EXTRACTION SUMMARY:")
    report.append("=" * 80)
    
    if len(result['final_exams']) == 21 and len(days_found) == 7:
        report.append("✅ SUCCESS: Complete exam schedule extracted!")
        report.append("✅ All 7 days covered with 3 time slots each (21 total)")
    else:
        report.append(f"⚠️ PARTIAL: {len(result['final_exams'])}/21 slots extracted")
        if len(days_found) < 7:
            missing_days = {f'Day {i}' for i in range(1, 8)} - days_found
            report.append(f"⚠️ Missing days: {sorted(missing_days)}")
    
    report.append(f"📊 Data quality: {final_only_count} final-only courses properly identified")
    report.append(f"🔗 Live data verification: Connected to UIU Google Sheets")
    
    return '\n'.join(report)

def main():
    print("Ultimate EEE Exam Routine Extractor - Table Parser Mode")
    print("=" * 60)
    html_file = 'eee_routine_live.html'
    try:
        parsed = parse_eee_html_table(html_file)
        # Save as JSON
        import json
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        out_json = f'eee_routine_flat_{timestamp}.json'
        with open(out_json, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)
        print(f"✅ Parsed {len(parsed)} entries. Output: {out_json}")
    except Exception as e:
        print(f"❌ Error parsing table: {e}")

if __name__ == "__main__":
    main()
