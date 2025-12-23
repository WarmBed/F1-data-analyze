"""簡單測試：驗證新的直線段識別邏輯"""

# 模擬速度數據
speeds_data = {
    0: 85, 1: 90, 2: 100, 3: 120, 4: 150, 5: 180, 6: 210,
    7: 240, 8: 261, 9: 270, 10: 280, 11: 295, 12: 310,
    13: 320, 14: 325, 15: 328,  # 最高點
    16: 328, 17: 327, 18: 320, 19: 280, 20: 200  # 減速
}

print("=" * 80)
print("模擬直線段識別邏輯測試")
print("=" * 80)

# 找到最高速度點
max_speed_idx = max(speeds_data, key=speeds_data.get)
max_speed = speeds_data[max_speed_idx]

print(f"\n步驟 1: 找到最高速度點")
print(f"  位置: {max_speed_idx}")
print(f"  速度: {max_speed} km/h")

# 向前回推找起點
segment_start_idx = None
segment_start_speed = None

for i in range(max_speed_idx - 1, -1, -1):
    current_speed = speeds_data[i]
    next_speed = speeds_data[i + 1]
    
    # 檢查是否還在加速階段
    if next_speed > current_speed and current_speed > 80:
        segment_start_idx = i
        segment_start_speed = current_speed
    else:
        break

print(f"\n步驟 2: 向前回推找起點")
print(f"  位置: {segment_start_idx}")
print(f"  速度: {segment_start_speed} km/h")

# 向後延伸找終點
segment_end_idx = max_speed_idx
for i in range(max_speed_idx + 1, len(speeds_data)):
    current_speed = speeds_data[i]
    prev_speed = speeds_data[i - 1]
    
    # 允許速度下降 ≤5 km/h
    if current_speed >= prev_speed - 5:
        segment_end_idx = i
    else:
        break

print(f"\n步驟 3: 向後延伸找終點")
print(f"  位置: {segment_end_idx}")
print(f"  速度: {speeds_data[segment_end_idx]} km/h")

# 驗證直線段
speed_gain = max_speed - segment_start_speed
print(f"\n步驟 4: 驗證直線段")
print(f"  速度增益: {speed_gain} km/h")
print(f"  是否有效: {speed_gain > 100}")

print("\n" + "=" * 80)
print("結論")
print("=" * 80)
print(f"直線段範圍: {segment_start_idx} → {segment_end_idx}")
print(f"速度範圍: {segment_start_speed} → {max_speed} km/h")
print(f"✅ 成功捕捉最高速度 {max_speed} km/h（舊邏輯可能只有 261 km/h）")
