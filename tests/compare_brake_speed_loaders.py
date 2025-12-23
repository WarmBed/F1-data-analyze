#!/usr/bin/env python3
"""比較 Brake Performance 和 Straight Line Speed 的 Loader 邏輯"""

print("=" * 100)
print("All Drivers Brake Performance vs All Drivers Straight Line Speed Loader 比較")
print("=" * 100)

print("\n📂 檔案位置：")
print("  Brake:  modules/gui/all_drivers_brake_performance_analysis/brake_performance_loader.py")
print("  Speed:  modules/gui/lap_analysis/speed_analysis/straight_line_speed_loader.py")

print("\n" + "=" * 100)
print("1️⃣  load_data() 方法比較")
print("=" * 100)

brake_load_data = '''
def load_data(self, **kwargs) -> bool:
    """Load straight-line speed data, fetching from API when needed."""

    if not self._validate_load_parameters(kwargs):
        self._error(tr("brake_perf_load_param_validation_failed", "載入參數驗證失敗"))
        self.load_error.emit(tr("brake_perf_load_param_invalid", "載入參數不正確"))
        return False

    existing = self._find_data_file(**kwargs)
    if not existing:
        self._debug(tr("brake_perf_no_local_file", "找不到本地煞車性能檔案，準備透過 API 取得最新資料"))
        if not self._fetch_via_api_and_cache(**kwargs):
            return False

    return super().load_data(**kwargs)
'''

speed_load_data = '''
def load_data(self, **kwargs) -> bool:
    """Load straight-line speed data, fetching from API when needed."""

    if not self._validate_load_parameters(kwargs):
        self._error(tr("straight_speed_load_param_validation_failed", "載入參數驗證失敗"))
        self.load_error.emit(tr("straight_speed_load_param_invalid", "載入參數不正確"))
        return False

    existing = self._find_data_file(**kwargs)
    if not existing:
        self._debug(tr("straight_speed_no_local_file", "找不到本地直線速度檔案，準備透過 API 取得最新資料"))
        if not self._fetch_via_api_and_cache(**kwargs):
            return False

    return super().load_data(**kwargs)
'''

print("\n🟢 Brake Performance load_data():")
print(brake_load_data)

print("\n🔵 Straight Line Speed load_data():")
print(speed_load_data)

print("\n✅ 結論：兩者的 load_data() 邏輯【完全一致】！")
print("   - 都先驗證參數")
print("   - 都先搜尋本地檔案")
print("   - 找不到檔案時調用 API")
print("   - 最後調用 super().load_data()")

print("\n" + "=" * 100)
print("2️⃣  檔案名稱模式比較")
print("=" * 100)

print("\n🟢 Brake Performance 檔案模式:")
print('  ["all_drivers_brake_performance_*.json", "brake_performance_*.json"]')

print("\n🔵 Straight Line Speed 檔案模式:")
print('  ["all_drivers_straight_line_speed_*.json", "straight_line_speed_*.json"]')

print("\n✅ 結論：檔案模式結構【一致】，只是名稱不同")

print("\n" + "=" * 100)
print("3️⃣  CLI Function ID 比較")
print("=" * 100)

print("\n🟢 Brake Performance: cli_function='34'")
print("🔵 Straight Line Speed: cli_function='48'")

print("\n✅ 結論：各自使用正確的 Function ID")

print("\n" + "=" * 100)
print("4️⃣  _generate_data_via_cli() 比較")
print("=" * 100)

print("\n兩者都已禁用 CLI 調用：")
print('  self._debug("⚠️  [API-ONLY] CLI 調用已禁用 (Function XX)")')
print('  return False')

print("\n✅ 結論：CLI 調用邏輯【完全一致】")

print("\n" + "=" * 100)
print("📊 總結：Brake 和 Speed 的 Loader 邏輯【完全一致】")
print("=" * 100)

print("\n如果 Speed 能正常工作，Brake 也應該能正常工作！")
print("問題可能出在：")
print("  1. API 端點處理 Function 34 的方式不同")
print("  2. CLI 生成的 JSON 格式不同")
print("  3. 檔案搜尋時機的差異")
print("  4. MDI 初始化順序的差異")

print("\n建議：")
print("  1. 測試 Speed 是否有同樣的問題")
print("  2. 檢查 API 對 Function 34 的處理")
print("  3. 驗證 JSON 格式是否符合 _validate_data_format() 的預期")
