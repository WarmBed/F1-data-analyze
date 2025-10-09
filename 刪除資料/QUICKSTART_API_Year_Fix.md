# API 年份限制修復 - 快速指南

## ✅ 問題已解決

**問題**: API 返回 422 錯誤，拒絕 2020-2023 年的數據請求  
**原因**: API 參數驗證限制年份範圍為 2024-2025  
**修復**: 擴展年份範圍至 2020-2025（與 CLI 一致）

---

## 🚀 立即使用

### 1. 重啟 API 服務器（必須）

```powershell
# 如果 API 正在運行，請先停止（Ctrl+C）

# 重新啟動 API 服務器
python refactored_api.py

# 或使用 VS Code 任務
# 執行 "🌐 啟動 API 伺服器" 任務
```

**重要**: 修復後**必須重啟**服務器才能生效！

### 2. 驗證修復

執行測試腳本：
```powershell
python test_api_year_fix.py
```

**預期輸出**：
```
✅ 2023 年請求修復成功（原始問題已解決）
✅ 年份範圍邊界正確 (2020-2025)
✅ 超出範圍的年份正確拒絕
🎉 所有測試通過！API 年份限制修復成功！
```

---

## 📋 支援的年份

### ✅ 現在支援
- **2020** - ✅ 可用
- **2021** - ✅ 可用
- **2022** - ✅ 可用
- **2023** - ✅ 可用（原本失敗，現已修復）
- **2024** - ✅ 可用
- **2025** - ✅ 可用

### ❌ 仍然拒絕
- **2019 及更早** - ❌ 不支援（超出 F1 數據範圍）
- **2026 及以後** - ❌ 不支援（未來賽季）

---

## 🔧 修復的 API 端點

### 1. 主要分析執行
```
POST /api/v2/analysis/execute
```

**範例**（現在可以工作）：
```bash
# 2023 年巴林站正賽分析
curl -X POST "http://localhost:8000/api/v2/analysis/execute" \
  -d "function_id=13" \
  -d "year=2023" \
  -d "race=Bahrain" \
  -d "session=R" \
  -d "driver1=VER"
```

### 2. 緩存搜尋 v2
```
GET /api/v2/cache/search
```

**範例**（現在可以工作）：
```bash
# 搜尋 2022 年摩納哥站的緩存
curl "http://localhost:8000/api/v2/cache/search?function_id=13&year=2022&race=Monaco&session=R"
```

### 3. 緩存搜尋舊版
```
GET /api/cache/search
```

---

## 🧪 測試範例

### Python 測試
```python
import requests

# 測試 2023 年請求（原本失敗）
response = requests.post(
    "http://localhost:8000/api/v2/analysis/execute",
    params={
        "function_id": "99",
        "year": 2023
    }
)

print(f"狀態碼: {response.status_code}")  # 應該是 200
print(f"成功: {response.json()['success']}")  # 應該是 True
```

### cURL 測試
```bash
# 測試 2020 年（最小值）
curl "http://localhost:8000/api/v2/analysis/execute?function_id=99&year=2020"

# 測試 2023 年（原始問題）
curl "http://localhost:8000/api/v2/analysis/execute?function_id=99&year=2023"

# 測試 2025 年（最大值）
curl "http://localhost:8000/api/v2/analysis/execute?function_id=99&year=2025"
```

---

## ⚠️ 故障排除

### 問題：仍然收到 422 錯誤

**解決方案**：
1. 確認已重啟 API 服務器
2. 檢查請求的年份是否在 2020-2025 範圍內
3. 查看服務器日誌以獲取詳細錯誤信息

### 問題：無法連接到 API

**解決方案**：
```powershell
# 檢查 API 是否正在運行
Get-Process python | Where-Object {$_.ProcessName -like "*python*"}

# 如果沒有運行，啟動它
python refactored_api.py
```

### 問題：測試腳本失敗

**可能原因**：
1. API 服務器未啟動
2. 端口被占用（預設 8000）
3. 防火牆阻止連接

**檢查方法**：
```powershell
# 測試 API 健康狀態
curl http://localhost:8000/api/v2/health
```

---

## 📊 預期結果

### 修復前（422 錯誤）
```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["query", "year"],
      "msg": "Input should be greater than or equal to 2024",
      "input": "2023"
    }
  ]
}
```

### 修復後（200 成功）
```json
{
  "success": true,
  "message": "分析完成 (功能 99)",
  "data": {
    "2023": {
      "success": true,
      "message": "2023 賽季賽程查詢完成",
      "data": [...]
    }
  }
}
```

---

## 📚 技術細節

詳細的技術說明請參考：  
📄 **FIX_REPORT_API_Year_Limit_Removed.md**

---

## ✅ 驗證清單

使用前請確認：

- [ ] API 服務器已重啟
- [ ] 測試腳本執行成功
- [ ] 2023 年請求返回 200（不是 422）
- [ ] 2020 年請求返回 200
- [ ] 2019 年請求返回 422（應該拒絕）
- [ ] GUI 可以查詢歷史賽季

---

**修復版本**: 2025-10-07  
**狀態**: ✅ 已修復，待重啟服務器後生效  
**影響**: 所有使用 API 的應用程式現在可以訪問 2020-2025 完整歷史數據
