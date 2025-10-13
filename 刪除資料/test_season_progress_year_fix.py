"""
測試 Season Progress 模組的 year 參數修復
驗證 tr() 函數的 .format() 調用是否正確傳入 year 參數
"""

import sys
from pathlib import Path

# 確保可以導入專案模組
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🧪 測試 Season Progress Year 參數修復")
print("=" * 80)

# 測試 1: 檢查修復後的代碼
print("\n測試 1: 檢查 populate_data 中的 tr() 調用...")
try:
    with open('modules/gui/season_progress/season_progress_widget.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查錯誤模式（已移除）
    if 'tr("season_progress_title", "Season Progress").format() + f" - {self.season_year}"' in content:
        print("❌ 仍存在錯誤模式：.format() 未傳入 year 參數")
    else:
        print("✅ 錯誤模式已移除")
    
    # 檢查正確模式
    if 'tr("season_progress_title"' in content and '.format(year=self.season_year)' in content:
        print("✅ 正確模式已實作：.format(year=self.season_year)")
    else:
        print("❌ 正確模式未找到")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 2: 檢查 i18n 定義
print("\n測試 2: 檢查 i18n 翻譯字串...")
try:
    with open('core/gui_i18n.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "'season_progress_title':" in content:
        # 提取翻譯定義
        start = content.find("'season_progress_title':")
        end = content.find('\n', start)
        line = content[start:end]
        
        print(f"✅ 找到翻譯定義")
        print(f"   {line.strip()}")
        
        if '{year}' in line:
            print("✅ 翻譯字串包含 {year} 佔位符")
        else:
            print("⚠️  翻譯字串未包含 {year} 佔位符")
    else:
        print("❌ 找不到 season_progress_title 翻譯")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")

# 測試 3: 模擬 populate_data 調用
print("\n測試 3: 模擬 populate_data 調用...")
try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    from modules.gui.season_progress.season_progress_widget import SeasonProgressWidget
    
    widget = SeasonProgressWidget()
    
    # 測試數據
    test_data = {
        "season_year": 2025,
        "round": 18,
        "calendar": {
            "completed": 18,
            "remaining": 6,
            "total": 24,
            "next_race": {
                "name": "United States Grand Prix",
                "date": "2025-10-20T19:00:00Z"
            }
        },
        "leaders": {
            "driver": {
                "full_name": "Oscar Piastri",
                "constructor": "McLaren",
                "points": 336.0
            },
            "constructor": {
                "name": "McLaren",
                "points": 650.0
            }
        }
    }
    
    # 調用 populate_data（這應該會觸發 tr() 和 .format()）
    try:
        widget.populate_data(test_data)
        print("✅ populate_data 調用成功，無 KeyError")
        
        # 檢查標題是否正確設置
        title_text = widget.title_label.text()
        if "2025" in title_text:
            print(f"✅ 標題包含年份：{title_text}")
        else:
            print(f"⚠️  標題未包含年份：{title_text}")
            
    except KeyError as e:
        print(f"❌ 仍存在 KeyError: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ 測試完成！")
print("=" * 80)

print("\n📋 修復總結：")
print("問題：tr('season_progress_title').format() 未傳入 year 參數")
print("      導致 KeyError: 'year'，因為 i18n 字串包含 {year} 佔位符")
print("")
print("修復：tr('season_progress_title').format(year=self.season_year)")
print("      正確傳入 year 參數給 .format() 方法")
print("")
print("參考：constructor_standings_widget.py 的正確實作")
