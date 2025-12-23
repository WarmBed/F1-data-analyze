#!/usr/bin/env python3
"""
深度對比分析：Brake Performance vs All Drivers Speed vs Ideal Lap Analysis
API 調用 CLI 生成時的等待邏輯對比
"""

print("=" * 100)
print("API 調用 CLI 生成時的等待邏輯 - 三模組深度對比")
print("=" * 100)

# ========== 層級 1: API 服務器端 (Backend) ==========
print("\n" + "=" * 100)
print("📊 層級 1: API 服務器端 (Backend) - 統一處理所有 Function")
print("=" * 100)

print("\n📂 檔案: api/services/simple_analysis_service.py")
print("   方法: _run_cli_async()")

print("\n🔧 CLI 執行超時設定:")
print("   - 超時時間: timeout = 180.0 秒 (3 分鐘)")
print("   - 適用範圍: **所有 Function** (包括 34, 48, Ideal Lap 等)")
print("   - 執行方式: asyncio.subprocess (非阻塞)")
print("   - 等待邏輯: await asyncio.wait_for(process.wait(), timeout=180.0)")

print("\n⚙️  CLI 執行流程:")
print("   1. 創建子進程: aio_subprocess.create_subprocess_exec()")
print("   2. 非阻塞讀取輸出: 持續讀取 stdout/stderr 並更新進度")
print("   3. 等待進程完成: 最多等待 180 秒")
print("   4. 超時處理: 如果超過 180 秒，kill 進程並返回超時錯誤")
print("   5. 成功處理: exit_code == 0 → 等待 0.5 秒 → 重新搜尋緩存")

print("\n📝 關鍵代碼片段:")
print("""
    async def _run_cli_async(self, request_id, spec, params, timeout: float = 180.0):
        # 1. 啟動 CLI 子進程
        process = await aio_subprocess.create_subprocess_exec(
            *cmd,
            stdout=aio_subprocess.PIPE,
            stderr=aio_subprocess.PIPE,
        )
        
        # 2. 非阻塞讀取輸出（持續更新進度）
        async def _read_stream(stream, accumulator, stream_name):
            while True:
                line = await stream.readline()
                if not line:
                    break
                # 更新進度...
        
        # 3. 等待進程完成（最多 180 秒）
        try:
            await asyncio.wait_for(process.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()  # 超時則強制終止
            return {"success": False, "error": "CLI 執行超時"}
        
        # 4. 檢查返回碼
        if exit_code == 0:
            # 成功：等待 0.5 秒讓檔案寫入完成
            await asyncio.sleep(0.5)
            # 重新搜尋緩存
            refreshed_data = await asyncio.to_thread(
                self.cache_service.search_cached_analysis, ...
            )
            return {"success": True, "cli_info": {...}}
""")

print("\n✅ 結論：API 端對所有 Function 使用【統一的等待邏輯】，無差異！")

# ========== 層級 2: GUI Loader 端 (Frontend) ==========
print("\n" + "=" * 100)
print("📊 層級 2: GUI Loader 端 (Frontend) - 各模組的 API 請求超時")
print("=" * 100)

print("\n📋 三模組 GUI Loader 超時設定對比:")

print("\n" + "-" * 100)
print("🟢 1. Brake Performance (Function 34)")
print("-" * 100)
print("   📂 檔案: modules/gui/all_drivers_brake_performance_analysis/brake_performance_loader.py")
print("   🔧 超時設定: self._api_timeout = 45.0 秒")
print("   📝 API 調用:")
print("""
       response = requests.post(
           endpoint,
           params=params,
           timeout=self._api_timeout,  # 45.0 秒
           headers={"Accept": "application/json"},
       )
   """)

print("\n" + "-" * 100)
print("🔵 2. All Drivers Straight Line Speed (Function 48)")
print("-" * 100)
print("   📂 檔案: modules/gui/lap_analysis/speed_analysis/straight_line_speed_loader.py")
print("   🔧 超時設定: self._api_timeout = 45.0 秒")
print("   📝 API 調用:")
print("""
       response = requests.post(
           endpoint,
           params=params,
           timeout=self._api_timeout,  # 45.0 秒
           headers={"Accept": "application/json"},
       )
   """)

