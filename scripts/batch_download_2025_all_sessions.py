"""
批次下載 2025 年所有賽事的所有會話數據

會話類型：FP1, FP2, FP3, Q (排位賽), R (正賽)
如果會話不存在則自動跳過

執行方式：
    python batch_download_2025_all_sessions.py
"""
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# 2025 年 F1 賽程（按賽曆順序）
RACES_2025 = [
    "Australia",
    "China",
    "Japan",
    "Bahrain",
    "Saudi Arabia",
    "Miami",
    "Emilia Romagna",
    "Monaco",
    "Spain",
    "Canada",
    "Austria",
    "Great Britain",
    "Belgium",
    "Hungary",
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

# 所有會話類型
SESSIONS = ["FP1", "FP2", "FP3", "Q", "R"]

# F120 功能 ID
FUNCTION_ID = 120

def run_cli_analysis(year: int, race: str, session: str) -> tuple[bool, str]:
    """
    執行 CLI 分析命令
    
    Returns:
        (success, message)
    """
    try:
        cmd = [
            "python",
            "f1_analysis_modular_main.py",
            "-f", str(FUNCTION_ID),
            "-y", str(year),
            "-r", race,
            "-s", session
        ]
        
        print(f"  🔄 執行命令: {' '.join(cmd)}")
        
        # 執行命令並捕獲輸出
        # Windows 使用 cp950 (Big5) 編碼，使用 errors='ignore' 避免解碼錯誤
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='cp950',  # Windows 繁體中文編碼
            errors='ignore',   # 忽略無法解碼的字元
            timeout=600  # 10 分鐘超時
        )
        
        # 檢查是否成功
        if result.returncode == 0:
            # 檢查輸出中是否有成功訊息
            stdout_text = result.stdout or ""
            if "SUCCESS" in stdout_text or "成功" in stdout_text:
                return True, "分析成功"
            elif "無此賽事" in stdout_text or "Session not found" in stdout_text.lower():
                return False, "會話不存在"
            elif "No such session" in stdout_text:
                return False, "會話不存在"
            else:
                return True, "分析完成"
        else:
            # 檢查錯誤訊息
            stderr_text = result.stderr or ""
            stdout_text = result.stdout or ""
            error_msg = stderr_text if stderr_text else stdout_text
            
            if "無此賽事" in error_msg or "Session not found" in error_msg.lower():
                return False, "會話不存在"
            elif "No such session" in error_msg:
                return False, "會話不存在"
            else:
                return False, f"執行失敗: {error_msg[:200]}"
                
    except subprocess.TimeoutExpired:
        return False, "執行超時（超過 10 分鐘）"
    except Exception as e:
        return False, f"執行錯誤: {str(e)}"

def main():
    """主執行函數"""
    print("=" * 80)
    print("🏎️  F1 2025 全賽季數據下載腳本")
    print("=" * 80)
    print(f"📅 目標年份: 2025")
    print(f"🏁 賽事數量: {len(RACES_2025)}")
    print(f"📊 會話類型: {', '.join(SESSIONS)}")
    print(f"🔧 分析功能: F120 彎道全圈數分析")
    print("=" * 80)
    print()
    
    # 統計資料
    total_attempts = 0
    total_success = 0
    total_skipped = 0
    total_failed = 0
    
    results = []  # 儲存所有結果
    
    start_time = time.time()
    
    # 遍歷所有賽事
    for race_idx, race in enumerate(RACES_2025, 1):
        print(f"\n{'─' * 80}")
        print(f"🏁 [{race_idx}/{len(RACES_2025)}] {race}")
        print(f"{'─' * 80}")
        
        race_success = 0
        race_skipped = 0
        race_failed = 0
        
        # 遍歷所有會話
        for session in SESSIONS:
            total_attempts += 1
            session_key = f"{race}_{session}"
            
            print(f"\n  📍 會話: {session}")
            
            # 執行分析
            success, message = run_cli_analysis(2025, race, session)
            
            if success:
                print(f"  ✅ {message}")
                total_success += 1
                race_success += 1
                results.append((race, session, "✅ 成功", message))
            elif "不存在" in message:
                print(f"  ⏭️  {message}（跳過）")
                total_skipped += 1
                race_skipped += 1
                results.append((race, session, "⏭️  跳過", message))
            else:
                print(f"  ❌ {message}")
                total_failed += 1
                race_failed += 1
                results.append((race, session, "❌ 失敗", message))
            
            # 避免過度請求 API
            time.sleep(2)
        
        # 賽事摘要
        print(f"\n  📊 {race} 摘要: 成功 {race_success}, 跳過 {race_skipped}, 失敗 {race_failed}")
    
    # 最終統計
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("📊 最終統計")
    print("=" * 80)
    print(f"⏱️  總耗時: {duration / 60:.1f} 分鐘 ({duration:.0f} 秒)")
    print(f"📌 總嘗試: {total_attempts}")
    print(f"✅ 成功: {total_success} ({total_success / total_attempts * 100:.1f}%)")
    print(f"⏭️  跳過: {total_skipped} ({total_skipped / total_attempts * 100:.1f}%)")
    print(f"❌ 失敗: {total_failed} ({total_failed / total_attempts * 100:.1f}%)")
    print("=" * 80)
    
    # 顯示失敗項目
    if total_failed > 0:
        print("\n⚠️  失敗項目明細：")
        print("─" * 80)
        for race, session, status, message in results:
            if "失敗" in status:
                print(f"  {race} - {session}: {message}")
        print("─" * 80)
    
    # 儲存結果報告
    report_path = Path("batch_download_2025_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"F1 2025 全賽季數據下載報告\n")
        f.write(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"總耗時: {duration / 60:.1f} 分鐘\n")
        f.write(f"\n{'=' * 80}\n")
        f.write(f"統計摘要\n")
        f.write(f"{'=' * 80}\n")
        f.write(f"總嘗試: {total_attempts}\n")
        f.write(f"✅ 成功: {total_success} ({total_success / total_attempts * 100:.1f}%)\n")
        f.write(f"⏭️  跳過: {total_skipped} ({total_skipped / total_attempts * 100:.1f}%)\n")
        f.write(f"❌ 失敗: {total_failed} ({total_failed / total_attempts * 100:.1f}%)\n")
        f.write(f"\n{'=' * 80}\n")
        f.write(f"詳細結果\n")
        f.write(f"{'=' * 80}\n")
        for race, session, status, message in results:
            f.write(f"{race:20s} {session:5s} {status:10s} {message}\n")
    
    print(f"\n💾 報告已儲存至: {report_path}")
    print("\n✅ 批次下載完成！")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  使用者中斷執行")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
