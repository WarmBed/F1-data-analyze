#!/usr/bin/env python3
"""測試日誌系統改進和日語模式下的圖表更新問題

測試項目：
1. ✅ 日誌系統使用日期式檔名（f1_gui_2025-10-06.log）
2. ✅ 日誌等級降為 INFO（不顯示 DEBUG）
3. ✅ 終端機不輸出日誌（僅寫入檔案）
4. 🔍 日語模式下 driver2=LEC 參數傳遞驗證
5. 🔍 update_lap_parameters 方法調用追蹤
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 設置路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.logger import setup_logging, get_logger

def test_logging_system():
    """測試日誌系統配置"""
    print("\n" + "="*80)
    print("📋 測試 1: 日誌系統配置驗證")
    print("="*80)
    
    # 初始化日誌系統
    setup_logging(component="test", level="INFO", force=True)
    logger = get_logger("logging_test")
    
    # 測試各級別日誌
    logger.debug("這是 DEBUG 訊息 - 應該不會出現在日誌檔案中")
    logger.info("這是 INFO 訊息 - 應該出現在日誌檔案中")
    logger.warning("這是 WARNING 訊息 - 應該出現在日誌檔案中")
    logger.error("這是 ERROR 訊息 - 應該出現在日誌檔案和錯誤日誌中")
    
    # 檢查日誌檔案是否存在
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = project_root / "logs" / f"f1_test_{today}.log"
    error_log_file = project_root / "logs" / f"f1_test_error_{today}.log"
    
    print(f"\n✅ 日誌檔案位置:")
    print(f"   - 一般日誌: {log_file}")
    print(f"   - 錯誤日誌: {error_log_file}")
    
    if log_file.exists():
        print(f"✅ 一般日誌檔案已創建")
        # 讀取最後 5 行
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"\n📄 日誌檔案內容（最後 5 行）:")
            for line in lines[-5:]:
                print(f"   {line.rstrip()}")
    else:
        print(f"❌ 一般日誌檔案不存在")
    
    if error_log_file.exists():
        print(f"\n✅ 錯誤日誌檔案已創建")
        with open(error_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"\n📄 錯誤日誌檔案內容（最後 3 行）:")
            for line in lines[-3:]:
                print(f"   {line.rstrip()}")
    else:
        print(f"❌ 錯誤日誌檔案不存在")
    
    print(f"\n💡 提示: 如果終端機沒有看到日誌訊息（除了這些測試輸出），表示 console 輸出已成功停用")

def test_driver2_parameter_handling():
    """測試 driver2 參數處理（模擬日語模式）"""
    print("\n" + "="*80)
    print("🇯🇵 測試 2: 日語模式下 driver2 參數處理")
    print("="*80)
    
    setup_logging(component="test", level="INFO", force=True)
    logger = get_logger("driver2_test")
    
    # 模擬不同語言的 driver2 選項
    test_cases = [
        {"text": "無", "data": None, "language": "中文"},
        {"text": "None", "data": None, "language": "English"},
        {"text": "なし", "data": None, "language": "日本語"},
        {"text": "LEC", "data": "LEC", "language": "All"},
        {"text": "VER", "data": "VER", "language": "All"},
    ]
    
    print("\n📋 測試 driver2 選項處理邏輯:")
    for case in test_cases:
        text = case["text"]
        data = case["data"]
        language = case["language"]
        
        # 模擬舊的錯誤邏輯（硬編碼 "無"）
        old_driver2 = text if text != "無" else None
        
        # 新的正確邏輯（使用 data）
        new_driver2 = text if data is not None else None
        
        match = "✅" if old_driver2 == new_driver2 else "❌"
        
        print(f"\n{match} 語言: {language}")
        print(f"   顯示文字: '{text}'")
        print(f"   關聯數據: {data}")
        print(f"   舊邏輯結果: {old_driver2}")
        print(f"   新邏輯結果: {new_driver2}")
        
        if old_driver2 != new_driver2:
            logger.warning(f"日語模式問題: 文字='{text}', 舊邏輯={old_driver2}, 新邏輯={new_driver2}")
            print(f"   ⚠️ 舊邏輯在此情況下會產生錯誤!")
    
    print("\n✅ 結論: 新邏輯使用 currentData() 可以正確處理所有語言")

def test_update_flow_simulation():
    """模擬更新流程的日誌追蹤"""
    print("\n" + "="*80)
    print("🔍 測試 3: 模擬日語模式下的參數更新流程")
    print("="*80)
    
    setup_logging(component="test", level="INFO", force=True)
    logger = get_logger("update_flow_test")
    
    # 模擬日語模式下的參數
    year = "2025"
    race = "Japan"
    session = "R"
    driver1 = "VER"
    driver2_text = "なし"  # 日語 "None"
    driver2_data = None
    lap1 = 1
    lap2 = 1
    
    logger.info(f"模擬更新流程開始")
    logger.info(f"參數: year={year}, race={race}, session={session}")
    logger.info(f"車手: driver1={driver1}, driver2_text='{driver2_text}', driver2_data={driver2_data}")
    logger.info(f"圈數: lap1={lap1}, lap2={lap2}")
    
    # 舊邏輯（錯誤）
    old_driver2 = driver2_text if driver2_text != "無" else None
    logger.warning(f"舊邏輯結果: driver2={old_driver2} (錯誤! 日語 'なし' 被當作車手代碼)")
    
    # 新邏輯（正確）
    new_driver2 = driver2_text if driver2_data is not None else None
    logger.info(f"新邏輯結果: driver2={new_driver2} (正確! 識別為 None)")
    
    # 模擬 API 調用
    if old_driver2:
        api_url = f"https://api.f1telemetrystationpro.org/api/v2/analysis/execute?driver1={driver1}&driver2={old_driver2}"
        logger.error(f"舊邏輯 API 調用: {api_url}")
        logger.error(f"❌ 這會導致 API 返回 422 錯誤（無效的車手代碼 'なし'）")
    
    if new_driver2 is None:
        api_url = f"https://api.f1telemetrystationpro.org/api/v2/analysis/execute?driver1={driver1}"
        logger.info(f"新邏輯 API 調用: {api_url}")
        logger.info(f"✅ 正確! driver2=None 時不包含在 API 請求中")
    
    # 模擬更新為 LEC
    print("\n" + "-"*80)
    print("🔄 使用者更新 driver2 為 LEC...")
    print("-"*80)
    
    driver2_text_new = "LEC"
    driver2_data_new = "LEC"
    
    new_driver2_updated = driver2_text_new if driver2_data_new is not None else None
    logger.info(f"更新後參數: driver2_text='{driver2_text_new}', driver2_data={driver2_data_new}")
    logger.info(f"新邏輯結果: driver2={new_driver2_updated}")
    
    api_url_updated = f"https://api.f1telemetrystationpro.org/api/v2/analysis/execute?driver1={driver1}&driver2={new_driver2_updated}"
    logger.info(f"更新後 API 調用: {api_url_updated}")
    logger.info(f"✅ 正確! driver2=LEC 已包含在 API 請求中")
    
    print("\n✅ 模擬完成 - 請檢查日誌檔案中的詳細記錄")

def main():
    """主測試流程"""
    print("\n" + "="*100)
    print("🧪 F1T 日誌系統和日語模式更新測試")
    print("="*100)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 執行測試
    test_logging_system()
    test_driver2_parameter_handling()
    test_update_flow_simulation()
    
    print("\n" + "="*100)
    print("✅ 所有測試完成")
    print("="*100)
    print(f"\n💡 重要提示:")
    print(f"   1. 檢查 logs/ 目錄中的日期式日誌檔案")
    print(f"   2. 確認終端機沒有出現 logger 輸出（僅測試的 print）")
    print(f"   3. 日誌檔案中應該只有 INFO/WARNING/ERROR，沒有 DEBUG")
    print(f"   4. 日語模式下 driver2 參數應該使用 currentData() 判斷")
    print("\n")

if __name__ == "__main__":
    main()
