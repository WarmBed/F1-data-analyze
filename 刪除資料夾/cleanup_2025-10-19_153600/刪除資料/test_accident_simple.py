#!/usr/bin/env python3
"""簡化測試 - 驗證 Qt 導入和 API-ONLY 政策"""

import os
os.environ.setdefault('F1T_ALLOW_ACCIDENT_JSON_FALLBACK', '0')  # 明確禁用

from modules.gui.accident_analysis.accident_data_manager import AccidentDataManager

print("="*70)
print("Qt 導入測試")
print("="*70)
print("✅ 成功導入 AccidentDataManager（Qt 已正確導入）")

print("\n" + "="*70)
print("API-ONLY 政策測試")
print("="*70)

manager = AccidentDataManager()
print(f"本地 JSON 後備: {manager._allow_local_fallback}")
print(f"政策原因: {manager._fallback_policy_reason}")

if not manager._allow_local_fallback:
    print("✅ API-ONLY 政策已啟用（預設禁用本地 JSON 後備）")
else:
    print("❌ 警告: 本地 JSON 後備仍然啟用")

print("\n" + "="*70)
print("測試完成")
print("="*70)
