# 速度模組最後 2 個洩漏修復計畫

## 🎯 目標

修復剩餘的 2 個記憶體洩漏：
1. SpeedAnalysisModule (+1)
2. SpeedChartWidget (+1)

## 🔍 問題分析

根據清理後的引用追蹤，仍有以下引用：
```
- dict: 1 個                        ← 模組的 __dict__？
- builtin_function_or_method: 1 個  ← Qt/Matplotlib 內建方法？
- frame: 1 個                       ← 執行幀（正常）
- cell: 1 個                        ← 閉包變數（正常）
```

## 📋 修復策略

### 策略 1：徹底清理 SpeedAnalysisModule 的 __dict__

在 `speed_analysis_mdi.py` 的 `cleanup()` 方法中添加：

```python
# 階段 7: 徹底清理模組自身的 __dict__（新增）
print(f"[SPEED_MDI] 🧹 階段 7: 清理模組 __dict__...")
try:
    # 保存必要的屬性
    essential_attrs = {'_module_id', '_module_name', '_version'}
    
    # 獲取所有屬性
    all_attrs = list(self.__dict__.keys())
    print(f"[SPEED_MDI] 🔍 __dict__ 共有 {len(all_attrs)} 個屬性")
    
    # 清理非必要屬性
    cleaned_count = 0
    for attr in all_attrs:
        if attr not in essential_attrs and not attr.startswith('__'):
            try:
                delattr(self, attr)
                cleaned_count += 1
            except Exception as e:
                print(f"[SPEED_MDI] ⚠️ 無法刪除屬性 {attr}: {e}")
    
    print(f"[SPEED_MDI] ✅ 已清理 {cleaned_count} 個屬性")
    print(f"[SPEED_MDI] 🔍 剩餘 {len(self.__dict__)} 個屬性")
    
except Exception as e:
    print(f"[SPEED_MDI] ⚠️ 清理 __dict__ 失敗: {e}")
```

### 策略 2：強化 SpeedChartWidget 的清理

在 `speed_analysis_chart_widget.py` 的 `cleanup()` 方法中添加：

```python
# 新增：徹底斷開所有連接
print(f"[SPEED_CHART] 🔌 斷開所有 Qt 連接...")
try:
    self.disconnect()
    print(f"[SPEED_CHART]   ✅ Qt 連接已斷開")
except Exception as e:
    print(f"[SPEED_CHART]   ⚠️ 斷開連接警告: {e}")

# 新增：清理 __dict__
print(f"[SPEED_CHART] 🧹 清理 __dict__...")
try:
    essential_attrs = set()  # SpeedChartWidget 沒有必要保留的屬性
    all_attrs = list(self.__dict__.keys())
    
    for attr in all_attrs:
        if not attr.startswith('__'):
            try:
                delattr(self, attr)
            except Exception as e:
                pass
    
    print(f"[SPEED_CHART]   ✅ __dict__ 已清理")
except Exception as e:
    print(f"[SPEED_CHART]   ⚠️ __dict__ 清理警告: {e}")
```

### 策略 3：確保從連動管理器解除註冊

檢查 SpeedChartWidget 是否正確解除註冊：

```python
# 在 SpeedChartWidget.cleanup() 開始處添加
if hasattr(self, 'linkage_manager') and self.linkage_manager:
    try:
        self.linkage_manager.unregister_module(self)
        print(f"[SPEED_CHART]   ✅ 已從連動管理器解除註冊")
    except Exception as e:
        print(f"[SPEED_CHART]   ⚠️ 解除註冊警告: {e}")
```

## 🧪 測試計畫

1. 實施修復
2. 清理 Python 緩存
3. 重啟 GUI
4. 開啟速度模組
5. 關閉速度模組
6. 檢查 objgraph 報告

### 預期結果

- SpeedAnalysisModule: +1 → 0 ✅
- SpeedChartWidget: +1 → 0 ✅
- GC 回收物件數: 0 → > 0 ✅

## 📝 執行順序

1. 修改 `speed_analysis_chart_widget.py` 的 `SpeedChartWidget.cleanup()`
2. 修改 `speed_analysis_mdi.py` 的 `SpeedAnalysisModule.cleanup()`
3. 清理緩存
4. 測試

---

**創建時間**：2025-10-15 20:15
**版本**：v3.4 Final Fix Plan
