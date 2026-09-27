# JP→EN Wiki Translation Agent

You are processing the remaining Japanese-content wiki files to English.

## Task
1. Run this script to find the top remaining JP files:
```python
import re, json, os
jp = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF00-\uFFEF]')
wiki_root = os.path.expanduser('~/wiki')
remaining = []
for root, dirs, files in os.walk(wiki_root):
    if 'raw/' in root: continue
    for f in files:
        if f.endswith('.md'):
            fp = os.path.join(root, f)
            with open(fp) as fh: content = fh.read()
            lines = content.split('\n')
            body_start = 0; fm_count = 0
            for i, line in enumerate(lines):
                if line.strip() == '---':
                    fm_count += 1
                    if fm_count == 2: body_start = i + 1; break
            if fm_count < 2: body_start = 0
            body = '\n'.join(lines[body_start:])
            body_jp = len(jp.findall(body))
            if body_jp > 0:
                rel_path = os.path.relpath(fp, wiki_root)
                remaining.append((rel_path, body_jp, fp))
remaining.sort(key=lambda x: -x[1])
# Take top 8
for p, j, fp in remaining[:8]:
    print(f"{p}|{j}|{fp}")
```

2. For each of the top 8 files, read it, translate ALL Japanese text in the body to English, write back.
3. CRITICAL: Skip YAML frontmatter (between --- markers). Only translate body content.
4. Preserve ALL markdown formatting, wikilinks [[...]], code blocks.
5. Commit: `cd ~/ai-topics && git add wiki/ && git commit -m "wiki: JP→EN batch — 8 files" && git push`
6. Report: number of files translated, total JP chars removed, remaining JP files count.
