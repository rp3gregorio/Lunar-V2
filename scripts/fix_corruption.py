#!/usr/bin/env python3
"""Fix corrupted notebook cells where source arrays have char-per-element."""
import json
import copy

NB_PATH = 'notebooks/01_apollo_validation.ipynb'

with open(NB_PATH) as f:
    nb = json.load(f)

fixed_count = 0
for i, cell in enumerate(nb['cells']):
    src = cell['source']
    n = len(src)
    if n < 10:
        continue
    avg_len = sum(len(s) for s in src) / n
    if avg_len < 3:
        # Corrupted: join chars back into text, then split into lines
        full_text = ''.join(src)
        lines = full_text.split('\n')
        # Rebuild source array with newlines (except last line)
        new_src = []
        for j, line in enumerate(lines):
            if j < len(lines) - 1:
                new_src.append(line + '\n')
            else:
                new_src.append(line)
        cell['source'] = new_src
        print(f'Fixed cell {i}: {n} chars -> {len(new_src)} lines')
        print(f'  First line: {new_src[0].rstrip()[:80]}')
        fixed_count += 1

print(f'\nTotal cells fixed: {fixed_count}')

# Verify the t_s and T_LUNAR fixes are still in place
for i, cell in enumerate(nb['cells']):
    text = ''.join(cell['source'])
    if '_t_s_sensor = t_sec_all[mask]' in text:
        print(f'Cell {i}: _t_s_sensor fix present ✓')
    if 't_s = t_sec_all[mask]' in text:
        print(f'Cell {i}: WARNING - old t_s = t_sec_all[mask] still present!')
    if '29.530589' in text:
        print(f'Cell {i}: synodic period fix present ✓')
    if '27.321661' in text:
        print(f'Cell {i}: WARNING - old sidereal period still present!')

with open(NB_PATH, 'w') as f:
    json.dump(nb, f, indent=1)
    f.write('\n')

print('\nNotebook saved.')
