# 🎯 根本原因分析：RPM 選擇 Fastest Lap 時自動彈出 Pitstop 視窗

**日期**: 2025-10-07  
**嚴重性**: ⚠️ **HIGH** - 嚴重影響用戶體驗  
**根本原因**: `_check_and_load_telemetry_if_needed` 方法違反 API-ONLY 政策

---

## 🔍 問題根源

### 觸發流程

用戶操作：**RPM 模組 → 選擇 Fastest Lap**

**完整調用鏈**：
```
1. 用戶選擇 "Fastest Lap" 選項
   ↓
2. RPMAnalysisModule._ensure_telemetry_data_for_fastest_laps()
   ↓
3. self._find_telemetry_analysis_file() → 返回 None (找不到 JSON)
   ↓
4. self._check_and_load_telemetry_if_needed() ← 💥 問題在這裡！
   ↓
5. 找到主視窗的 create_telemetry_analysis() 方法
   ↓
6. handler() ← 自動呼叫創建！
   ↓
7. 創建了遙測分析視窗（用戶誤認為是 Pitstop）
```

### 問題程式碼

**檔案**: `modules/gui/lap_analysis/rpm_analysis/rpm_analysis_mdi.py`  
**行數**: 794-841  
**方法**: `RPMAnalysisModule._check_and_load_telemetry_if_needed`

```python
def _check_and_load_telemetry_if_needed(self, year: Optional[str] = None,
                                        race: Optional[str] = None,
                                        session: Optional[str] = None) -> bool:
    """確保遙測分析資料符合 API-ONLY 政策"""
    try:
        # ... 省略檢查檔案部分 ...

        main_window = self._get_main_window()
        if main_window:
            for method_name in (
                "open_telemetry_analysis",
                "create_telemetry_analysis",        # ← 💥 這個！
                "create_telemetry_analysis_tab"     # ← 💥 這個！
            ):
                if hasattr(main_window, method_name):
                    handler = getattr(main_window, method_name)
                    try:
                        handler()  # ← 💥 自動呼叫！違反 API-ONLY 政策！
                        print(f"[RPM_MDI] 🚀 已透過主視窗觸發 {method_name}")
                        return True  # ← 返回成功，讓調用者以為數據已載入
                    except TypeError:
                        try:
                            handler(target_year, target_race, target_session)
                            print(f"[RPM_MDI] 🚀 已透過主視窗觸發 {method_name}（含參數）")
                            return True
                        except Exception as inner_error:
                            print(f"[RPM_MDI] ⚠️ 呼叫 {method_name} 失敗: {inner_error}")

        print("⚠️ [RPM_MDI] 未能自動載入遙測分析，請先使用主視窗遙測模組或 REST API 取得資料")
        return False

    except Exception as e:
        print(f"[ERROR] [RPM_MDI] _check_and_load_telemetry_if_needed 失敗: {e}")
        return False
```

### 為什麼這違反 API-ONLY 政策？

**API-ONLY 模式政策 (2025-10-03)**：
> GUI 模組絕不允許直接啟動 CLI 進程或執行緒，也不能自動創建其他視窗

**違規行為**：
1. ❌ 自動呼叫 `create_telemetry_analysis()` 創建視窗
2. ❌ 沒有用戶明確操作
3. ❌ 返回 `True` 讓調用者誤以為數據已成功載入

---

## 🛠️ 修復方案

### 方案 1: 完全禁用自動創建（推薦）

**策略**: 完全移除自動創建視窗的邏輯，遵循 API-ONLY 政策

```python
def _check_and_load_telemetry_if_needed(self, year: Optional[str] = None,
                                        race: Optional[str] = None,
                                        session: Optional[str] = None) -> bool:
    """確保遙測分析資料可用，遵循 API-ONLY 模式
    
    ⚠️ API-ONLY 模式：此方法只檢查本地 JSON 緩存，不自動創建視窗
    若數據不存在，應通過 API 或提示用戶手動操作
    """
    try:
        target_year = str(year or self.current_year or "").strip()
        target_race = (race or self.current_race or "").strip()
        target_session = str(session or self.current_session or "").strip()

        print(f"[RPM_MDI] 🔍 [API-ONLY] 檢查遙測分析本地緩存: {target_year} {target_race} {target_session}")

        # ✅ 允許：檢查本地 JSON 緩存
        telemetry_file = self._find_telemetry_analysis_file(
            year=target_year,
            race=target_race,
            session=target_session
        )
        if telemetry_file:
            print(f"[RPM_MDI] 📂 [API-ONLY] 找到本地遙測分析緩存: {telemetry_file}")
            return True

        # ❌ 禁止：自動創建視窗或啟動 CLI
        # 改為僅提示用戶通過 API 或主視窗遙測模組獲取數據
        print("⚠️ [RPM_MDI] [API-ONLY] 遙測分析數據不存在於本地緩存")
        print("💡 [RPM_MDI] [API-ONLY] 提示：請先透過主視窗遙測模組或 REST API 獲取遙測數據")
        print("💡 [RPM_MDI] [API-ONLY] 或者手動執行 CLI: python f1_analysis_modular_main.py -f 8")
        return False

    except Exception as e:
        print(f"[ERROR] [RPM_MDI] _check_and_load_telemetry_if_needed 失敗: {e}")
        return False
```

