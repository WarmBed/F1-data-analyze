"""
單元測試：驗證 time.sleep(0.25) 已被移除
這是一個代碼檢查測試，不需要啟動 GUI
"""
import re
from pathlib import Path

def test_time_sleep_removed():
    """
    測試 1: 檢查 time.sleep(0.25) 是否已從 update_all_lap_analysis() 移除
    """
    print("=" * 80)
    print("🧪 測試 1: 檢查 time.sleep(0.25) 已移除")
    print("=" * 80)
    
    # 讀取檔案
    main_file = Path(__file__).parent / "f1t_gui_main.py"
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到 update_all_lap_analysis 函數
    pattern = r'def update_all_lap_analysis\(self\):.*?(?=\n    def |\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ 找不到 update_all_lap_analysis() 函數")
        return False
    
    function_code = match.group(0)
    
    print(f"\n✅ 找到函數，長度: {len(function_code)} 字符")
    
    # 檢查是否有 time.sleep（必須不在註解中）
    # 分行處理，排除註解行
    lines = function_code.split('\n')
    active_sleep_count = 0
    commented_sleep_count = 0
    
    for line in lines:
        # 檢查是否是註解行
        stripped = line.strip()
        if stripped.startswith('#'):
            # 完全註解的行
            if 'time.sleep' in line and '0.25' in line:
                commented_sleep_count += 1
        else:
            # 非註解行，檢查是否有 sleep
            # 但要排除行末註解的情況
            code_part = line.split('#')[0]  # 取註解前的部分
            if re.search(r'time\.sleep\s*\(\s*0\.25\s*\)', code_part):
                active_sleep_count += 1
            # 檢查註解部分是否提到 sleep
            if '#' in line:
                comment_part = line.split('#', 1)[1]
                if 'time.sleep' in comment_part and '0.25' in comment_part:
                    commented_sleep_count += 1
    
    print(f"\n🔍 檢查結果:")
    print(f"  實際執行的 time.sleep(0.25): {active_sleep_count} 個")
    print(f"  註解中的 time.sleep(0.25): {commented_sleep_count} 個")
    
    # 驗證
    if len(sleep_matches) == 0 and len(commented_matches) >= 1:
        print("\n✅ 測試通過：time.sleep(0.25) 已被正確移除（註解）")
        return True
    elif len(sleep_matches) == 0:
        print("\n✅ 測試通過：沒有找到 time.sleep(0.25)")
        print("⚠️ 注意：也沒有找到註解，可能已完全刪除")
        return True
    else:
        print(f"\n❌ 測試失敗：仍然存在 {len(sleep_matches)} 個未註解的 time.sleep(0.25)")
        
        # 顯示位置
        for i, match in enumerate(sleep_matches, 1):
            start = match.start()
            # 計算行號
            line_num = content[:match.start()].count('\n') + 1
            print(f"\n  位置 {i}:")
            print(f"    行號: {line_num}")
            
            # 顯示上下文
            context_start = max(0, start - 100)
            context_end = min(len(function_code), start + 100)
            context = function_code[context_start:context_end]
            print(f"    上下文: ...{context}...")
        
        return False

def test_qapplication_processevents_present():
    """
    測試 2: 確認 QApplication.processEvents() 仍然存在
    """
    print("\n" + "=" * 80)
    print("🧪 測試 2: 確認 QApplication.processEvents() 保留")
    print("=" * 80)
    
    main_file = Path(__file__).parent / "f1t_gui_main.py"
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到函數
    pattern = r'def update_all_lap_analysis\(self\):.*?(?=\n    def |\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ 找不到函數")
        return False
    
    function_code = match.group(0)
    
    # 檢查 processEvents
    process_events_pattern = r'QApplication\.processEvents\(\)'
    matches = list(re.finditer(process_events_pattern, function_code))
    
    print(f"\n🔍 檢查結果:")
    print(f"  QApplication.processEvents() 調用: {len(matches)} 次")
    
    if len(matches) > 0:
        print(f"\n✅ 測試通過：QApplication.processEvents() 仍然存在（{len(matches)} 次調用）")
        return True
    else:
        print("\n⚠️ 測試警告：沒有找到 QApplication.processEvents()")
        print("這可能影響 GUI 響應性")
        return False

