import matplotlib.pyplot as plt
import numpy as np

# 設定圖表風格
plt.style.use('bmh')

# 模擬數據：圈數 15 到 35
laps = np.arange(15, 36)

# 基礎設定
base_pace_old = 90.0  # 舊胎基礎速度
base_pace_new = 88.0  # 新胎基礎速度
deg_per_lap = 0.1     # 每圈衰退
pit_loss = 22.0       # 進站損失時間 (In-lap + Pit time cost)

# --------------------------
# Driver A (領跑者 - 晚進站 - Victim)
# 進站圈：Lap 24
# --------------------------
times_a = []
for lap in laps:
    if lap < 24: # 使用舊胎
        time = base_pace_old + (lap - 15) * deg_per_lap
    elif lap == 24: # 進站圈 (包含進站損失)
        time = base_pace_old + (lap - 15) * deg_per_lap + pit_loss
    else: # Lap 25+ 使用新胎
        time = base_pace_new + (lap - 25) * deg_per_lap
    times_a.append(time)

# --------------------------
# Driver B (追趕者 - 早進站 - Attacker)
# 進站圈：Lap 21 (Undercut)
# --------------------------
times_b = []
for lap in laps:
    if lap < 21: # 使用舊胎 (假設跟隨在前車後面，速度略慢或相同)
        time = base_pace_old + (lap - 15) * deg_per_lap + 0.2
    elif lap == 21: # 進站圈 (Undercut!)
        time = base_pace_old + (lap - 15) * deg_per_lap + pit_loss
    else: # Lap 22+ 使用新胎 (Undercut 黃金期)
        # 關鍵：新胎前幾圈通常非常快
        time = base_pace_new + (lap - 22) * deg_per_lap
    times_b.append(time)

# 繪圖
plt.figure(figsize=(12, 7))

# 繪製曲線
plt.plot(laps, times_a, 'r-o', linewidth=2, label='Driver A (Leader - Pits Lap 24)')
plt.plot(laps, times_b, 'b-o', linewidth=2, label='Driver B (Attacker - Pits Lap 21)')

# 標記 Undercut 區域
# Driver B 在 Lap 22, 23 是新胎，Driver A 在 Lap 22, 23 是舊胎
# 這是時間差拉開的關鍵
plt.axvspan(21.5, 23.5, color='yellow', alpha=0.3, label='Undercut Window (The "Push" Laps)')

# 添加註解
plt.annotate('Driver B Pits (Undercut)', xy=(21, 112), xytext=(16, 115),
             arrowprops=dict(facecolor='blue', shrink=0.05))
plt.annotate('Driver A Pits (Response)', xy=(24, 112), xytext=(26, 115),
             arrowprops=dict(facecolor='red', shrink=0.05))

plt.annotate('Key Gain: B is ~2s/lap faster here!', xy=(22.5, 89), xytext=(24, 95),
             arrowprops=dict(facecolor='black', arrowstyle='->'))

# 設置標籤
plt.title('F1 Undercut Strategy: Lap Time Analysis', fontsize=14)
plt.xlabel('Race Lap', fontsize=12)
plt.ylabel('Lap Time (Seconds) - Lower is Faster', fontsize=12)
plt.legend()
plt.grid(True)

# 顯示
plt.tight_layout()
plt.show()