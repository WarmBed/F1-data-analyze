import time
from modules.gui.themes import color_palette_provider

print("首次調用...")
start = time.time()
color_palette_provider.ensure_loaded(year=2025)
print(f"耗時: {time.time()-start:.3f}s")

print("\n連續1000次調用...")
start = time.time()
for _ in range(1000):
    color_palette_provider.ensure_loaded(year=2025)
elapsed = time.time() - start
print(f"總耗時: {elapsed:.3f}s")
print(f"平均每次: {elapsed/1000*1000:.3f}ms")

print(f"\n統計資訊:")
print(f"  總調用次數: {color_palette_provider._ensure_loaded_call_count}")
print(f"  緩存命中: {color_palette_provider._cache_hit_count}")
hit_rate = color_palette_provider._cache_hit_count / color_palette_provider._ensure_loaded_call_count * 100
print(f"  命中率: {hit_rate:.1f}%")
