"""讀取 GUI 錯誤日誌並顯示最近的錯誤"""
import codecs

log_file = "logs/f1_gui_error_2025-10-18.log"

# 嘗試不同的編碼
for encoding in ['utf-8', 'utf-8-sig', 'cp950', 'gbk']:
    try:
        with open(log_file, 'r', encoding=encoding, errors='ignore') as f:
            lines = f.readlines()
        
        print(f"使用編碼: {encoding}")
        print(f"總行數: {len(lines)}")
        print("\n最後 30 行:")
        print("=" * 80)
        
        for line in lines[-30:]:
            print(line.rstrip())
        
        break
    except Exception as e:
        print(f"嘗試編碼 {encoding} 失敗: {e}")
        continue
