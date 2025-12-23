#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試批次生成器的錯誤過濾邏輯"""

# 真實的錯誤訊息範例
test_line = '[FAIL] F121 Qatar FP2 - warnings.warn("`fastf1.api` will be considered private in future releases and " | events WARNING Correcting user input \'Qatar\' to \'Qatar Grand Prix\''

print('=' * 60)
print('測試 FastF1 警告過濾邏輯')
print('=' * 60)
print(f'\n測試訊息:\n{test_line}\n')

print('檢查條件:')
print(f'  1. [FAIL] in line: {("[FAIL]" in test_line)}')
print(f'  2. fastf1.api in line: {("fastf1.api" in test_line)}')
print(f'  3. warnings.warn in line: {("warnings.warn" in test_line)}')
print(f'  4. WARNING Correcting user input in line: {("WARNING Correcting user input" in test_line)}')
print(f'  5. events WARNING in line: {("events WARNING" in test_line)}')
print(f'  6. will be considered private in line: {("will be considered private in future releases" in test_line)}\n')

# 模擬當前的過濾邏輯
filtered_stdout_errors = []
if '[FAIL]' in test_line or '[ERROR]' in test_line:
    # 跳過 FastF1 相關的所有警告訊息
    if 'fastf1.api' in test_line and 'warnings.warn' in test_line:
        print('✅ 匹配條件 1: fastf1.api + warnings.warn → 應該跳過')
    elif 'WARNING Correcting user input' in test_line:
        print('✅ 匹配條件 2: WARNING Correcting user input → 應該跳過')
    elif 'events WARNING' in test_line:
        print('✅ 匹配條件 3: events WARNING → 應該跳過')
    elif 'will be considered private in future releases' in test_line:
        print('✅ 匹配條件 4: will be considered private → 應該跳過')
    else:
        filtered_stdout_errors.append(test_line.strip())
        print('❌ 未匹配任何跳過條件 → 會被保留為錯誤')

print(f'\n過濾後的錯誤列表: {filtered_stdout_errors}')
print(f'結果: 此訊息 {"被正確過濾 ✅" if not filtered_stdout_errors else "被誤判為錯誤 ❌"}')

# 測試真正的錯誤是否會被保留
print('\n' + '=' * 60)
print('測試真正的錯誤訊息')
print('=' * 60)
real_error = '[FAIL] F121 Qatar FP2 - FileNotFoundError: No such file or directory'
print(f'\n測試訊息:\n{real_error}\n')

filtered_real_errors = []
if '[FAIL]' in real_error or '[ERROR]' in real_error:
    if 'fastf1.api' in real_error and 'warnings.warn' in real_error:
        print('條件 1 不匹配')
    elif 'WARNING Correcting user input' in real_error:
        print('條件 2 不匹配')
    elif 'events WARNING' in real_error:
        print('條件 3 不匹配')
    elif 'will be considered private in future releases' in real_error:
        print('條件 4 不匹配')
    else:
        filtered_real_errors.append(real_error.strip())
        print('✅ 所有跳過條件都不匹配 → 正確保留為錯誤')

print(f'\n過濾後的錯誤列表: {filtered_real_errors}')
print(f'結果: 真正的錯誤 {"被正確保留 ✅" if filtered_real_errors else "被錯誤過濾 ❌"}')
