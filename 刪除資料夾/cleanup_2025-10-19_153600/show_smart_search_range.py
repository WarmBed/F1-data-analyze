"""顯示智能搜索範圍邏輯的示例"""

# 模擬不同賽道的主直線段長度
tracks = [
    ("Monaco", 400),
    ("Singapore", 600),
    ("Azerbaijan", 200),  # Baku 主直線很長但這裡是VER的參考段
    ("Monza", 1100),
    ("Spa", 800),
    ("Silverstone", 750),
]

print("=" * 80)
print("🎯 智能搜索範圍計算")
print("=" * 80)
print(f"\n{'賽道':<15} {'主直線長度':<12} {'往前搜索':<12} {'搜索總範圍':<15} {'策略'}")
print("-" * 80)

for track_name, straight_length in tracks:
    # 應用智能邏輯
    if straight_length < 500:
        search_backward_distance = straight_length * 1.5
        strategy = "短直線 (1.5x)"
    elif straight_length < 1000:
        search_backward_distance = 800
        strategy = "中等直線 (固定800m)"
    else:
        search_backward_distance = 1000
        strategy = "長直線 (固定1000m)"
    
    search_forward_distance = 200
    total_search_range = search_backward_distance + straight_length + search_forward_distance
    
    print(f"{track_name:<15} {straight_length:>6}m      {search_backward_distance:>6.0f}m      {total_search_range:>8.0f}m      {strategy}")

print("\n" + "=" * 80)
print("✅ 策略說明:")
print("  • 短直線 (<500m): 往前延伸 1.5 倍直線長度（適應賽道特性）")
print("  • 中等直線 (500-1000m): 固定往前 800m（標準範圍）")
print("  • 長直線 (>1000m): 固定往前 1000m（避免搜索過遠）")
print("=" * 80)
