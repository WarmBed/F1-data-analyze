# -*- coding: utf-8 -*-
"""
修復 6 個 lap_analysis 模組缺少的 _check_and_load_telemetry_if_needed 方法
目標模組：Speed, Gear, Throttle, Acceleration, SpeedDiff, DistanceDiff
參考模組：Brake (已正確實現)
"""

import os
import re

# 需要修復的模組清單（不包括 Brake 和 RPM，它們已有正確實現）
MODULES_TO_FIX = [
    {
        "path": "modules/gui/lap_analysis/speed_analysis/speed_analysis_mdi.py",
        "class_name": "SpeedAnalysisModule",
        "tag": "speed_MDI"
    },
    {
        "path": "modules/gui/lap_analysis/gear_analysis/gear_analysis_mdi.py",
        "class_name": "GearAnalysisModule",
        "tag": "gear_MDI"
    },
    {
        "path": "modules/gui/lap_analysis/throttle_analysis/throttle_analysis_mdi.py",
        "class_name": "ThrottleAnalysisModule",
        "tag": "throttle_MDI"
    },
    {
        "path": "modules/gui/lap_analysis/acceleration_analysis/acceleration_analysis_mdi.py",
        "class_name": "accelerationAnalysisModule",
        "tag": "acceleration_MDI"
    },
    {
        "path": "modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_mdi.py",
        "class_name": "SpeeddiffAnalysisModule",
        "tag": "speeddiff_MDI"
    },
    {
        "path": "modules/gui/lap_analysis/distancediff_analysis/distancediff_analysis_mdi.py",
        "class_name": "distancediffAnalysisModule",
        "tag": "distancediff_MDI"
    }
]

# Brake 模組的正確實現模板（作為參考）
METHOD_TEMPLATE = '''
    def _check_and_load_telemetry_if_needed(self, year: Optional[str] = None,
                                            race: Optional[str] = None,
                                            session: Optional[str] = None) -> bool:
        """確保遙測分析資料可用，遵循 API-ONLY 模式
        
        ⚠️ API-ONLY 模式：此方法只檢查本地 JSON 緩存，不自動創建視窗
        若數據不存在，應通過 API 或提示用戶手動操作
        """
        try:
            target_year = str(year or self.current_year or "").strip()
            target_race = (race or self.current_race or "").strip()
            target_session = str(session or self.current_session or "").strip()

            print(f"[{tag}] 🔍 [API-ONLY] 檢查遙測分析本地緩存: {{target_year}} {{target_race}} {{target_session}}")

            # ✅ 允許：檢查本地 JSON 緩存
            telemetry_file = self._find_telemetry_analysis_file(
                year=target_year,
                race=target_race,
                session=target_session
            )
            if telemetry_file:
                print(f"[{tag}] 📂 [API-ONLY] 找到本地遙測分析緩存: {{telemetry_file}}")
                return True

            # ❌ 禁止：自動創建視窗或啟動 CLI
            # 改為僅提示用戶通過 API 或主視窗遙測模組獲取數據
            print("⚠️ [{tag}] [API-ONLY] 遙測分析數據不存在於本地緩存")
            print("💡 [{tag}] [API-ONLY] 提示：請先透過主視窗遙測模組或 REST API 獲取遙測數據")
            print("💡 [{tag}] [API-ONLY] 或者手動執行 CLI: python f1_analysis_modular_main.py -f 8")
            return False

        except Exception as e:
            print(f"[ERROR] [{tag}] _check_and_load_telemetry_if_needed 失敗: {{e}}")
            return False
'''

def find_insertion_point(content, class_name):
    """找到 AnalysisModule 類別中 _ensure_telemetry_data_for_fastest_laps 方法的位置"""
    # 先找到類別定義
    class_pattern = rf'class {re.escape(class_name)}\(.*?\):'
    class_match = re.search(class_pattern, content)
    if not class_match:
        print(f"❌ 找不到類別: {class_name}")
        return None
    
    class_start = class_match.start()
    
    # 從類別開始處往後搜尋 _ensure_telemetry_data_for_fastest_laps 方法
    method_pattern = r'def _ensure_telemetry_data_for_fastest_laps\(self\)'
    method_match = re.search(method_pattern, content[class_start:])
    if not method_match:
        print(f"⚠️ 找不到 _ensure_telemetry_data_for_fastest_laps 方法")
        return None
    
    # 返回該方法在整個文件中的絕對位置
    return class_start + method_match.start()

