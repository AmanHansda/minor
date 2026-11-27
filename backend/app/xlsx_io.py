"""Small, dependency-free XLSX reader/writer for ChronosAI import templates."""
from __future__ import annotations

from io import BytesIO
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

HEADERS = {
    "Groups": ["code*", "department*", "program*", "year*", "section", "students*"],
    "Rooms": ["id*", "name*", "room_type*", "capacity*", "building", "department", "accessible"],
    "Faculty": ["id*", "name*", "max_hours_week*", "unavailable", "preferred"],
    "Allocations": ["course_code*", "course_name*", "cohort*", "instructor_id*", "allocation_type*", "hours*", "block_size", "accessible_room"],
    "Configuration": ["lunch_time*"],
}

SAMPLES = {
    "Groups": [["CSE-S3-A", "CSE", "B.Tech", "3rd Year", "A", 60]],
    "Rooms": [["LH1", "Lecture Hall 1", "LECTURE", 80, "A", "CSE", "TRUE"], ["LAB1", "Computing Lab", "LAB", 40, "B", "CSE", "TRUE"]],
    "Faculty": [["T1", "Dr. Sharma", 18, "Wed-2", "Mon-1, Tue-1"]],
    "Allocations": [["CS301", "Data Structures", "CSE-S3-A", "T1", "CLASS", 3, 1, "FALSE"]],
    "Configuration": [["13:00"]],
}

def _col(n):
    out = ""
    while n:
        n, r = divmod(n - 1, 26)
        out = chr(65 + r) + out
    return out

def _sheet_xml(rows):
    xml = []
    for r, values in enumerate(rows, 1):
        cells = []
        for c, value in enumerate(values, 1):
            if value is None:
                continue
            ref = f"{_col(c)}{r}"
            if isinstance(value, (int, float)):
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        xml.append(f'<row r="{r}">{"".join(cells)}</row>')
    return '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + ''.join(xml) + '</sheetData></worksheet>'

