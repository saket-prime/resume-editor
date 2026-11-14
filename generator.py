"""Minimal OOXML replacement: preserve every ZIP member except placeholder text."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
from xml.sax.saxutils import escape
from zipfile import ZipFile
from zoneinfo import ZoneInfo

TEMPLATE = Path(__file__).parent / 'templates' / 'offer.docx'
MONTHS = ('January February March April May June July August September October November December').split()

def today_india():
    return datetime.now(ZoneInfo('Asia/Kolkata')).date()

def format_date(day: date):
    suffix = 'th' if 11 <= day.day % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day.day % 10, 'th')
    return f'{day.day}{suffix} {MONTHS[day.month - 1]} {day.year}'

def salary_amount(ctc):
    try:
        amount = Decimal(str(ctc))
    except InvalidOperation as exc:
        raise ValueError('Enter a valid CTC amount.') from exc
    if not amount.is_finite() or not Decimal('0') < amount <= Decimal('1000000'):
        raise ValueError('CTC must be greater than zero and at most 1,000,000 (thousands).')
    return (amount * 1000 / 4).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

def format_salary(ctc):
    return f'{salary_amount(ctc):,.2f}'.rstrip('0').rstrip('.')

def build_docx(name, ctc, day=None, template=TEMPLATE):
    name = name.strip()
    if not name or len(name) > 120 or any(ord(c) < 32 for c in name):
        raise ValueError('Enter a name between 1 and 120 characters, without line breaks.')
    values = {'{{1}}': format_date(day or today_india()), '{{2}}': name, '{{3}}': format_salary(ctc)}
    counts = dict.fromkeys(values, 0)
    result = BytesIO()
    with ZipFile(template) as source, ZipFile(result, 'w') as target:
        for member in source.infolist():
            data = source.read(member.filename)
            if member.filename.startswith('word/') and member.filename.endswith('.xml'):
                xml = data.decode('utf-8')
                # Work per paragraph, even when Word splits a token across runs.
                def paragraph(match):
                    raw = match.group(0)
                    nodes = list(re.finditer(r'<w:t\b[^>]*>(.*?)</w:t>', raw, re.S))
                    text = ''.join(n.group(1) for n in nodes)
                    edits = []
                    for token, value in values.items():
                        for hit in re.finditer(re.escape(token), text):
                            counts[token] += 1
                            edits.append((hit.start(), hit.end(), escape(value)))
                    chunks = [n.group(1) for n in nodes]
                    offsets = []
                    offset = 0
                    for chunk in chunks:
                        offsets.append(offset)
                        offset += len(chunk)
                    for start, end, value in sorted(edits, reverse=True):
                        for i in range(len(chunks) - 1, -1, -1):
                            lo, hi = offsets[i], offsets[i] + len(nodes[i].group(1))
                            if lo < end and hi > start:
                                a, b = max(0, start-lo), min(hi-lo, end-lo)
                                chunks[i] = chunks[i][:a] + (value if lo <= start < hi else '') + chunks[i][b:]
                    for node, chunk in reversed(list(zip(nodes, chunks))):
                        raw = raw[:node.start(1)] + chunk + raw[node.end(1):]
                    return raw
                xml = re.sub(r'<w:p\b[^>]*>.*?</w:p>', paragraph, xml, flags=re.S)
                data = xml.encode('utf-8')
            target.writestr(member, data)
    if any(count != 1 for count in counts.values()):
        raise ValueError(f'Template must contain each placeholder exactly once: {counts}')
    return result.getvalue()

def libreoffice_path():
    configured = os.environ.get('LIBREOFFICE_PATH')
    candidates = [configured, shutil.which('libreoffice'), shutil.which('soffice'),
                  r'C:\Program Files\LibreOffice\program\soffice.exe']
    return next((p for p in candidates if p and Path(p).is_file()), None)

def to_pdf(docx):
    executable = libreoffice_path()
    if not executable:
        raise RuntimeError('PDF engine is unavailable. Install LibreOffice or deploy with the included packages.txt.')
    with tempfile.TemporaryDirectory(prefix='inkai-') as folder:
        root = Path(folder)
        source = root / 'offer.docx'
        source.write_bytes(docx)
        try:
            process = subprocess.run([executable, f'-env:UserInstallation={(root / "profile").as_uri()}',
                '--headless', '--convert-to', 'pdf:writer_pdf_Export', '--outdir', str(root), str(source)],
                capture_output=True, timeout=90, check=False)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError('PDF conversion took too long. Please try again.') from exc
        output = root / 'offer.pdf'
        if process.returncode != 0 or not output.exists():
            raise RuntimeError('PDF conversion failed. Check the LibreOffice installation and available memory.')
        data = output.read_bytes()
        if not data.startswith(b'%PDF-'):
            raise RuntimeError('The converter did not produce a valid PDF.')
        return data

def filename(name):
    return (re.sub(r'[^\w-]+', '_', name.strip(), flags=re.UNICODE).strip('_')[:80] or 'candidate') + '_offer.pdf'
