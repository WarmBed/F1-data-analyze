"""
測試 F125 + Ollama 整合

此腳本測試：
1. F125 JSON 生成
2. Ollama AI 分析
3. Markdown 報告生成
"""

import os
import sys
import json

# 添加專案路徑
sys.path.insert(0, os.path.dirname(__file__))

from batch_generator_gui import analyze_f125_with_ollama

def test_f125_ollama_integration():
    """測試 F125 + Ollama 整合"""

    print("="*80)
    print("  F125 + Ollama AI 整合測試")
    print("="*80)

    # 測試參數
    YEAR = 2025
    RACE = "Abu Dhabi"
    SESSION = "FP2"

    # JSON 檔案路徑
    json_filename = f"vehicle_performance_analysis_{YEAR}_{RACE}_{SESSION}.json"
    json_path = os.path.join("json", json_filename)

    print(f"\n[STEP 1] 檢查 JSON 檔案")
    print(f"路徑: {json_path}")

    if not os.path.exists(json_path):
        print(f"[ERROR] JSON 檔案不存在")
        print(f"請先執行: python f1_analysis_modular_main.py -f 125 -y {YEAR} -r \"{RACE}\" -s {SESSION}")
        return False

    print(f"[OK] JSON 檔案存在")

    # 讀取並驗證 JSON
    print(f"\n[STEP 2] 驗證 JSON 格式")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data.get('success'):
            print(f"[ERROR] JSON 標記為失敗")
            return False

        if 'formatted_summary' not in data:
            print(f"[WARNING] JSON 缺少 formatted_summary 欄位")
            print(f"可能是舊版本的 JSON，建議重新生成")

        print(f"[OK] JSON 格式正確")
        print(f"  - 車手數: {data['summary']['total_drivers']}")
        print(f"  - 賽道類型: {data['track_info']['track_type']}")

    except Exception as e:
        print(f"[ERROR] JSON 讀取失敗: {e}")
        return False

    # 測試 Ollama 分析
    print(f"\n[STEP 3] 執行 Ollama AI 分析")
    print(f"這可能需要 1-3 分鐘，請稍候...")

    md_path = analyze_f125_with_ollama(
        json_path=json_path,
        year=YEAR,
        race=RACE,
        session=SESSION
    )

    if md_path:
        print(f"\n[SUCCESS] AI 分析完成！")
        print(f"Markdown 報告: {md_path}")

        # 顯示報告前幾行
        print(f"\n[預覽] Markdown 報告前 30 行:")
        print("-"*80)
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:30], 1):
                print(f"{i:3d}: {line.rstrip()}")

        print("-"*80)
        print(f"\n[INFO] 完整報告請查看: {md_path}")

        return True
    else:
        print(f"\n[FAILED] AI 分析失敗")
        print(f"可能原因:")
        print(f"  1. Ollama 未安裝（請執行: ollama run llama3.2）")
        print(f"  2. llama3.2 模型未下載")
        print(f"  3. Ollama 服務未啟動")
        return False


if __name__ == "__main__":
    print("\n")
    try:
        success = test_f125_ollama_integration()
        print("\n" + "="*80)
        if success:
            print("  ✓ 測試成功！F125 + Ollama 整合正常運作")
        else:
            print("  ✗ 測試失敗，請檢查上述錯誤訊息")
        print("="*80 + "\n")

        exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] 測試中斷")
        exit(1)
    except Exception as e:
        print(f"\n\n[EXCEPTION] 測試異常: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