def build_template():
    """Return a valid Excel template containing every accepted import field."""
    sheets = [(name, [HEADERS[name]] + SAMPLES[name]) for name in HEADERS]
    instructions = [["ChronosAI Excel import instructions"], ["Fields marked * are mandatory."], ["Use one row per record. Delete sample rows before importing your own data."], ["room_type: LECTURE, CLASSROOM, or LAB."], ["allocation_type: CLASS, TUTORIAL, or LAB."], ["Unavailable/preferred slots use Mon-1, Tue-2 format separated by commas."], ["lunch_time is a 24-hour time on the hour from 09:00 through 16:00."]]
    sheets.append(("Instructions", instructions))
    content = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?><Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Default Extension=\"xml\" ContentType=\"application/xml\"/><Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"]
    for i in range(1, len(sheets)+1): content.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    content.append('</Types>')
    rels = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    wb_rels = ['<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    wb_sheets = []
    for i, (name, _) in enumerate(sheets, 1):
        wb_sheets.append(f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>')
        wb_rels.append(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>')
    wb_rels.append('</Relationships>')
    wb = '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + ''.join(wb_sheets) + '</sheets></workbook>'
    out = BytesIO()
    with ZipFile(out, 'w', ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ''.join(content)); z.writestr('_rels/.rels', rels)
        z.writestr('xl/workbook.xml', wb); z.writestr('xl/_rels/workbook.xml.rels', ''.join(wb_rels))
        for i, (_, rows) in enumerate(sheets, 1): z.writestr(f'xl/worksheets/sheet{i}.xml', _sheet_xml(rows))
    return out.getvalue()

def _text(cell, shared):
    kind = cell.get('t'); value = cell.findtext(NS + 'v', '')
    if kind == 's': return shared[int(value)] if value else ''
    if kind == 'inlineStr': return ''.join(cell.itertext())
    return value

def _rows(z, name, shared):
    root = ET.fromstring(z.read(name)); result = []
    for row in root.findall('.//' + NS + 'row'):
        values = {}
        for cell in row.findall(NS + 'c'):
            col = ''.join(ch for ch in cell.get('r', '') if ch.isalpha())
            values[col] = _text(cell, shared).strip()
        result.append([values.get(_col(i), '') for i in range(1, max([0] + [ord(k[0])-64 for k in values])+1)])
    return result

def parse_upload(blob):
    """Validate and convert a template-compatible XLSX into the manual input payload."""
    try: z = ZipFile(BytesIO(blob))
    except Exception as exc: raise ValueError('Upload a valid .xlsx file.') from exc
    try:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            shared = [''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(NS + 'si')]
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        targets = {r.get('Id'): 'xl/' + r.get('Target').lstrip('/') for r in rels.findall(REL + 'Relationship')}
        sheets = {s.get('name'): _rows(z, targets[s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')], shared) for s in wb.findall('.//' + NS + 'sheet')}
    except Exception as exc: raise ValueError('The workbook structure could not be read.') from exc
    errors = []
    records = {}
    for sheet, headers in HEADERS.items():
        rows = sheets.get(sheet)
        if not rows: errors.append(f'Missing required sheet: {sheet}.'); continue
        actual = [h.strip().lower() for h in rows[0]]
        if actual[:len(headers)] != headers: errors.append(f'{sheet}: expected columns: {", ".join(headers)}.'); continue
        records[sheet] = [dict(zip(headers, row + [''] * (len(headers)-len(row)))) for row in rows[1:] if any(v.strip() for v in row)]
    if errors: raise ValueError(' '.join(errors))
    def required(sheet):
        for n, row in enumerate(records[sheet], 2):
            missing = [h for h in HEADERS[sheet] if h.endswith('*') and not row.get(h, '').strip()]
            if missing: errors.append(f'{sheet} row {n}: missing {", ".join(missing)}.')
    for sheet in HEADERS: required(sheet)
    def num(value, label):
        try: return int(float(value))
        except ValueError: errors.append(f'{label} must be a whole number.'); return 0
    groups=[]; rooms=[]; faculty=[]; allocations=[]
    for r in records['Groups']: groups.append({'code':r['code*'], 'department':r['department*'], 'program':r['program*'], 'year':r['year*'], 'section':r['section'], 'students':num(r['students*'], 'Group students')})
    for r in records['Rooms']:
        typ=r['room_type*'].upper();
        if typ not in ('LECTURE','CLASSROOM','LAB'): errors.append(f"Room {r['id*']}: room_type must be LECTURE, CLASSROOM, or LAB.")
        rooms.append({'id':r['id*'], 'name':r['name*'], 'room_type':typ, 'capacity':num(r['capacity*'], 'Room capacity'), 'building':r['building'] or 'Main', 'department':r['department'] or 'General', 'accessible':r['accessible'].upper() != 'FALSE'})
    for r in records['Faculty']: faculty.append({'id':r['id*'], 'name':r['name*'], 'max_hours_week':num(r['max_hours_week*'], 'Faculty max_hours_week'), 'unavailable':[x.strip() for x in r['unavailable'].split(',') if x.strip()], 'preferred':[x.strip() for x in r['preferred'].split(',') if x.strip()]})
    group_ids={x['code'] for x in groups}; faculty_ids={x['id'] for x in faculty}
    for label, values in (("group code", group_ids), ("room ID", {x['id'] for x in rooms}), ("faculty ID", faculty_ids)):
        expected = len(groups) if label == "group code" else len(rooms) if label == "room ID" else len(faculty)
        if len(values) != expected: errors.append(f"Duplicate {label} values are not allowed.")
    for r in records['Allocations']:
        typ=r['allocation_type*'].upper()
        if typ not in ('CLASS','TUTORIAL','LAB'): errors.append(f"Allocation {r['course_code*']}: allocation_type must be CLASS, TUTORIAL, or LAB.")
        if r['cohort*'] not in group_ids: errors.append(f"Allocation {r['course_code*']}: unknown cohort {r['cohort*']}.")
        if r['instructor_id*'] not in faculty_ids: errors.append(f"Allocation {r['course_code*']}: unknown instructor {r['instructor_id*']}.")
        allocations.append({'id':f"{r['cohort*']}-{r['course_code*']}-{typ}", 'course':f"{r['course_code*']} {r['course_name*']}", 'cohort':r['cohort*'], 'instructor':r['instructor_id*'], 'students':next((x['students'] for x in groups if x['code']==r['cohort*']), 0), 'hours':num(r['hours*'], 'Allocation hours'), 'block_size':num(r['block_size'] or ('2' if typ=='LAB' else '1'), 'Allocation block_size'), 'room_type':'LAB' if typ=='LAB' else ('CLASSROOM' if typ=='TUTORIAL' else 'LECTURE'), 'accessible_room':r['accessible_room'].upper() == 'TRUE', 'allocation_type':typ})
    lunch=records['Configuration'][0]['lunch_time*'] if records['Configuration'] else ''
    if not __import__('re').match(r'^(09|10|11|12|13|14|15|16):00$', lunch): errors.append('Configuration lunch_time must be on the hour from 09:00 through 16:00 (for example 13:00).')
    if errors: raise ValueError(' '.join(errors))
    return {'class_groups':groups, 'rooms':rooms, 'instructors':faculty, 'requirements':allocations, 'config':{'lunch_time':lunch}}
