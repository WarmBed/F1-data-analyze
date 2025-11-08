"""
Lap Analysis Cleanup 效果診斷工具
==========================================
目的：精確測試 cleanup() 方法是否被正確調用和執行

測試策略：
1. 單模組測試（一次只開一個）
2. 監控 cleanup() 是否被調用
3. 檢查 MDI 關閉邏輯
4. 分析未清理的物件類型
"""

import sys
import os
import gc
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))


def check_cleanup_method_exists():
    """檢查所有 Chart Widget 是否有 cleanup() 方法"""
    print("=" * 80)
    print("階段 1: 檢查 cleanup() 方法是否存在")
    print("=" * 80)
    
    modules = [
        "modules.gui.lap_analysis.speed_analysis_chart_widget",
        "modules.gui.lap_analysis.throttle_analysis_chart_widget",
        "modules.gui.lap_analysis.acceleration_analysis_chart_widget",
        "modules.gui.lap_analysis.brake_analysis_chart_widget",
        "modules.gui.lap_analysis.gear_analysis_chart_widget",
        "modules.gui.lap_analysis.rpm_analysis_chart_widget",
        "modules.gui.lap_analysis.timediff_analysis_chart_widget",
        "modules.gui.lap_analysis.speeddiff_analysis_chart_widget",
        "modules.gui.lap_analysis.distancediff_analysis_chart_widget",
    ]
    
    class_names = [
        "SpeedAnalysisChartWidget",
        "ThrottleAnalysisChartWidget",
        "accelerationAnalysisChartWidget",
        "BrakeAnalysisChartWidget",
        "GearAnalysisChartWidget",
        "RPMAnalysisChartWidget",
        "timediffAnalysisChartWidget",
        "SpeeddiffAnalysisChartWidget",
        "distancediffAnalysisChartWidget",
    ]
    
    results = []
    for module_name, class_name in zip(modules, class_names):
        try:
            module = __import__(module_name, fromlist=[class_name])
            widget_class = getattr(module, class_name)
            
            has_cleanup = hasattr(widget_class, 'cleanup')
            is_callable = callable(getattr(widget_class, 'cleanup', None))
            
            status = "✅" if (has_cleanup and is_callable) else "❌"
            results.append((class_name, status, has_cleanup, is_callable))
            print(f"{status} {class_name:40s} cleanup={'存在' if has_cleanup else '不存在':6s} callable={is_callable}")
        except Exception as e:
            print(f"❌ {class_name:40s} 匯入失敗: {e}")
            results.append((class_name, "❌", False, False))
    
    success_count = sum(1 for _, status, _, _ in results if status == "✅")
    print(f"\n結果: {success_count}/{len(results)} 個模組有 cleanup() 方法\n")
    
    return results


def check_mdi_cleanup_logic():
    """檢查 MDI 關閉邏輯是否調用 cleanup()"""
    print("=" * 80)
    print("階段 2: 檢查 MDI 關閉邏輯")
    print("=" * 80)
    
    mdi_file = project_root / "modules" / "gui" / "lap_analysis" / "lap_analysis_module.py"
    
    if not mdi_file.exists():
        print(f"❌ 找不到檔案: {mdi_file}")
        return False
    
    content = mdi_file.read_text(encoding='utf-8')
    
    # 檢查關鍵模式
    patterns = {
        "close_sub_window": "close_sub_window" in content,
        "chart_widget.cleanup": "chart_widget.cleanup()" in content,
        "deleteLater": "deleteLater()" in content,
        "removeSubWindow": "removeSubWindow" in content,
    }
    
    print(f"檔案: {mdi_file.name}")
    for pattern, exists in patterns.items():
        status = "✅" if exists else "❌"
        print(f"  {status} {pattern:30s} {'找到' if exists else '未找到'}")
    
    all_found = all(patterns.values())
    print(f"\n結果: {'✅ MDI 關閉邏輯完整' if all_found else '❌ MDI 關閉邏輯有缺失'}\n")
    
    return all_found


def search_cleanup_calls():
    """搜索 cleanup() 實際被調用的位置"""
    print("=" * 80)
    print("階段 3: 搜索 cleanup() 調用位置")
    print("=" * 80)
    
    search_dirs = [
        project_root / "modules" / "gui" / "lap_analysis",
    ]
    
    cleanup_calls = []
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        
        for py_file in search_dir.glob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # 搜索 cleanup() 調用
                if ".cleanup()" in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if ".cleanup()" in line and not line.strip().startswith('#'):
                            cleanup_calls.append((py_file.name, i, line.strip()))
            except Exception as e:
                print(f"⚠️  讀取檔案失敗 {py_file.name}: {e}")
    
    if cleanup_calls:
        print(f"找到 {len(cleanup_calls)} 處 cleanup() 調用:\n")
        for filename, line_num, line_content in cleanup_calls:
            print(f"  📄 {filename}:{line_num}")
            print(f"     {line_content}\n")
    else:
        print("❌ 沒有找到任何 cleanup() 調用！\n")
    
    return cleanup_calls


