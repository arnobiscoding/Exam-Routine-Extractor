# Exam Routine Extractor

This project extracts exam routines from Google Sheets HTML exports (such as UIU EEE, CSE, BBA/BSECO, and BA English exam schedules) and outputs a flat, machine-readable list of exam slots with time intervals. It is designed to be extensible for other departments as well.

## Features
- Robustly parses complex Google Sheets HTML tables (merged headers, rowspans, etc.)
- Outputs a flat list of exam slots with time intervals and course information
- Handles edge cases and table structure changes
- Supports EEE, CSE, BBA/BSECO, and BA English routines (see scripts below)
- Easily extensible for other departments

## Requirements
- Python 3.7+
- `beautifulsoup4`
- `requests`

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Extract EEE Routine

1. Download the Google Sheets HTML export of the EEE routine (e.g., `eee_routine_live.html`).
2. Run the extractor:
   ```bash
   python ultimate_eee_extractor.py
   ```
3. Output: `eee_routine_flat_<timestamp>.json` — a flat list of `{trimester, day, slot, time_interval, course}` entries.

### 2. Extract CSE Routine

1. Download the Google Sheets HTML export of the CSE routine (e.g., `cse_routine_live.html`).
2. Run the extractor:
   ```bash
   python ultimate_cse_extractor.py
   ```
3. Output: `cse_routine_flat_<timestamp>.json` — a grouped list of `{day, slot, time_interval, courses: [ ... ]}` entries.

### 3. Extract BBA/BSECO Routine

1. Download the Google Sheets HTML export of the BBA/BSECO routine (e.g., `bba_bseco_routine.html`).
2. Run the extractor:
   ```bash
   python ultimate_bba_bseco_extractor.py
   ```
3. Output: `bba_bseco_routine_flat_<timestamp>.json` — a grouped list of `{day, slot, time_interval, courses: [ ... ]}` entries.

### 4. Extract BA English Routine

1. Download the Google Sheets HTML export of the BA English routine (e.g., `ba_english_routine.html`).
2. Run the extractor:
   ```bash
   python ultimate_ba_english_extractor.py
   ```
3. Output: `ba_english_routine_flat_<timestamp>.json` — a flat list of `{day, slot, time_interval, course_code, course_name}` entries.

## Output Formats
- **EEE:** `{trimester, day, slot, time_interval, course}`
- **CSE:** `{day, slot, time_interval, courses: [ ... ]}`
- **BBA/BSECO:** `{day, slot, time_interval, courses: [ ... ]}`
- **BA English:** `{day, slot, time_interval, course_code, course_name}`

## Extending for Other Departments
- Add a new extractor script following the same pattern.
- Adjust the parsing logic for the department's table structure.

## License
MIT