"""
Lap Time Box Plot vs Throttle Box Plot - 深度差異分析報告

執行日期: 2025-10-11
分析目的: 診斷為什麼 Lap Time Box Plot 的 filter 功能未生效

═══════════════════════════════════════════════════════════════════════════════
[1] 檔案結構比較
═══════════════════════════════════════════════════════════════════════════════

檔案大小:
- Throttle Box Plot: 21,151 bytes (573 行)
- Lap Time Box Plot:  28,897 bytes (794 行)
- 差異: +36.6% (Lap Time 更大)

方法數量:
- Throttle: 18 個方法
- Lap Time: 20 個方法
  
獨特方法:
- Throttle 獨有: leaveEvent (1 個)
- Lap Time 獨有: _draw_legend, _draw_title, clear_chart (3 個)

═══════════════════════════════════════════════════════════════════════════════
[2] Filter 功能核心組件檢查
═══════════════════════════════════════════════════════════════════════════════

✅ QMenu 導入
   Throttle: ✓ (from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QMenu)
   Lap Time: ✓ (from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QMenu)

✅ QCursor 導入
   Throttle: ✓ (from PyQt5.QtGui import ... QCursor)
   Lap Time: ✓ (from PyQt5.QtGui import ... QCursor)

✅ hidden_drivers 屬性
   Throttle: ✓ (self.hidden_drivers = set())
   Lap Time: ✓ (self.hidden_drivers = set())
   
   位置: 都在 __init__() 中初始化

✅ _calculate_y_range() 過濾邏輯
   Throttle: ✓ (16 行實現，包含 hidden_drivers 過濾)
   Lap Time: ✓ (同樣的過濾邏輯)

✅ _draw_box_plots() 過濾邏輯
   Throttle: ✓ (visible_drivers = [d for d in drivers if d not in self.hidden_drivers])
   Lap Time: ✓ (相同的過濾邏輯)

✅ mousePressEvent() 實現
   Throttle: ✓ (8 行，支援左鍵和右鍵)
   Lap Time: ✓ (7 行，支援左鍵和右鍵)

✅ _show_context_menu() 實現
   Throttle: ✓ (16 行)
   Lap Time: ✓ (16 行，邏輯完全相同)

✅ _hide_driver() 實現
   Throttle: ✓ (13 行)
   Lap Time: ✓ (13 行，邏輯完全相同)

✅ show_all_drivers() 實現
   Throttle: ✓ (12 行)
   Lap Time: ✓ (12 行，邏輯完全相同)

═══════════════════════════════════════════════════════════════════════════════
[3] 代碼片段出現次數統計
═══════════════════════════════════════════════════════════════════════════════

hidden_drivers:      Throttle: 10 次 | Lap Time: 10 次 ✅
QMenu:               Throttle:  2 次 | Lap Time:  2 次 ✅
QCursor:             Throttle:  2 次 | Lap Time:  2 次 ✅
visible_drivers =:   Throttle:  2 次 | Lap Time:  2 次 ✅
menu.exec_:          Throttle:  1 次 | Lap Time:  1 次 ✅

═══════════════════════════════════════════════════════════════════════════════
[4] 差異點分析
═══════════════════════════════════════════════════════════════════════════════

❌ Lap Time 獨有的額外方法:
   - _draw_legend(): 繪製圖例（但已被註釋掉）
   - _draw_title(): 繪製標題（但已被註釋掉）
   - clear_chart(): 清空圖表

❌ Lap Time 獨有的屬性:
   - self.hover_driver: 懸停車手追蹤
   - self.hover_position: 懸停位置追蹤

❌ Throttle 獨有的方法:
   - leaveEvent(): 滑鼠離開事件處理

⚠️ 潛在問題點:
   無！兩個檔案的 filter 核心邏輯完全一致。

═══════════════════════════════════════════════════════════════════════════════
[5] 理論驗證 - Filter 功能應該可以正常工作
═══════════════════════════════════════════════════════════════════════════════

理由 1: 所有關鍵方法都已實現
   ✅ mousePressEvent() - 捕獲右鍵點擊
   ✅ _show_context_menu() - 顯示選單
   ✅ _hide_driver() - 隱藏車手
   ✅ show_all_drivers() - 恢復所有車手

理由 2: 數據過濾邏輯完整
   ✅ _calculate_y_range() 過濾隱藏車手
   ✅ _draw_box_plots() 過濾隱藏車手
   ✅ hidden_drivers 集合正確管理

理由 3: 導入正確
   ✅ QMenu 已導入
   ✅ QCursor 已導入

理由 4: 與 Throttle 實現完全一致
   ✅ 代碼邏輯相同
   ✅ 方法調用相同

═══════════════════════════════════════════════════════════════════════════════
[6] 可能原因假設
═══════════════════════════════════════════════════════════════════════════════

假設 1: 用戶測試環境問題
   - GUI 可能使用的是舊的緩存版本
   - 需要重啟 GUI 以載入新代碼

假設 2: 滑鼠懸停檢測失效
   - self.hover_driver 可能未正確更新
   - mouseMoveEvent() 可能有問題

假設 3: 數據更新時機問題
   - update_data() 被調用時 hidden_drivers 可能被重置

假設 4: MDI 視窗整合問題
   - reset_chart_view() 方法可能有問題

═══════════════════════════════════════════════════════════════════════════════
[7] 診斷建議
═══════════════════════════════════════════════════════════════════════════════

步驟 1: 重啟 GUI
   - 強制重新載入所有模組

步驟 2: 檢查 mouseMoveEvent()
   - 確認 hover_driver 是否正確追蹤

步驟 3: 添加調試輸出
   - 在 mousePressEvent() 開頭添加 print()
   - 在 _show_context_menu() 添加 print()

步驟 4: 檢查 update_data() 方法
   - 確認是否意外清空 hidden_drivers

═══════════════════════════════════════════════════════════════════════════════
[8] 結論
═══════════════════════════════════════════════════════════════════════════════

✅ 代碼層面: Filter 功能已完整實現，邏輯完全正確
⚠️ 運行時問題: 可能是環境、緩存或滑鼠事件追蹤問題

建議: 創建測試腳本驗證 Lap Time Box Plot 的 filter 功能
"""
