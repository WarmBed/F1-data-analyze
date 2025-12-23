"""驗證 F121 已加入 API"""
from api.models.function_specs import FUNCTION_SPECS

f121 = FUNCTION_SPECS.get('121')

print("=" * 70)
print("F121 API 規格驗證")
print("=" * 70)
print()

if f121:
    print("✅ F121 已成功加入 API")
    print()
    
    print("【基本資訊】")
    print(f"  Function ID: {f121.function_id}")
    print(f"  名稱: {f121.name}")
    print(f"  描述: {f121.description[:100]}...")
    print()
    
    print("【必要參數】")
    for param in f121.required_params:
        print(f"  • {param}")
    print()
    
    print("【可選參數】")
    if f121.optional_params:
        for param in f121.optional_params:
            print(f"  • {param}")
    else:
        print("  (無)")
    print()
    
    print("【CLI 標誌映射】")
    for param, flag in f121.cli_flag_map.items():
        print(f"  • {param} → {flag}")
    print()
    
    print("【緩存模式】")
    for pattern in f121.cache_patterns:
        print(f"  • {pattern}")
    print()
    
    print("【備註】")
    print(f"  {f121.notes}")
    print()
    
    print("=" * 70)
    print("所有支援的 Function IDs:")
    all_ids = sorted(FUNCTION_SPECS.keys(), key=lambda x: int(x.split('.')[0]) if x.replace('.', '').isdigit() else 999)
    print(f"  總數: {len(all_ids)}")
    print(f"  範圍: {all_ids[:5]} ... {all_ids[-5:]}")
    print(f"  121 在列表中: {'121' in all_ids}")
    
else:
    print("❌ F121 未找到")

print("=" * 70)