**優點**：
- ✅ 完全符合 API-ONLY 政策
- ✅ 不會自動彈出任何視窗
- ✅ 清晰的用戶提示
- ✅ 與 Brake 模組的修復保持一致

**缺點**：
- ⚠️ 用戶需要手動開啟遙測分析或通過 API 獲取數據

---

### 方案 2: 用戶確認對話框（備選）

**策略**: 詢問用戶是否要開啟遙測分析

```python
def _check_and_load_telemetry_if_needed(self, year: Optional[str] = None,
                                        race: Optional[str] = None,
                                        session: Optional[str] = None) -> bool:
    """確保遙測分析資料可用，遵循 API-ONLY 模式"""
    try:
        # ... 檢查本地檔案 ...
        
        if telemetry_file:
            return True

        # ✅ 改為詢問用戶
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "需要遙測分析數據",
            "使用最速圈功能需要遙測分析數據。\n\n"
            "是否要開啟遙測分析模組來獲取數據？\n\n"
            "（您也可以選擇「否」，然後通過 API 或 CLI 手動獲取數據）",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # 預設為「否」
        )

        if reply == QMessageBox.Yes:
            # 用戶明確同意，才創建視窗
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'open_telemetry_analysis'):
                main_window.open_telemetry_analysis()
                print(f"[RPM_MDI] ✅ 用戶確認後開啟遙測分析模組")
                return True

        print(f"[RPM_MDI] ℹ️ 用戶選擇不開啟遙測分析，請手動獲取數據")
        return False

    except Exception as e:
        print(f"[ERROR] [RPM_MDI] _check_and_load_telemetry_if_needed 失敗: {e}")
        return False
```

**優點**：
- ✅ 用戶有明確的選擇權
- ✅ 不會無預警彈出視窗
- ✅ 提供清晰的說明

**缺點**：
- ⚠️ 每次選擇 Fastest Lap 都會彈出對話框（可能煩人）
- ⚠️ 仍然違反「完全禁止自動創建」的嚴格解釋

---

## 🚀 推薦修復方案

**採用方案 1：完全禁用自動創建**

理由：
1. 與 Brake 模組已修復的邏輯保持一致
2. 完全符合 API-ONLY 政策
3. 避免任何意外的視窗彈出
4. 清晰的錯誤提示引導用戶正確操作

---

## 📋 需要修復的檔案

**相同問題可能存在於所有 lap_analysis 模組**：

1. ✅ **brake_analysis_mdi.py** - 已修復（參考實現）
2. ❌ **rpm_analysis_mdi.py** - 需要修復
3. ❌ **speed_analysis_mdi.py** - 需要檢查
4. ❌ **gear_analysis_mdi.py** - 需要檢查
5. ❌ **throttle_analysis_mdi.py** - 需要檢查
6. ❌ **acceleration_analysis_mdi.py** - 需要檢查
7. ❌ **speeddiff_analysis_mdi.py** - 需要檢查
8. ❌ **distancediff_analysis_mdi.py** - 需要檢查

---

## 🧪 測試計劃

### 測試案例 1: RPM 最速圈（問題重現）
```
步驟：
1. 開啟 RPM 分析視窗
2. 選擇 Fastest Lap
3. 預期結果：不應該自動彈出遙測分析或 Pitstop 視窗
4. 預期日誌：
   [RPM_MDI] ⚠️ [API-ONLY] 遙測分析數據不存在於本地緩存
   [RPM_MDI] 💡 [API-ONLY] 提示：請先透過主視窗遙測模組...
```

### 測試案例 2: 有遙測數據時的正常流程
```
步驟：
1. 先手動開啟遙測分析模組 → 生成 JSON
2. 開啟 RPM 分析視窗
3. 選擇 Fastest Lap
4. 預期結果：成功載入最速圈數據，不彈出任何視窗
5. 預期日誌：
   [RPM_MDI] 📂 [API-ONLY] 找到本地遙測分析緩存: ...
```

### 測試案例 3: 其他模組檢查
```
對每個 lap_analysis 模組重複測試案例 1
確保所有模組都不會自動彈出視窗
```

---

## 📝 修復腳本

已創建 `fix_rpm_auto_create_telemetry.py` 自動修復腳本

---

**診斷工程師**: GitHub Copilot  
**報告日期**: 2025-10-07  
**根本原因**: `_check_and_load_telemetry_if_needed` 違反 API-ONLY 政策，自動創建視窗  
**修復狀態**: 待執行
