"""
測試方案 1 的效果：移除 time.sleep(0.25)
對比修改前後的性能差異
"""
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_solution_1_effect():
    """
    測試移除 time.sleep(0.25) 的實際效果
    """
    print("=" * 80)
    print("🧪 測試方案 1：移除 time.sleep(0.25)")
    print("=" * 80)
    
    from PyQt5.QtWidgets import QApplication
    from f1t_gui_main import StyleHMainWindow
    
    app = QApplication(sys.argv)
    
    print("\n📦 初始化主視窗...")
    main_window = StyleHMainWindow()
    main_window.show()
    
    # 設置基本參數
    print("\n⚙️ 設置測試參數...")
    main_window.year_combo.setCurrentText("2025")
    main_window.race_combo.setCurrentText("Japan")
    main_window.session_combo.setCurrentText("R")
    main_window.driver1_combo.setCurrentText("VER")
    
    QApplication.processEvents()
    
    # 創建測試視窗
    print("\n🏗️ 創建測試視窗...")
    window_count = 0
    
    # 只創建速度分析視窗作為測試
    for i in range(10):
        try:
            if hasattr(main_window, 'open_speed_analysis'):
                main_window.open_speed_analysis()
                window_count += 1
                print(f"  ✅ 已創建視窗 #{window_count}")
                QApplication.processEvents()
        except Exception as e:
            print(f"  ❌ 創建失敗: {e}")
            break
    
    print(f"\n✅ 共創建 {window_count} 個視窗")
    print(f"📊 實際活動視窗: {len(main_window.lap_analysis_windows)}")
    
    # 等待視窗完全初始化
    time.sleep(1)
    QApplication.processEvents()
    
    # 測試更新性能
    print("\n" + "=" * 80)
    print("🚀 開始性能測試...")
    print("=" * 80)
    
    # 進行 3 次測試取平均
    timings = []
    for test_run in range(3):
        print(f"\n測試輪次 {test_run + 1}/3:")
        
        # 改變參數觸發更新
        if test_run == 0:
            main_window.race_combo.setCurrentText("Australia")
        elif test_run == 1:
            main_window.race_combo.setCurrentText("Japan")
        else:
            main_window.driver1_combo.setCurrentText("LEC")
        
        QApplication.processEvents()
        
        start_time = time.time()
        main_window.update_all_lap_analysis()
        elapsed = time.time() - start_time
        
        timings.append(elapsed)
        print(f"  ⏱️ 執行時間: {elapsed:.3f}s")
        
        # 等待異步操作完成
        time.sleep(2)
        QApplication.processEvents()
    
    # 統計結果
    print("\n" + "=" * 80)
    print("📊 測試結果統計:")
    print("=" * 80)
    
    avg_time = sum(timings) / len(timings)
    min_time = min(timings)
    max_time = max(timings)
    
    print(f"\n視窗數量: {window_count}")
    print(f"測試次數: {len(timings)}")
    print(f"\n⏱️ 時間統計:")
    print(f"  平均時間: {avg_time:.3f}s")
    print(f"  最短時間: {min_time:.3f}s")
    print(f"  最長時間: {max_time:.3f}s")
    
    # 計算理論節省時間
    theoretical_saving = window_count * 0.25
    print(f"\n💡 理論分析:")
    print(f"  移除前每視窗延遲: 0.25s")
    print(f"  {window_count} 個視窗理論節省: {theoretical_saving:.2f}s")
    
    # 與基準對比
    baseline_time = 47.0  # 用戶報告的原始時間
    improvement = baseline_time - avg_time
    improvement_pct = (improvement / baseline_time) * 100
    
    print(f"\n📈 與基準對比:")
    print(f"  基準時間（用戶報告）: {baseline_time}s")
    print(f"  當前平均時間: {avg_time:.3f}s")
    print(f"  改善幅度: {improvement:.3f}s ({improvement_pct:.1f}%)")
    
    # 評估結果
    print("\n" + "=" * 80)
    print("✅ 評估結論:")
    print("=" * 80)
    
    if avg_time < 5.0:
        print("🎉 極佳！時間已降至 5 秒以內")
    elif avg_time < 10.0:
        print("👍 良好！時間顯著改善")
    elif avg_time < baseline_time - 2:
        print("✓ 有改善，但仍有優化空間")
    else:
        print("⚠️ 改善不明顯，需要進一步分析")
    
    if theoretical_saving > 2.0:
        print(f"💡 方案 1 理論上可節省 {theoretical_saving:.2f}s")
    
    if avg_time > 10.0:
        print("⚠️ 建議執行 Profiling 找出其他瓶頸")
    
    # 清理
    app.quit()
    
    return {
        'window_count': window_count,
        'avg_time': avg_time,
        'min_time': min_time,
        'max_time': max_time,
        'improvement': improvement,
        'improvement_pct': improvement_pct,
        'timings': timings
    }

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║  方案 1 效果驗證：移除 time.sleep(0.25)                          ║
║  預期改善：10 視窗減少 2.5 秒                                     ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        results = test_solution_1_effect()
        
        print("\n" + "=" * 80)
        print("📝 測試完成，結果摘要:")
        print("=" * 80)
        print(f"✅ 成功執行 {len(results['timings'])} 次測試")
        print(f"📊 平均時間: {results['avg_time']:.3f}s")
        print(f"📈 改善幅度: {results['improvement_pct']:.1f}%")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