def analyze_cleanup_implementation():
    """分析 cleanup() 實作品質"""
    print("=" * 80)
    print("階段 4: 分析 cleanup() 實作品質")
    print("=" * 80)
    
    # 檢查一個範例檔案（Speed Analysis）
    chart_file = project_root / "modules" / "gui" / "lap_analysis" / "speed_analysis_chart_widget.py"
    
    if not chart_file.exists():
        print(f"❌ 找不到檔案: {chart_file}")
        return False
    
    content = chart_file.read_text(encoding='utf-8')
    
    # 搜索 cleanup() 方法內容
    cleanup_start = content.find("def cleanup(self):")
    if cleanup_start == -1:
        print("❌ 找不到 cleanup() 方法定義")
        return False
    
    # 提取 cleanup() 方法（簡單的縮排判斷）
    lines = content[cleanup_start:].split('\n')
    cleanup_lines = [lines[0]]  # def cleanup(self):
    
    for line in lines[1:]:
        if line and not line[0].isspace():
            break  # 遇到下一個非縮排行，結束
        cleanup_lines.append(line)
    
    cleanup_code = '\n'.join(cleanup_lines)
    
    # 檢查關鍵清理步驟
    checks = {
        "Matplotlib cleanup": "plt.close" in cleanup_code or "figure.clear()" in cleanup_code,
        "QTableWidget takeItem": "takeItem" in cleanup_code,
        "QTableWidget del item": "del item" in cleanup_code,
        "receiver deleteLater": "receiver.deleteLater()" in cleanup_code,
        "Data nullification": "= None" in cleanup_code,
        "Widget deleteLater": "chart_widget.deleteLater()" in cleanup_code,
    }
    
    print(f"檔案: {chart_file.name}")
    print(f"cleanup() 方法長度: {len(cleanup_lines)} 行\n")
    
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
    
    all_passed = all(checks.values())
    print(f"\n結果: {'✅ cleanup() 實作完整' if all_passed else '❌ cleanup() 實作有缺失'}\n")
    
    return all_passed


def suggest_targeted_test():
    """建議精確測試步驟"""
    print("=" * 80)
    print("階段 5: 建議的精確測試步驟")
    print("=" * 80)
    
    print("""
🎯 **單模組測試**（最重要）

步驟 1: 清空記憶體
  - 重新啟動 GUI
  - 在 Memory Diagnostics → 點擊「Snapshot State」（建立基準線）

步驟 2: 測試 Speed Analysis（單一模組）
  - Tools → Lap Analysis → Speed Analysis
  - 輸入參數：2024, Bahrain, R, VER, PER
  - 等待載入完成
  - Snapshot State（記錄開啟後的物件數）
  - **關閉 Speed Analysis 視窗**
  - 等待 2 秒
  - Snapshot State（記錄關閉後的物件數）

預期結果：
  - 開啟前: ~106,000 物件
  - 開啟後: ~108,500 物件 (+2,500)
  - 關閉後: ~106,200 物件 (+200)  ← **如果 cleanup() 有效**

如果關閉後仍有 +2,000 物件：
  → cleanup() 沒有被調用，或實作有問題


步驟 3: 查看終端輸出
  - 檢查是否有 cleanup() 的 debug 訊息
  - 例如：「[SPEED_CHART] ✅ Matplotlib 已清理」

如果沒有看到任何 cleanup 訊息：
  → MDI 關閉邏輯沒有調用 cleanup()


步驟 4: 重複測試（驗證穩定性）
  - 再次開啟 Speed Analysis
  - 再次關閉
  - Snapshot State
  - 檢查物件數是否穩定在 ~106,200 ±100


🔍 **多模組測試**（如果單模組測試通過）

步驟 1: 開啟 3 個不同模組
  - Speed Analysis
  - Brake Analysis  
  - Throttle Analysis

步驟 2: 逐一關閉
  - 關閉 Speed → Snapshot
  - 關閉 Brake → Snapshot
  - 關閉 Throttle → Snapshot

預期：每關閉一個模組，物件數應減少 ~2,300


📊 **檢查點**

如果單模組測試失敗：
  1. 檢查 MDI 是否調用 cleanup()
  2. 在 cleanup() 加入 print 輸出
  3. 檢查 chart_widget 屬性是否存在

如果多模組測試失敗（但單模組通過）：
  1. 檢查是否有共享資源（DataManager）
  2. 檢查模組間的交叉引用
  3. 檢查 API client 是否共享
""")


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║          Lap Analysis Cleanup 效果診斷工具                              ║
║                                                                          ║
║  目的：診斷為什麼 cleanup() 方法沒有有效減少物件洩漏                    ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
    
    # 執行診斷
    results = check_cleanup_method_exists()
    mdi_ok = check_mdi_cleanup_logic()
    cleanup_calls = search_cleanup_calls()
    impl_ok = analyze_cleanup_implementation()
    
    # 總結
    print("=" * 80)
    print("診斷總結")
    print("=" * 80)
    
    success_count = sum(1 for _, status, _, _ in results if status == "✅")
    
    print(f"✅ cleanup() 方法存在: {success_count}/9 個模組")
    print(f"{'✅' if mdi_ok else '❌'} MDI 關閉邏輯: {'完整' if mdi_ok else '有缺失'}")
    print(f"{'✅' if cleanup_calls else '❌'} cleanup() 調用: {len(cleanup_calls)} 處")
    print(f"{'✅' if impl_ok else '❌'} cleanup() 實作: {'完整' if impl_ok else '有缺失'}")
    
    print("\n" + "=" * 80)
    
    if success_count == 9 and mdi_ok and cleanup_calls and impl_ok:
        print("🎉 所有檢查都通過！")
        print("👉 下一步：進行單模組測試（見上方建議）")
    else:
        print("⚠️  發現問題！")
        if success_count < 9:
            print(f"   → {9 - success_count} 個模組缺少 cleanup() 方法")
        if not mdi_ok:
            print("   → MDI 關閉邏輯不完整")
        if not cleanup_calls:
            print("   → 沒有找到 cleanup() 調用（最嚴重！）")
        if not impl_ok:
            print("   → cleanup() 實作有缺失")
    
    print("\n")
    suggest_targeted_test()


if __name__ == "__main__":
    main()
