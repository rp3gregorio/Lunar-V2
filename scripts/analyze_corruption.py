#!/usr/bin/env python3
"""Analyze notebook corruption and compare with git HEAD."""
import json
import subprocess

with open('notebooks/01_apollo_validation.ipynb') as f:
    nb_bad = json.load(f)

git_content = subprocess.check_output(
    ['git', 'show', 'HEAD:notebooks/01_apollo_validation.ipynb']
)
nb_good = json.loads(git_content)

corrupted = []
for i, cell in enumerate(nb_bad['cells']):
    src = cell['source']
    n_lines = len(src)
    avg_len = sum(len(s) for s in src) / max(n_lines, 1)
    if avg_len < 3 and n_lines > 10:
        corrupted.append(i)

print(f'Corrupted cell indices (0-based): {corrupted}')
print(f'Total cells in bad notebook: {len(nb_bad["cells"])}')
print(f'Total cells in good (git HEAD): {len(nb_good["cells"])}')
print()

# Show first lines of each good cell for mapping
for i in corrupted:
    if i < len(nb_good['cells']):
        gsrc = nb_good['cells'][i]['source']
        first = gsrc[0].strip() if gsrc else '<empty>'
        print(f'  Good cell {i}: type={nb_good["cells"][i]["cell_type"]}, '
              f'lines={len(gsrc)}, first: {first[:80]}')

    bsrc = nb_bad['cells'][i]['source']
    # Reconstruct the original text from char-per-line
    full_text = ''.join(bsrc)
    first_line = full_text.split('\n')[0] if full_text else '<empty>'
    print(f'  Bad  cell {i}: type={nb_bad["cells"][i]["cell_type"]}, '
          f'chars={len(bsrc)}, reconstructed first: {first_line[:80]}')
    print()

# Check if the non-corrupted cells differ between bad and good
print('--- Non-corrupted cell comparison ---')
for i, cell in enumerate(nb_bad['cells']):
    if i in corrupted:
        continue
    if i < len(nb_good['cells']):
        bad_text = ''.join(cell['source'])
        good_text = ''.join(nb_good['cells'][i]['source'])
        if bad_text != good_text:
            print(f'  Cell {i}: DIFFERS (bad={len(cell["source"])} lines, '
                  f'good={len(nb_good["cells"][i]["source"])} lines)')
