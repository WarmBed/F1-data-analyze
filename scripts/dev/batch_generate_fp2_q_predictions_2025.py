"""
2025 FP2→Q 批次預測生成器
使用新訓練的 v3.10 模型 (含 Quali Sim 過濾邏輯)
"""
import subprocess
import time
from pathlib import Path

# 2025 賽季所有賽事 (與數據收集腳本保持一致)
RACES_2025 = [
    "Australia", "China", "Japan", "Bahrain", "Saudi Arabia",
    "Miami", "Emilia Romagna", "Monaco", "Spain", "Canada",
    "Austria", "Great Britain", "Belgium", "Hungary", "Netherlands",
    "Italy", "Azerbaijan", "Singapore", "United States", "Mexico",
    "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
]

def run_fp2_q_prediction(race: str):
    """執行單一賽事的 FP2→Q 預測"""
    print(f"\n{'='*60}")
    print(f"[{RACES_2025.index(race) + 1}/{len(RACES_2025)}] 生成: {race}")
    print(f"{'='*60}\n")
    
    try:
        cmd = [
            "python",
            "f1_analysis_modular_main.py",
            "-f", "76",
            "-y", "2025",
            "-r", race,
            "-s", "R"
        ]
        
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # 檢查是否成功生成
        output_file = Path(f"json/fp2_qualifying_prediction_2025_{race}.json")
        if output_file.exists():
            print(f"✅ {race} 預測生成成功")
            return True
        else:
            print(f"⚠️  {race} 預測檔案未找到")
            print(f"STDOUT:\n{result.stdout}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ {race} 預測失敗")
        print(f"錯誤碼: {e.returncode}")
        print(f"STDERR:\n{e.stderr}")
        return False
    except Exception as e:
        print(f"❌ {race} 執行異常: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("2025 FP2→Q 批次預測生成器")
    print("="*60)
    print(f"總賽事數: {len(RACES_2025)}")
    print(f"模型版本: v3.10 (含 Quali Sim 過濾)")
    
    start_time = time.time()
    success_count = 0
    failed_races = []
    
    for race in RACES_2025:
        if run_fp2_q_prediction(race):
            success_count += 1
        else:
            failed_races.append(race)
        
        # 短暫延遲避免過度請求
        time.sleep(1)
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "="*60)
    print("批次預測完成！")
    print("="*60)
    print(f"✅ 成功: {success_count}/{len(RACES_2025)} 場賽事")
    print(f"⏱️  耗時: {elapsed_time:.1f} 秒")
    
    if failed_races:
        print(f"\n⚠️  失敗賽事 ({len(failed_races)}):")
        for race in failed_races:
            print(f"   - {race}")
    else:
        print("\n🎉 所有賽事預測生成成功！")
    
    print(f"\n📁 輸出目錄: json/")
    print(f"📋 檔案命名: fp2_qualifying_prediction_2025_{{race}}.json")

if __name__ == "__main__":
    main()
