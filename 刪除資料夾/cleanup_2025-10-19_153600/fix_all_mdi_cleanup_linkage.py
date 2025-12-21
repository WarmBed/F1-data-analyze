"""
批次修復所有 Lap Analysis MDI 的 cleanup() 方法
============================================
問題：缺少 linkage_manager 解除註冊，導致模組實例洩漏
解決：在 cleanup() 中添加 linkage_manager.unregister_module()
"""

import re
from pathlib import Path

# 需要修復的模組列表
MODULES_TO_FIX = [
    "modules/gui/lap_analysis/brake_analysis/brake_analysis_mdi.py",
    "modules/gui/lap_analysis/throttle_analysis/throttle_analysis_mdi.py",
    "modules/gui/lap_analysis/acceleration_analysis/acceleration_analysis_mdi.py",
    "modules/gui/lap_analysis/gear_analysis/gear_analysis_mdi.py",
    "modules/gui/lap_analysis/rpm_analysis/rpm_analysis_mdi.py",
    "modules/gui/lap_analysis/timediff_analysis/timediff_analysis_mdi.py",
    "modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_mdi.py",
    "modules/gui/lap_analysis/distancediff_analysis/distancediff_analysis_mdi.py",
]

# 需要添加的 linkage_manager 解除註冊代碼片段
LINKAGE_UNREGISTER_CODE = '''
            if hasattr(self, '{chart_widget_name}') and self.{chart_widget_name}:
                # 🔧 修復：從連動管理器中取消註冊圖表組件
                try:
                    from modules.gui.lap_analysis.linkage import linkage_manager
                    if linkage_manager:
                        linkage_manager.unregister_module(self.{chart_widget_name})
                        print(f"[{module_name}_MDI] ✅ 已從連動管理器解除註冊圖表組件")
                except Exception as e:
                    print(f"[ERROR] [{module_name}_MDI] 從連動管理器解除註冊失敗: {{e}}")
                
                # 清理圖表組件
                if hasattr(self.{chart_widget_name}, 'cleanup'):
                    self.{chart_widget_name}.cleanup()
                self.{chart_widget_name}.deleteLater()
'''


def get_chart_widget_name(file_path: Path) -> str:
    """從檔案路徑推斷圖表組件名稱"""
    module_name = file_path.parent.name.replace("_analysis", "")
    
    name_mapping = {
        "brake": "brake_chart_widget",
        "throttle": "throttle_chart_widget",
        "acceleration": "acceleration_chart_widget",
        "gear": "gear_chart_widget",
        "rpm": "rpm_chart_widget",
        "timediff": "timediff_chart_widget",
        "speeddiff": "speeddiff_chart_widget",
        "distancediff": "distancediff_chart_widget",
    }
    
    return name_mapping.get(module_name, f"{module_name}_chart_widget")


def get_module_prefix(file_path: Path) -> str:
    """從檔案路徑推斷模組前綴"""
    module_name = file_path.parent.name.replace("_analysis", "")
    return module_name.upper()


def check_has_linkage_unregister(content: str) -> bool:
    """檢查是否已經有 linkage_manager 解除註冊代碼"""
    return "linkage_manager.unregister_module" in content


def fix_cleanup_method(file_path: Path) -> bool:
    """修復單個檔案的 cleanup() 方法"""
    try:
        print(f"\n處理: {file_path.name}")
        
        if not file_path.exists():
            print(f"  ❌ 檔案不存在: {file_path}")
            return False
        
        content = file_path.read_text(encoding='utf-8')
        
        # 檢查是否已經有 linkage_manager 解除註冊
        if check_has_linkage_unregister(content):
            print(f"  ⚠️  已經有 linkage_manager 解除註冊代碼，跳過")
            return False
        
        # 獲取圖表組件名稱和模組前綴
        chart_widget_name = get_chart_widget_name(file_path)
        module_prefix = get_module_prefix(file_path)
        
        print(f"  📝 圖表組件: {chart_widget_name}")
        print(f"  📝 模組前綴: {module_prefix}")
        
        # 生成 linkage_manager 解除註冊代碼
        linkage_code = LINKAGE_UNREGISTER_CODE.format(
            chart_widget_name=chart_widget_name,
            module_name=module_prefix
        )
        
        # 尋找需要替換的模式（圖表組件清理部分）
        # 模式：if hasattr(self, 'xxx_chart_widget') and self.xxx_chart_widget:
        #           if hasattr(self.xxx_chart_widget, 'cleanup'):
        pattern = rf'''(if hasattr\(self, '{chart_widget_name}'\) and self\.{chart_widget_name}:\s*\n\s*# 清理圖表組件\s*\n\s*if hasattr\(self\.{chart_widget_name}, 'cleanup'\):)'''
        
        if not re.search(pattern, content):
            print(f"  ⚠️  找不到圖表組件清理代碼模式")
            print(f"  🔍 嘗試搜索簡化模式...")
            
            # 簡化模式：直接找 if hasattr(self, 'xxx_chart_widget')
            simple_pattern = rf'''(if hasattr\(self, '{chart_widget_name}'\) and self\.{chart_widget_name}:)'''
            match = re.search(simple_pattern, content)
            
            if match:
                print(f"  ✅ 找到簡化模式，開始替換...")
                # 替換：在 if hasattr 之前插入 linkage_manager 解除註冊代碼
                # 但保持原有的 if hasattr 檢查
                old_text = match.group(0)
                new_text = linkage_code.strip() + '\n'
                
                # 找到這行的縮排
                lines_before = content[:match.start()].split('\n')
                indent = len(lines_before[-1]) - len(lines_before[-1].lstrip())
                
                # 調整新代碼的縮排
                new_lines = []
                for line in new_text.split('\n'):
                    if line.strip():
                        new_lines.append(' ' * indent + line)
                    else:
                        new_lines.append(line)
                new_text = '\n'.join(new_lines)
                
                # 執行替換
                new_content = content[:match.start()] + new_text + '\n' + content[match.start():]
                
                # 寫回檔案
                file_path.write_text(new_content, encoding='utf-8')
                print(f"  ✅ 成功添加 linkage_manager 解除註冊代碼")
                return True
            else:
                print(f"  ❌ 找不到任何圖表組件清理代碼")
                return False
        
        # 執行替換
        new_content = re.sub(
            pattern,
            linkage_code.strip() + r'\n\1',
            content,
            flags=re.MULTILINE | re.DOTALL
        )
        
        if new_content == content:
            print(f"  ❌ 替換失敗，內容沒有變化")
            return False
        
        # 寫回檔案
        file_path.write_text(new_content, encoding='utf-8')
        print(f"  ✅ 成功添加 linkage_manager 解除註冊代碼")
        return True
        
    except Exception as e:
        print(f"  ❌ 處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("批次修復 Lap Analysis MDI cleanup() 方法")
    print("=" * 80)
    print(f"\n目標：在 cleanup() 中添加 linkage_manager.unregister_module()")
    print(f"原因：linkage_manager 持有模組引用，阻止垃圾回收\n")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for module_path in MODULES_TO_FIX:
        file_path = Path(module_path)
        result = fix_cleanup_method(file_path)
        
        if result is True:
            success_count += 1
        elif result is False and "已經有" in str(result):
            skip_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 80)
    print(f"處理完成！")
    print(f"  ✅ 成功: {success_count} 個")
    print(f"  ⚠️  跳過: {skip_count} 個")
    print(f"  ❌ 失敗: {fail_count} 個")
    print("=" * 80)


if __name__ == "__main__":
    main()