def check_method_exists(content, class_name):
    """檢查 AnalysisModule 類別中是否已有 _check_and_load_telemetry_if_needed 方法"""
    class_pattern = rf'class {re.escape(class_name)}\(.*?\):'
    class_match = re.search(class_pattern, content)
    if not class_match:
        return False
    
    class_start = class_match.start()
    
    # 搜尋下一個類別定義（作為搜尋範圍的終點）
    next_class_match = re.search(r'\nclass \w+', content[class_start + 10:])
    if next_class_match:
        search_end = class_start + 10 + next_class_match.start()
    else:
        search_end = len(content)
    
    # 在類別範圍內搜尋方法（帶參數的版本）
    method_pattern = r'def _check_and_load_telemetry_if_needed\(self,\s*year:'
    return bool(re.search(method_pattern, content[class_start:search_end]))

def add_method_to_module(file_path, class_name, tag):
    """在指定模組的 AnalysisModule 類別中添加缺失的方法"""
    print(f"\n{'='*80}")
    print(f"處理: {file_path}")
    print(f"類別: {class_name}")
    print(f"標籤: {tag}")
    print(f"{'='*80}")
    
    try:
        # 讀取檔案
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查方法是否已存在
        if check_method_exists(content, class_name):
            print(f"✅ {class_name} 已有 _check_and_load_telemetry_if_needed 方法（帶參數版本），跳過")
            return True
        
        # 找到插入位置
        insertion_point = find_insertion_point(content, class_name)
        if insertion_point is None:
            print(f"❌ 無法找到插入位置")
            return False
        
        # 準備要插入的方法（替換標籤）
        method_code = METHOD_TEMPLATE.replace('{tag}', tag)
        
        # 在 _ensure_telemetry_data_for_fastest_laps 方法之前插入
        modified_content = content[:insertion_point] + method_code + '\n' + content[insertion_point:]
        
        # 備份原始檔案
        backup_path = file_path + '.backup_telemetry_method'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📦 已備份原始檔案: {backup_path}")
        
        # 寫入修改後的內容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"✅ 已添加 _check_and_load_telemetry_if_needed 方法到 {class_name}")
        
        # 驗證修改
        with open(file_path, 'r', encoding='utf-8') as f:
            new_content = f.read()
        
        if check_method_exists(new_content, class_name):
            print(f"✅ 驗證成功：方法已正確添加")
            return True
        else:
            print(f"❌ 驗證失敗：方法添加可能有問題")
            return False
            
    except Exception as e:
        print(f"❌ 處理檔案時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🚀 開始修復 lap_analysis 模組缺失的遙測方法...")
    print(f"📋 需要修復的模組數量: {len(MODULES_TO_FIX)}")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for module_info in MODULES_TO_FIX:
        result = add_method_to_module(
            module_info["path"],
            module_info["class_name"],
            module_info["tag"]
        )
        
        if result is True:
            if check_method_exists(
                open(module_info["path"], 'r', encoding='utf-8').read(),
                module_info["class_name"]
            ):
                success_count += 1
            else:
                skip_count += 1
        else:
            fail_count += 1
    
    print("\n" + "="*80)
    print("📊 修復結果統計:")
    print(f"  ✅ 成功修復: {success_count}")
    print(f"  ⏭️  已存在跳過: {skip_count}")
    print(f"  ❌ 修復失敗: {fail_count}")
    print("="*80)
    
    if fail_count == 0:
        print("\n🎉 所有模組修復完成！")
        print("\n📝 後續步驟:")
        print("1. 檢查修改後的檔案是否正確")
        print("2. 執行測試驗證功能")
        print("3. 重新打包 EXE")
    else:
        print("\n⚠️ 部分模組修復失敗，請檢查錯誤訊息")

if __name__ == "__main__":
    main()
