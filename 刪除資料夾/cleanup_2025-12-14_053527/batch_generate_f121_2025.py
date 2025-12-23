"""
批次生成 2025 年所有正賽的 F121 分析數據
"""
import subprocess
import time
from datetime import datetime

# 2025 年已完成的賽事列表
RACES_2025 = [
    ("Australia", "Australian Grand Prix"),
    ("China", "Chinese Grand Prix"),
    ("Japan", "Japanese Grand Prix"),
    ("Bahrain", "Bahrain Grand Prix"),
    ("Saudi Arabia", "Saudi Arabian Grand Prix"),
    ("Miami", "Miami Grand Prix"),
    ("Emilia Romagna", "Emilia Romagna Grand Prix"),
    ("Monaco", "Monaco Grand Prix"),
    ("Spain", "Spanish Grand Prix"),
    ("Canada", "Canadian Grand Prix"),
    ("Austria", "Austrian Grand Prix"),
    ("Great Britain", "British Grand Prix"),
    ("Belgium", "Belgian Grand Prix"),
    ("Hungary", "Hungarian Grand Prix"),
    ("Netherlands", "Dutch Grand Prix"),
    ("Italy", "Italian Grand Prix"),
    ("Azerbaijan", "Azerbaijan Grand Prix"),
    ("Singapore", "Singapore Grand Prix"),
    ("United States", "United States Grand Prix"),
    ("Mexico", "Mexico City Grand Prix"),
    ("Brazil", "São Paulo Grand Prix"),
    ("Las Vegas", "Las Vegas Grand Prix"),
    ("Qatar", "Qatar Grand Prix"),
    ("Abu Dhabi", "Abu Dhabi Grand Prix"),
]

def run_f121_analysis(race_name):
    """執行 F121 分析"""
    cmd = [
        "python",
        "f1_analysis_modular_main.py",
        "-f", "121",
        "-y", "2025",
        "-r", race_name,
        "-s", "R"
    ]
    
    print(f"\n{'='*80}")
    print(f"正在分析: {race_name}")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300  # 5 分鐘超時
        )
        
        if "SUCCESS" in result.stdout:
            print(f"✅ {race_name} - 分析完成")
            return True
        else:
            print(f"❌ {race_name} - 分析失敗")
            if "ERROR" in result.stdout:
                print(f"   錯誤信息: {[line for line in result.stdout.split('\\n') if 'ERROR' in line][:3]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️  {race_name} - 超時")
        return False
    except Exception as e:
        print(f"❌ {race_name} - 異常: {e}")
        return False

def main():
    print("=" * 80)
    print("批次生成 2025 F1 賽季所有正賽的 F121 分析數據")
    print("=" * 80)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"總計: {len(RACES_2025)} 場賽事")
    print()
    
    success_count = 0
    failed_races = []
    
    for i, (race_name, full_name) in enumerate(RACES_2025, 1):
        print(f"\n[{i}/{len(RACES_2025)}] {full_name}")
        
        if run_f121_analysis(race_name):
            success_count += 1
        else:
            failed_races.append(race_name)
        
        # 每場分析後休息 2 秒
        if i < len(RACES_2025):
            time.sleep(2)
    
    # 總結
    print("\n" + "=" * 80)
    print("批次生成完成")
    print("=" * 80)
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"成功: {success_count}/{len(RACES_2025)}")
    print(f"失敗: {len(failed_races)}/{len(RACES_2025)}")
    
    if failed_races:
        print("\n失敗的賽事:")
        for race in failed_races:
            print(f"  - {race}")

if __name__ == "__main__":
    main()
