import json

path = '/Users/rp3gregorio/Documents/Lunar-V2/notebooks/01_apollo_validation.ipynb'
with open(path) as f:
    nb = json.load(f)

fixes = 0
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        ns, chg = [], False
        for line in cell['source']:
            if line.strip() == 't_s   = t_sec_all[mask]':
                line = line.replace('t_s   = t_sec_all[mask]',
                                    '_t_s_sensor = t_sec_all[mask]')
                chg = True
            elif 't_day = (t_s - t_s[0]) / 86400.0' in line.strip() and chg:
                line = line.replace('t_s', '_t_s_sensor')
            ns.append(line)
        if chg:
            cell['source'] = ns
            fixes += 1

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        ns = []
        for line in cell['source']:
            if '27.321661' in line and 'T_LUNAR' in line:
                line = line.replace('27.321661', '29.530589')
                line = line.replace('sidereal period', 'synodic period')
                line = line.replace('sidereal', 'synodic')
            ns.append(line)
        cell['source'] = ns

with open(path, 'w') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print('Fixed', fixes, 'cells with t_s shadowing + T_LUNAR')