print("\n" + "-" * 100)
print("🟡 3. Ideal Lap Analysis (Telemetry Base)")
print("-" * 100)
print("   📂 檔案: modules/gui/lap_analysis/telemetry_data_loader_base.py")
print("   🔧 超時設定: self._api_timeout = 75.0 秒")
print("   📝 API 調用:")
print("""
       # 注意：Ideal Lap 使用 min(timeout, 10.0) 限制！
       timeout = getattr(self, "_api_timeout", 75.0)
       timeout = min(timeout, 10.0)  # 實際只有 10 秒！
       
       response = requests.post(
           url,
           json=payload,
           timeout=timeout,  # 只有 10 秒！
           headers={"Accept": "application/json"},
       )
   """)

print("\n" + "=" * 100)
print("📊 層級 2 總結：GUI Loader 超時設定對比表")
print("=" * 100)

print("\n┌─────────────────────────────┬────────────────┬────────────────┬──────────────┐")
print("│ 模組                        │ 設定超時       │ 實際超時       │ 檔案位置     │")
print("├─────────────────────────────┼────────────────┼────────────────┼──────────────┤")
print("│ Brake Performance           │ 45.0 秒        │ 45.0 秒        │ brake_...    │")
print("│ All Drivers Speed           │ 45.0 秒        │ 45.0 秒        │ straight_... │")
print("│ Ideal Lap Analysis          │ 75.0 秒        │ **10.0 秒！**  │ telemetry... │")
print("└─────────────────────────────┴────────────────┴────────────────┴──────────────┘")

print("\n⚠️  **重要發現：Ideal Lap Analysis 的實際超時只有 10 秒！**")
print("   - 設定值：75.0 秒")
print("   - 實際值：min(75.0, 10.0) = **10.0 秒**")
print("   - 位置：telemetry_data_loader_base.py 第 684 行")

# ========== 層級 3: 完整數據流分析 ==========
print("\n" + "=" * 100)
print("📊 層級 3: 完整數據流分析 - 從 GUI 到 API 到 CLI 的完整路徑")
print("=" * 100)

print("\n🟢 Brake Performance 完整流程:")
print("   1. GUI 調用 loader.load_data()")
print("   2. Loader 搜尋本地檔案 → 找不到")
print("   3. Loader 調用 _fetch_via_api_and_cache()")
print("   4. 發送 HTTP POST 到 API (timeout=45秒)")
print("      ↓")
print("   5. API 接收請求 → execute_analysis()")
print("   6. API 調用 _run_cli_async() (timeout=180秒)")
print("   7. CLI 子進程執行 Function 34")
print("   8. API 等待 CLI 完成 (最多 180 秒)")
print("   9. CLI 完成 → API 等待 0.5 秒")
print("   10. API 重新搜尋緩存 → 找到 JSON")
print("   11. API 返回 JSON 給 GUI")
print("      ↓")
print("   12. GUI Loader 收到響應 (在 45 秒內)")
print("   13. Loader 寫入本地緩存")
print("   14. Loader 調用 super().load_data() → 再次搜尋檔案")
print("   15. 找到檔案 → 載入成功 ✅")

print("\n🔵 All Drivers Speed 完整流程:")
print("   【完全相同！】")

print("\n🟡 Ideal Lap Analysis 完整流程:")
print("   【大部分相同，但 GUI 超時只有 10 秒！】")
print("   ⚠️  問題：如果 CLI 執行超過 10 秒，GUI 會超時！")

# ========== 層級 4: 超時層級分析 ==========
print("\n" + "=" * 100)
print("📊 層級 4: 超時層級分析 - 誰會先超時？")
print("=" * 100)

print("\n┌──────────────────────┬───────────────┬───────────────┬───────────────┐")
print("│ 超時層級             │ Brake/Speed   │ Ideal Lap     │ 說明          │")
print("├──────────────────────┼───────────────┼───────────────┼───────────────┤")
print("│ GUI HTTP 請求超時    │ 45 秒         │ **10 秒**     │ requests.post │")
print("│ API CLI 執行超時     │ 180 秒        │ 180 秒        │ asyncio.wait  │")
print("│ 實際瓶頸             │ GUI 45 秒     │ **GUI 10 秒** │ 最短者        │")
print("└──────────────────────┴───────────────┴───────────────┴───────────────┘")

