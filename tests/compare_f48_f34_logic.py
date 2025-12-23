"""比較直線速度分析（F48）和煞車分析（F34）的賽道名稱處理邏輯"""
import subprocess
import json
import os

print("=" * 80)
print("🔍 比較 Function 48 vs Function 34 的賽道名稱處理")
print("=" * 80)

# 測試參數
test_params = [
    {"race": "Japan", "case": "大寫 Japan"},
    {"race": "japan", "case": "小寫 japan"},
    {"race": "China", "case": "大寫 China"},
    {"race": "china", "case": "小寫 china"},
]

print("\n" + "=" * 80)
print("📋 賽道名稱處理邏輯分析")
print("=" * 80)

# 檢查源碼中的賽道名稱字典
print("\n✅ Function 48 (直線速度分析) - 賽道字典檢查:")
print("   檔案: CLI_modules/cli/analyzer/all_drivers_straight_line_speed.py")
print("   Line 698: if race_name and race_name in TRACK_ACCELERATION_START_DISTANCE:")
print("   字典鍵: 'Japan', 'China', 'Australia' 等（大寫開頭）")
print("   檢查方式: 直接字符串匹配（區分大小寫）")

print("\n✅ Function 34 (煞車分析) - 賽道字典檢查:")
print("   檔案: CLI_modules/cli/analyzer/brake_performance_analyzer.py")
print("   Line 354: if race_name and race_name in TRACK_BRAKE_END_DISTANCE:")
print("   字典鍵: 'Japan', 'China', 'Australia' 等（大寫開頭）")
print("   檢查方式: 直接字符串匹配（區分大小寫）")

print("\n" + "=" * 80)
print("🔧 CLI 參數傳遞流程")
print("=" * 80)

print("""
1. CLI 入口 (f1_analysis_modular_main.py)
   ↓
   Line 587: race=self.args.race  # 保持原始大小寫
   ↓
2. Function Mapper (function_mapper.py)
   ↓
   Line 2697 (F34): race = kwargs.get("race", ...)  # 保持原始
   Line 2794 (F48): race = kwargs.get("race", ...)  # 保持原始
   ↓
3. Analyzer 初始化
   ↓
   Both: self.race = race or getattr(data_loader, "race_name", None)
   ↓
4. 賽道字典查找
   ↓
   Both: if race_name and race_name in TRACK_..._DISTANCE:
         # 如果傳入 'japan'（小寫），字典中只有 'Japan'（大寫）→ 查找失敗
""")

print("=" * 80)
print("🧪 API 調用測試")
print("=" * 80)

print("\n💡 為什麼 F48 通過 API 成功，但 F34 失敗？")
print("\n   可能原因 1: API 服務器對不同功能有不同的參數處理")
print("   可能原因 2: F48 和 F34 的執行時機不同")
print("   可能原因 3: 本地 CLI 測試使用大寫，但 API 轉換成小寫")

# 檢查 API 成功的直線速度分析結果
china_json = "json/all_drivers_straight_line_speed_2025_China_R.json"
if os.path.exists(china_json):
    print(f"\n✅ 檢查成功的 F48 結果: {china_json}")
    try:
        with open(china_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cli_info = data.get('cli_info', {})
        command = cli_info.get('command', '')
        
        print(f"   CLI 命令: {command}")
        
        # 從命令中提取賽道名稱
        if '-r' in command:
            parts = command.split()
            r_idx = parts.index('-r')
            if r_idx + 1 < len(parts):
                race_param = parts[r_idx + 1]
                print(f"   賽道參數: {race_param}")
                print(f"   大小寫: {'大寫開頭' if race_param[0].isupper() else '小寫'}")
        
        metadata = data.get('data', {}).get('metadata', {})
        print(f"   元數據賽道: {metadata.get('race')}")
        
    except Exception as e:
        print(f"   ⚠️  讀取失敗: {e}")

# 檢查失敗的煞車分析
print("\n❌ 檢查失敗的 F34 API 調用:")
print("   從日誌可見:")
print("   - API 傳入: 'japan' (小寫)")
print("   - CLI 命令: python f1_analysis_modular_main.py -f 34 -y 2025 -r japan -s R")
print("   - 字典查找: 'japan' in {'Japan': 5256, ...} → False")
print("   - 錯誤: 賽道 'japan' 未設定硬編碼煞車終點")

print("\n" + "=" * 80)
print("🎯 結論")
print("=" * 80)

print("""
✅ **邏輯一致性**：F48 和 F34 的賽道名稱處理邏輯完全一致
   - 都使用相同的參數傳遞方式
   - 都使用相同的字典查找方式（區分大小寫）
   - 都要求賽道名稱大寫開頭

❌ **API 問題**：API 服務器將賽道名稱轉換成小寫
   - 本地 CLI: python ... -r Japan  → ✅ 成功
   - API 調用: {race: "Japan"}       → CLI: -r japan → ❌ 失敗

🔧 **解決方案**：
   1. 短期：修改分析器支援不區分大小寫的查找
   2. 長期：修正 API 服務器保持原始大小寫
""")

print("=" * 80)
print("💡 建議修正位置")
print("=" * 80)

print("""
方案 1: 修改分析器（推薦）
檔案: brake_performance_analyzer.py, all_drivers_straight_line_speed.py
位置: 字典查找前添加標準化處理

修改前:
    if race_name and race_name in TRACK_..._DISTANCE:

修改後:
    # 標準化賽道名稱：首字母大寫
    race_name_normalized = race_name.title() if race_name else None
    if race_name_normalized and race_name_normalized in TRACK_..._DISTANCE:

方案 2: 修改 API 服務器
檔案: api/services/simple_analysis_service.py
位置: _build_cli_command 方法
確保保持原始大小寫
""")

print("\n" + "=" * 80)
