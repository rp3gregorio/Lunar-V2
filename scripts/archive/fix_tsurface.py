#!/usr/bin/env python3
"""Fix CE-4 and ChaSTE cells to use T_surface instead of T[0, :]."""
import json

NB_PATH = 'notebooks/01_apollo_validation.ipynb'

with open(NB_PATH) as f:
    nb = json.load(f)

fixes = {
    31: [  # CE-4 cell
        ('ce4_T_surface_peak = float(np.max(ce4_T[0, :]))',
         'ce4_T_surface_peak = float(np.max(ce4_out.T_surface))'),
        ('ce4_T_surface_min  = float(np.min(ce4_T[0, :]))',
         'ce4_T_surface_min  = float(np.min(ce4_out.T_surface))'),
    ],
    33: [  # ChaSTE cell
        ('chaste_T_surface_peak = float(np.max(chaste_T[0, :]))',
         'chaste_T_surface_peak = float(np.max(chaste_out.T_surface))'),
        ('chaste_T_surface_min  = float(np.min(chaste_T[0, :]))',
         'chaste_T_surface_min  = float(np.min(chaste_out.T_surface))'),
    ],
}

for cell_idx, replacements in fixes.items():
    src_text = ''.join(nb['cells'][cell_idx]['source'])
    for old, new in replacements:
        if old in src_text:
            src_text = src_text.replace(old, new)
            print(f'Cell {cell_idx}: {old[:50]} -> {new[:50]}')
        else:
            print(f'Cell {cell_idx}: NOT FOUND: {old[:50]}')
    # Rebuild source array
    lines = src_text.split('\n')
    new_src = []
    for j, line in enumerate(lines):
        if j < len(lines) - 1:
            new_src.append(line + '\n')
        else:
            new_src.append(line)
    nb['cells'][cell_idx]['source'] = new_src

with open(NB_PATH, 'w') as f:
    json.dump(nb, f, indent=1)
    f.write('\n')

print('\nDone. Notebook saved.')
