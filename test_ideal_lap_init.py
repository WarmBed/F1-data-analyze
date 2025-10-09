"""測試 IdealLapRankingTableMDI 新的初始化方式"""

from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_mdi import IdealLapRankingTableMDI

print("=" * 60)
print("測試 IdealLapRankingTableMDI 初始化")
print("=" * 60)

# 測試 1: 僅用 parent 參數初始化
print("\n[測試 1] 僅用 parent 參數初始化...")
try:
    module = IdealLapRankingTableMDI(parent=None)
    print(f"✅ 初始化成功！")
    print(f"   year={module.year}, race={module.race}, session={module.session}")
    print(f"   有 initialize_module 方法: {hasattr(module, 'initialize_module')}")
except Exception as e:
    print(f"❌ 初始化失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 2: 設置參數並初始化
print("\n[測試 2] 設置參數並調用 initialize_module()...")
try:
    module = IdealLapRankingTableMDI(parent=None)
    module.current_year = "2025"
    module.current_race = "Japan"
    module.current_session = "R"
    
    result = module.initialize_module()
    print(f"✅ initialize_module() 返回: {result}")
    print(f"   year={module.year}, race={module.race}, session={module.session}")
except Exception as e:
    print(f"❌ 初始化失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("測試完成！")
print("=" * 60)
