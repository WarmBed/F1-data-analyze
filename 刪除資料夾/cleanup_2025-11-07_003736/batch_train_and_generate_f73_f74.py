#!/usr/bin/env python3
"""
批次訓練和生成腳本 - F73 + F74
Batch Training and Generation Script

功能:
1. 執行 F73 訓練所有 24 個賽道的 v3.8 模型
2. 執行 F74 為 2025 賽季所有賽事生成排位賽預測

作者: F1T Team
日期: 2025-11-05
"""

import subprocess
import sys
from pathlib import Path
import time
from typing import List, Tuple

# 2025 賽季所有賽事列表（按賽曆順序）
RACES_2025 = [
    "Bahrain",
    "Saudi Arabia",
    "Australia",
    "Japan",
    "China",
    "Miami",
    "Emilia Romagna",
    "Monaco",
    "Canada",
    "Spain",
    "Austria",
    "Great Britain",
    "Belgium",
    "Netherlands",
    "Italy",
    "Azerbaijan",
    "Singapore",
    "United States",
    "Mexico",
    "Brazil",
    "Las Vegas",
    "Qatar",
    "Abu Dhabi"
]

def print_header(title: str):
    """打印標題"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_progress(current: int, total: int, race: str, status: str):
    """打印進度"""
    print(f"[{current}/{total}] 🏁 {race}: {status}")

def run_f73_training() -> bool:
    """
    執行 F73 訓練所有賽道
    
    Returns:
        bool: 訓練是否成功
    """
    print_header("階段 1: F73 訓練所有賽道模型")
    
    print("\n📋 即將訓練 24 個賽道的 v3.8 模型...")
    print("⏱️  預計時間: 30-60 分鐘")
    print("💡 提示: 訓練過程中可能需要從 FastF1 下載數據\n")
    
    try:
        cmd = [sys.executable, "f1_analysis_modular_main.py", "-f", "73"]
        print(f"🚀 執行命令: {' '.join(cmd)}\n")
        
        # 執行 F73
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # 檢查輸出
        if result.returncode == 0:
            print("✅ F73 訓練完成！")
            
            # 檢查模型檔案
            model_dir = Path("models/track_specific_v3.8")
            if model_dir.exists():
                pkl_files = list(model_dir.glob("*.pkl"))
                print(f"📊 已生成 {len(pkl_files)} 個模型檔案")
                return len(pkl_files) > 0
            else:
                print("⚠️  警告: models/track_specific_v3.8 目錄不存在")
                return False
        else:
            print(f"❌ F73 訓練失敗 (返回碼: {result.returncode})")
            print(f"錯誤輸出:\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ F73 執行異常: {e}")
        return False

def run_f74_generation(year: int = 2025) -> Tuple[int, int]:
    """
    執行 F74 生成所有賽事的排位賽預測
    
    Args:
        year: 賽季年份
        
    Returns:
        Tuple[int, int]: (成功數, 失敗數)
    """
    print_header(f"階段 2: F74 生成 {year} 賽季排位賽預測")
    
    total_races = len(RACES_2025)
    success_count = 0
    fail_count = 0
    
    print(f"\n📋 總賽事數: {total_races}")
    print(f"🎯 目標年份: {year}\n")
    
    for index, race in enumerate(RACES_2025, 1):
        print_progress(index, total_races, race, "處理中...")
        
        try:
            cmd = [
                sys.executable,
                "f1_analysis_modular_main.py",
                "-f", "74",
                "-y", str(year),
                "-r", race
            ]
            
            # 執行 F74
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120  # 2 分鐘超時
            )
            
            # 檢查結果
            if result.returncode == 0 and "JSON 檔案已保存" in result.stdout:
                print_progress(index, total_races, race, "✅ 成功")
                success_count += 1
                
                # 檢查生成的 JSON 檔案
                json_file = Path(f"json/qualifying_prediction_{year}_{race}.json")
                if json_file.exists():
                    file_size = json_file.stat().st_size
                    print(f"   📄 檔案: {json_file.name} ({file_size} bytes)")
            else:
                print_progress(index, total_races, race, "⚠️  警告 (可能無數據)")
                fail_count += 1
                
        except subprocess.TimeoutExpired:
            print_progress(index, total_races, race, "❌ 超時")
            fail_count += 1
        except Exception as e:
            print_progress(index, total_races, race, f"❌ 錯誤: {e}")
            fail_count += 1
        
        # 每 5 個賽事後暫停 2 秒
        if index % 5 == 0 and index < total_races:
            print("   ⏸️  暫停 2 秒...\n")
            time.sleep(2)
    
    return success_count, fail_count

def list_generated_files(year: int = 2025):
    """列出生成的 JSON 檔案"""
    print_header("生成的檔案列表")
    
    json_dir = Path("json")
    if not json_dir.exists():
        print("❌ json 目錄不存在")
        return
    
    pattern = f"qualifying_prediction_{year}_*.json"
    json_files = sorted(
        json_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if json_files:
        print(f"\n📂 找到 {len(json_files)} 個 JSON 檔案:\n")
        for json_file in json_files:
            stat = json_file.stat()
            size_kb = stat.st_size / 1024
            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
            print(f"  📄 {json_file.name:<50} {size_kb:>8.2f} KB  {mtime}")
    else:
        print(f"\n⚠️  未找到任何 {pattern} 檔案")

def main():
    """主函數"""
    print_header("F1T 批次訓練與生成工具")
    print("功能: F73 訓練 + F74 生成")
    print("目標: 2025 賽季所有賽事")
    
    # 階段 1: F73 訓練
    print("\n" + "▶" * 35)
    if not run_f73_training():
        print("\n❌ F73 訓練失敗，終止執行")
        sys.exit(1)
    
    print("\n⏸️  暫停 5 秒後開始 F74 生成...")
    time.sleep(5)
    
    # 階段 2: F74 生成
    print("\n" + "▶" * 35)
    success_count, fail_count = run_f74_generation(year=2025)
    
    # 階段 3: 列出生成的檔案
    print("\n" + "▶" * 35)
    list_generated_files(year=2025)
    
    # 最終摘要
    print_header("執行摘要")
    total_races = len(RACES_2025)
    print(f"\n✅ 成功: {success_count}/{total_races} 個賽事")
    print(f"❌ 失敗: {fail_count}/{total_races} 個賽事")
    print(f"📊 成功率: {success_count/total_races*100:.1f}%")
    
    print("\n💡 提示: 請在 GUI 中重新載入 Qualifying Prediction 模組以查看更新後的數據")
    print("\n" + "=" * 70)
    
    # 返回狀態碼
    sys.exit(0 if fail_count == 0 else 1)

if __name__ == "__main__":
    main()
