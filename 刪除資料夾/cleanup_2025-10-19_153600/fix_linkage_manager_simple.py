"""
簡化批次添加 linkage_manager 解除註冊
=====================================
直接替換特定代碼片段
"""

from pathlib import Path

# 需要修復的模組配置
MODULES_TO_FIX = {
    "modules/gui/lap_analysis/brake_analysis/brake_analysis_mdi.py": {
        "widget": "brake_chart_widget",
        "prefix": "BRAKE"
    },
    "modules/gui/lap_analysis/gear_analysis/gear_analysis_mdi.py": {
        "widget": "gear_chart_widget",
        "prefix": "GEAR"
    },
    "modules/gui/lap_analysis/rpm_analysis/rpm_analysis_mdi.py": {
        "widget": "rpm_chart_widget",
        "prefix": "RPM"
    },
    "modules/gui/lap_analysis/timediff_analysis/timediff_analysis_mdi.py": {
        "widget": "timediff_chart_widget",
        "prefix": "TIMEDIFF"
    },
    "modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_mdi.py": {
        "widget": "speeddiff_chart_widget",
        "prefix": "SPEEDDIFF"
    },
    "modules/gui/lap_analysis/distancediff_analysis/distancediff_analysis_mdi.py": {
        "widget": "distancediff_chart_widget",
        "prefix": "DISTANCEDIFF"
    },
}


def fix_module(file_path: Path, widget_name: str, prefix: str) -> bool:
    """修復單個模組"""
    try:
        print(f"\n處理: {file_path.name}")
        
        if not file_path.exists():
            print(f"  ❌ 檔案不存在")
            return False
        
        content = file_path.read_text(encoding='utf-8')
        
        # 檢查是否已經有 linkage_manager
        if 'linkage_manager.unregister_module' in content:
            print(f"  ⚠️  已經有 linkage_manager 解除註冊，跳過")
            return False
        
        # 舊代碼模式（要替換的部分）
        old_pattern = f'''            if hasattr(self, '{widget_name}') and self.{widget_name}:
                # 清理圖表組件
                if hasattr(self.{widget_name}, 'cleanup'):
                    self.{widget_name}.cleanup()
                self.{widget_name}.deleteLater()'''
        
        # 新代碼（添加 linkage_manager 解除註冊）
        new_code = f'''            if hasattr(self, '{widget_name}') and self.{widget_name}:
                # 🔧 修復：從連動管理器中取消註冊圖表組件
                try:
                    from modules.gui.lap_analysis.linkage import linkage_manager
                    if linkage_manager:
                        linkage_manager.unregister_module(self.{widget_name})
                        print(f"[{prefix}_MDI] ✅ 已從連動管理器解除註冊圖表組件")
                except Exception as e:
                    print(f"[ERROR] [{prefix}_MDI] 從連動管理器解除註冊失敗: {{e}}")
                
                # 清理圖表組件
                if hasattr(self.{widget_name}, 'cleanup'):
                    self.{widget_name}.cleanup()
                self.{widget_name}.deleteLater()'''
        
        if old_pattern not in content:
            print(f"  ⚠️  找不到目標代碼模式")
            return False
        
        # 執行替換
        new_content = content.replace(old_pattern, new_code)
        
        if new_content == content:
            print(f"  ❌ 替換失敗")
            return False
        
        # 寫回檔案
        file_path.write_text(new_content, encoding='utf-8')
        print(f"  ✅ 成功添加 linkage_manager 解除註冊")
        return True
        
    except Exception as e:
        print(f"  ❌ 處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("批次添加 linkage_manager 解除註冊")
    print("=" * 80)
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for file_path_str, config in MODULES_TO_FIX.items():
        file_path = Path(file_path_str)
        result = fix_module(file_path, config['widget'], config['prefix'])
        
        if result:
            success_count += 1
        elif result is False:
            # 檢查是否是跳過
            content = file_path.read_text(encoding='utf-8') if file_path.exists() else ""
            if 'linkage_manager.unregister_module' in content:
                skip_count += 1
            else:
                fail_count += 1
    
    print("\n" + "=" * 80)
    print(f"處理完成！")
    print(f"  ✅ 成功: {success_count} 個")
    print(f"  ⚠️  跳過: {skip_count} 個")
    print(f"  ❌ 失敗: {fail_count} 個")
    print("=" * 80)
    
    if success_count > 0:
        print("\n🎉 修復完成！請重新測試記憶體洩漏。")
        print("\n測試步驟：")
        print("  1. 重啟 GUI")
        print("  2. Memory Diagnostics → Snapshot State（基準線）")
        print("  3. 開啟所有 9 個 Lap Analysis 模組")
        print("  4. 關閉所有模組")
        print("  5. Snapshot State（最終）")
        print("  6. 預期洩漏：<1,500 物件（vs 之前的 +2,669）")


if __name__ == "__main__":
    main()
