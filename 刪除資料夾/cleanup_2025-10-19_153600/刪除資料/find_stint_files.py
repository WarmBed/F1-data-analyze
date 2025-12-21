import json
import glob

files = glob.glob('json/*2025*Japan*.json')

print("=" * 80)
print("檢查哪些 JSON 檔案包含 'stint' 數據")
print("=" * 80)

for f in files[:15]:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = json.load(file)
            content_str = str(content)
            
            if 'stint' in content_str.lower():
                print(f"\n✅ {f}")
                print(f"   檔案大小: {len(content_str)} 字元")
                
                # 試著找出 stint 數據的位置
                if isinstance(content, dict):
                    for key in content.keys():
                        if 'stint' in key.lower() or ('data' in key and isinstance(content[key], dict)):
                            print(f"   可能的鍵: {key}")
    except Exception as e:
        print(f"❌ {f}: 錯誤 - {e}")
