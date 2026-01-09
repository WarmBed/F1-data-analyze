# -*- coding: utf-8 -*-
"""
測試 Yas Marina 進站損失配置
"""

from strategy_simulator.core.config_loader import ConfigLoader

# 初始化 ConfigLoader
loader = ConfigLoader()

# 測試 Yas Marina
print("=" * 70)
print("測試 Yas Marina 進站損失配置")
print("=" * 70)

track_config = loader.get_track_config("Yas Marina")

print(f"\n賽道名稱: {track_config.name}")
print(f"官方名稱: {track_config.official_name}")
print(f"綠旗進站損失: {track_config.pit_loss_green} 秒")
print(f"SC 進站損失: {track_config.pit_loss_sc} 秒")
print(f"VSC 進站損失: {track_config.pit_loss_vsc} 秒")

# 預期結果：
# 綠旗進站損失應該是 22.80 秒 (來自 F142 統計數據)
# 而不是 22.0 秒 (pit_loss_database.json 的預設值)

print("\n" + "=" * 70)
if abs(track_config.pit_loss_green - 22.80) < 0.1:
    print("✅ 成功！使用了 F142 統計數據 (22.80 秒)")
else:
    print(f"❌ 失敗！仍使用預設值 ({track_config.pit_loss_green} 秒)")
    print("   預期: 22.80 秒 (F142 統計數據)")
print("=" * 70)
