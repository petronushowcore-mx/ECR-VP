import re
import os

path = os.path.join('frontend', 'src', 'App.jsx')
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

replacements = [
    ('\u0432\u201c\u0402', '\u2500'),
    ('\u0432\u2022\u0450', '\u2550'),
    ('\u0432\u0402\u201c', '\u2014'),
    ('\u0432\u0402\u2122', '\u2019'),
    ('\u0432\u045a\u201c', '\u2713'),
    ('\u0432\u2030\u00a5', '\u2265'),
    ('\u0432\u0459 ', '\u26a0 '),
    ('\u0432\u2020\u2019', '\u2192'),
    ('\ufeff', ''),
]
for broken, fixed in replacements:
    content = content.replace(broken, fixed)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

bad = re.findall(r'[\u0400-\u04ff]{2,}', content)
print(f'Fixed. Remaining Cyrillic clusters: {len(bad)}')
for b in bad[:10]:
    idx = content.find(b)
    ctx = content[max(0,idx-20):idx+len(b)+20]
    print(f'  {repr(b)} in: ...{repr(ctx)}...')
