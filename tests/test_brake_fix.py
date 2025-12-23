"""
Brake 模組修復驗證測試腳本

測試目標：
1. 驗證 update_lap_parameters 的 if-else 邏輯
2. 驗證 use_time_axis 儲存
3. 驗證參數變化檢測
"""

import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_brake_module_structure():
    """測試 Brake 模組結構"""
    print("=" * 80)
    print("測試: Brake 模組修復驗證")
    print("=" * 80)
    
    try:
        # 導入模組
        from modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi import BrakeAnalysisModule
        print("✅ Brake 模組導入成功")
        
        # 檢查關鍵方法存在
        assert hasattr(BrakeAnalysisModule, 'update_lap_parameters'), "❌ 缺少 update_lap_parameters 方法"
        print("✅ update_lap_parameters 方法存在")
        
        # 檢查 update_lap_parameters 簽名
        import inspect
        sig = inspect.signature(BrakeAnalysisModule.update_lap_parameters)
        params = list(sig.parameters.keys())
        
        required_params = ['self', 'year', 'race', 'session', 'driver1', 'driver2', 'lap1', 'lap2', 'is_fastest', 'use_time_axis']
        for param in required_params:
            assert param in params, f"❌ 缺少參數: {param}"
        print(f"✅ 方法簽名正確: {params}")
        
        # 檢查原始碼中的關鍵邏輯
        source = inspect.getsource(BrakeAnalysisModule.update_lap_parameters)
        
        # 檢查 1: 是否有 self.use_time_axis = use_time_axis
        assert 'self.use_time_axis = use_time_axis' in source, "❌ 缺少 use_time_axis 儲存"
        print("✅ 包含 'self.use_time_axis = use_time_axis'")
        
        # 檢查 2: 是否有 if params_changed:
        assert 'if params_changed:' in source, "❌ 缺少 params_changed 條件判斷"
        print("✅ 包含 'if params_changed:' 條件判斷")
        
        # 檢查 3: 是否有 else: 分支
        # 使用更寬鬆的檢查（考慮縮排）
        lines = source.split('\n')
        has_else = any('else:' in line and line.strip().startswith('else:') for line in lines)
        assert has_else, "❌ 缺少 else: 分支"
        print("✅ 包含 'else:' 分支")
        
        # 檢查 4: 是否有「參數未變化」的日誌
        assert '圈速參數未變化' in source or '參數未變化' in source, "❌ 缺少參數未變化日誌"
        print("✅ 包含參數未變化日誌")
        
        # 檢查 5: Exception 處理
        assert 'except Exception as e:' in source, "❌ 缺少 Exception 處理"
        print("✅ 包含 Exception 處理")
        
        # 檢查 6: 避免 traceback（檢查是否註釋）
        assert '# import traceback' in source or '# traceback.print_exc()' in source, "⚠️ traceback 可能未註釋"
        print("✅ traceback 已註釋（避免內存洩漏）")
        
        print("\n" + "=" * 80)
        print("✅ 所有結構測試通過！")
        print("=" * 80)
        
        # 輸出關鍵代碼片段
        print("\n[關鍵代碼片段]:")
        print("-" * 80)
        
        # 提取 if params_changed 區塊（簡化顯示）
        in_if_block = False
        if_block_lines = []
        indent_level = 0
        
        for line in lines:
            if 'if params_changed:' in line:
                in_if_block = True
                indent_level = len(line) - len(line.lstrip())
                if_block_lines.append(line)
            elif in_if_block:
                current_indent = len(line) - len(line.lstrip())
                if line.strip() and current_indent <= indent_level and not line.strip().startswith('#'):
                    # 遇到同層級或更低層級的非註釋行，結束
                    if 'else:' in line:
                        if_block_lines.append(line)
                        # 繼續收集 else 區塊的前幾行
                        for i in range(5):
                            if lines.index(line) + i + 1 < len(lines):
                                next_line = lines[lines.index(line) + i + 1]
                                if_block_lines.append(next_line)
                    break
                else:
                    if_block_lines.append(line)
        
        print("[if params_changed 邏輯]:")
        for line in if_block_lines[:30]:  # 最多顯示 30 行
            print(line.rstrip())
        
        if len(if_block_lines) > 30:
            print(f"    ... (省略 {len(if_block_lines) - 30} 行)")
        
        print("-" * 80)
        
        return True
        
    except ImportError as e:
        print(f"❌ 導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    except AssertionError as e:
        print(f"❌ 測試失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_speed_module():
    """對比 Speed 模組確認一致性"""
    print("\n" + "=" * 80)
    print("[與 Speed 模組對比]")
    print("=" * 80)
    
    try:
        from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule
        from modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi import BrakeAnalysisModule
        
        import inspect
        
        speed_source = inspect.getsource(SpeedAnalysisModule.update_lap_parameters)
        brake_source = inspect.getsource(BrakeAnalysisModule.update_lap_parameters)
        
        # 關鍵模式對比
        patterns = {
            'if params_changed:': 'params_changed 條件判斷',
            'else:': 'else 分支',
            'self.use_time_axis = use_time_axis': 'use_time_axis 儲存',
            '參數未變化': '參數未變化日誌',
            '# import traceback': 'traceback 註釋'
        }
        
        print("\n[關鍵模式對比]:")
        print(f"{'模式':<40} {'Speed':<10} {'Brake':<10} {'狀態':<10}")
        print("-" * 80)
        
        all_match = True
        for pattern, description in patterns.items():
            speed_has = pattern in speed_source
            brake_has = pattern in brake_source
            match = '✅ 一致' if speed_has == brake_has else '❌ 不一致'
            
            if speed_has != brake_has:
                all_match = False
            
            print(f"{description:<40} {'✅' if speed_has else '❌':<10} {'✅' if brake_has else '❌':<10} {match:<10}")
        
        print("-" * 80)
        
        if all_match:
            print("✅ 所有關鍵模式一致！")
        else:
            print("⚠️ 發現不一致模式，需要進一步檢查")
        
        return all_match
        
    except Exception as e:
        print(f"❌ 對比失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # 設置 UTF-8 輸出
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("\n")
    print(">> 開始 Brake 模組修復驗證")
    print("\n")
    
    # 測試 1: 結構測試
    structure_ok = test_brake_module_structure()
    
    # 測試 2: 對比測試
    comparison_ok = compare_with_speed_module()
    
    # 最終結果
    print("\n" + "=" * 80)
    print("[測試總結]")
    print("=" * 80)
    print(f"結構測試: {'✅ 通過' if structure_ok else '❌ 失敗'}")
    print(f"對比測試: {'✅ 通過' if comparison_ok else '❌ 失敗'}")
    print("=" * 80)
    
    if structure_ok and comparison_ok:
        print("\n>>> 所有測試通過！Brake 模組修復成功！")
        print("\n[下一步]:")
        print("  1. 執行 Python 環境功能測試")
        print("  2. 建置 EXE: .\\build_exe.ps1")
        print("  3. 執行 EXE 環境穩定性測試")
        sys.exit(0)
    else:
        print("\n>>> 測試失敗，需要進一步修復")
        sys.exit(1)