def test_code_structure():
    """
    測試 3: 檢查代碼結構是否完整
    """
    print("\n" + "=" * 80)
    print("🧪 測試 3: 代碼結構完整性")
    print("=" * 80)
    
    main_file = Path(__file__).parent / "f1t_gui_main.py"
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'def update_all_lap_analysis\(self\):.*?(?=\n    def |\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ 找不到函數")
        return False
    
    function_code = match.group(0)
    
    # 檢查關鍵結構
    checks = {
        'QProgressDialog': r'QProgressDialog',
        '進度更新循環': r'for .* in .*modules_to_update',
        'update_lap_parameters 調用': r'update_lap_parameters\s*\(',
        '錯誤處理': r'except\s+Exception',
        '結果統計': r'updated_count|failed_count',
    }
    
    results = {}
    for name, pattern in checks.items():
        found = bool(re.search(pattern, function_code))
        results[name] = found
        status = "✅" if found else "❌"
        print(f"  {status} {name}: {'存在' if found else '缺失'}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n✅ 測試通過：所有關鍵結構都存在")
        return True
    else:
        missing = [k for k, v in results.items() if not v]
        print(f"\n❌ 測試失敗：缺少以下結構: {', '.join(missing)}")
        return False

def calculate_theoretical_improvement():
    """
    計算理論性能改善
    """
    print("\n" + "=" * 80)
    print("📊 理論性能改善計算")
    print("=" * 80)
    
    window_counts = [5, 10, 15, 20]
    sleep_per_window = 0.25  # 秒
    
    print("\n視窗數量  | 移除前浪費時間 | 改善幅度")
    print("-" * 45)
    
    for count in window_counts:
        wasted_time = count * sleep_per_window
        print(f"{count:2d} 個視窗  | {wasted_time:6.2f}s        | {wasted_time:6.2f}s")
    
    print("\n💡 結論:")
    print(f"  • 每個視窗移除 {sleep_per_window}s 延遲")
    print(f"  • 10 個視窗可節省 {10 * sleep_per_window}s")
    print(f"  • 20 個視窗可節省 {20 * sleep_per_window}s")
    
    baseline = 47.0  # 用戶報告的時間
    improvement = 10 * sleep_per_window
    
    print(f"\n📈 預期改善:")
    print(f"  • 基準時間: {baseline}s")
    print(f"  • 理論節省: {improvement}s")
    print(f"  • 預期時間: {baseline - improvement}s")
    print(f"  • 改善幅度: {(improvement / baseline) * 100:.1f}%")
    
    if improvement < 5:
        print(f"\n⚠️ 注意: 理論改善僅 {improvement}s，可能還有其他瓶頸需要解決")

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║  方案 1 代碼驗證：移除 time.sleep(0.25)                          ║
║  這是靜態代碼檢查，不需要啟動 GUI                                ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    results = {}
    
    # 執行測試
    results['sleep_removed'] = test_time_sleep_removed()
    results['processevents_present'] = test_qapplication_processevents_present()
    results['structure_intact'] = test_code_structure()
    
    # 計算理論改善
    calculate_theoretical_improvement()
    
    # 總結
    print("\n" + "=" * 80)
    print("📋 測試總結")
    print("=" * 80)
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n通過: {passed}/{total}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    if all(results.values()):
        print("\n🎉 所有測試通過！方案 1 已正確實施")
        print("\n下一步:")
        print("  1. 執行 GUI 測試驗證實際效果")
        print("  2. 如果改善不明顯，執行 Profiling 找出其他瓶頸")
        print("  3. 基於數據實施方案 2")
    else:
        print("\n⚠️ 部分測試失敗，請檢查代碼")
