#!/usr/bin/env python3
import sys
from pathlib import Path

speed_path = Path('modules/gui/lap_analysis/speed_analysis/speed_analysis_mdi.py')
throttle_path = Path('modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_mdi.py')
output_path = Path('tasks/throttle_vs_speed_char_diff.txt')

if not speed_path.exists():
    print('ERROR: speed file not found:', speed_path)
    sys.exit(2)
if not throttle_path.exists():
    print('ERROR: throttle file not found:', throttle_path)
    sys.exit(2)

speed_lines = speed_path.read_text(encoding='utf-8').splitlines()
throttle_lines = throttle_path.read_text(encoding='utf-8').splitlines()

max_lines = max(len(speed_lines), len(throttle_lines))

with output_path.open('w', encoding='utf-8') as out:
    out.write('Throttle vs Speed detailed char diff\n')
    out.write('='*80 + '\n')
    out.write(f'Speed file: {speed_path}\n')
    out.write(f'Throttle file: {throttle_path}\n')
    out.write(f'Lines: speed={len(speed_lines)}, throttle={len(throttle_lines)}\n')
    out.write('='*80 + '\n\n')

    total_identical = 0
    total_diff_lines = 0

    for i in range(max_lines):
        s = speed_lines[i] if i < len(speed_lines) else ''
        t = throttle_lines[i] if i < len(throttle_lines) else ''
        line_no = i+1
        if s == t:
            total_identical += 1
            continue
        total_diff_lines += 1
        out.write(f'LINE {line_no}\n')
        out.write('-'*40 + '\n')
        out.write('SPEED: ' + s + '\n')
        out.write('THROTTLE: ' + t + '\n')
        out.write('\n')
        # char level diff
        out.write('Char-level differences (index, speed_char, throttle_char)\n')
        out.write('Index | Speed (repr) | Throttle (repr) | Note\n')
        out.write('-'*80 + '\n')
        maxc = max(len(s), len(t))
        for ci in range(maxc):
            sc = s[ci] if ci < len(s) else ''
            tc = t[ci] if ci < len(t) else ''
            if sc != tc:
                # show visible repr
                def r(ch):
                    if ch == '':
                        return "<EOL>"
                    return repr(ch)
                out.write(f'{ci:5d} | {r(sc):12s} | {r(tc):14s} | {"diff"}\n')
        out.write('\n' + '='*80 + '\n\n')

    out.write('\nSUMMARY\n')
    out.write('-'*40 + '\n')
    out.write(f'Total lines compared: {max_lines}\n')
    out.write(f'Identical lines: {total_identical}\n')
    out.write(f'Different lines: {total_diff_lines}\n')

print('Comparison complete. Report written to', output_path)
sys.exit(0)
