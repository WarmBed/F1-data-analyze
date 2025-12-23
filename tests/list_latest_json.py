import os
import glob

files = glob.glob('json/all_drivers_straight*.json')
files.sort(key=os.path.getmtime, reverse=True)

print("最新的 3 個 JSON 檔案:")
for i, file in enumerate(files[:3], 1):
    mtime = os.path.getmtime(file)
    from datetime import datetime
    time_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    print(f"{i}. {file}")
    print(f"   修改時間: {time_str}")