print("\n📝 超時優先級：")
print("   1. **GUI 請求超時** (requests.post timeout)")
print("      - Brake/Speed: 45 秒")
print("      - Ideal Lap: **10 秒** (⚠️  最短！)")
print("   ")
print("   2. **API CLI 執行超時** (asyncio.wait_for timeout)")
print("      - 所有模組: 180 秒")
print("   ")
print("   ➡️  實際瓶頸：**GUI 的 requests.post timeout**")
print("   ➡️  Brake/Speed 會在 45 秒超時，Ideal Lap 會在 10 秒超時")

# ========== 層級 5: 問題診斷 ==========
print("\n" + "=" * 100)
print("🔍 層級 5: 問題診斷 - 為什麼 Brake 會失敗？")
print("=" * 100)

print("\n❓ 問題現象：")
print("   - GUI log 顯示「API 返回失敗：分析執行失敗」")
print("   - 但 CLI log 顯示成功生成 JSON")
print("   - 最終 GUI 還是成功載入了數據")

print("\n🔍 可能原因分析：")

print("\n【原因 1】CLI 執行時間接近或超過 45 秒：")
print("   - GUI 請求在 45 秒時超時")
print("   - API 仍在執行 CLI (有 180 秒時間)")
print("   - CLI 完成後生成 JSON")
print("   - GUI 第二次搜尋檔案時找到了 JSON")
print("   ➡️  時間線：GUI 超時 (45s) → CLI 完成 (50s) → GUI 重新載入 (成功)")

print("\n【原因 2】API 緩存搜尋失敗：")
print("   - CLI 成功執行並生成 JSON")
print("   - API 的 cache_service.search_cached_analysis() 沒找到檔案")
print("   - API 返回「CLI 執行成功但未找到輸出文件」錯誤")
print("   - GUI 收到錯誤後，自己搜尋本地檔案 → 找到了！")
print("   ➡️  檔案搜尋邏輯：API 沒找到 ≠ 檔案不存在")

print("\n【原因 3】檔案寫入延遲：")
print("   - CLI 完成後立即返回")
print("   - API 只等待 0.5 秒就搜尋緩存")
print("   - 檔案系統可能還在緩衝寫入")
print("   - API 搜尋時檔案尚未完全寫入 → 找不到")
print("   - GUI 稍後搜尋時檔案已完全寫入 → 找到了")
print("   ➡️  時間差：API 搜尋 (0.5s 後) 失敗 → GUI 搜尋 (1-2s 後) 成功")

# ========== 總結 ==========
print("\n" + "=" * 100)
print("📊 總結：Brake Performance 與其他模組的邏輯差異")
print("=" * 100)

print("\n✅ **相同點：**")
print("   1. API 端處理邏輯完全相同 (統一的 _run_cli_async)")
print("   2. GUI Loader 的 load_data() 邏輯完全相同")
print("   3. 檔案搜尋模式結構相同")
print("   4. CLI 執行超時都是 180 秒")

print("\n⚠️  **差異點：**")
print("   1. GUI HTTP 請求超時：")
print("      - Brake/Speed: 45 秒 ✅")
print("      - Ideal Lap: 10 秒 ⚠️  (太短！)")
print("   ")
print("   2. API 緩存搜尋邏輯：")
print("      - 可能在某些情況下搜尋失敗")
print("      - 但 GUI 的本地搜尋能找到檔案")

print("\n💡 **建議修正方案：**")
print("   1. 增加 API 等待檔案寫入時間（0.5s → 1.0s）")
print("   2. 改進 API 緩存搜尋邏輯（檔案名稱匹配）")
print("   3. Ideal Lap Analysis 增加超時時間（10s → 45s）")
print("   4. 統一所有模組的超時設定（都改為 60 秒）")

print("\n" + "=" * 100)
print("✅ 分析完成！")
print("=" * 100)
