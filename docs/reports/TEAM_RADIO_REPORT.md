# Team Radio 下載報告

## 📊 執行結果

### ✅ 成功完成的步驟

1. **數據流下載** ✅
   - 成功從 F1 官方 API 下載 `TeamRadio.jsonStream`
   - 檔案大小: 2.96 KB
   - 位置: `team_radio_data/TeamRadio_2025_Abu_Dhabi_R.jsonStream`

2. **數據解析** ✅
   - 成功解析 22 筆 TeamRadio 記錄
   - 輸出檔案: `team_radio_data/TeamRadio_2025_Abu_Dhabi_R_parsed.json`
   - 數據結構已正確識別

3. **統計資訊** ✅
   ```
   總記錄數: 22 筆
   涉及車手: 6 位
   
   車手語音次數:
   - 車手 4 (Lando Norris): 6 次
   - 車手 81 (Oscar Piastri): 6 次
   - 車手 1 (Max Verstappen): 5 次
   - 車手 63 (George Russell): 2 次
   - 車手 22 (Yuki Tsunoda): 2 次
   - 車手 5 (Charles Leclerc): 1 次
   ```

### ❌ 遇到的問題

**音檔下載失敗 - HTTP 403 (Forbidden)**

所有 22 個 .mp3 音檔都無法下載，服務器返回 403 錯誤。

**可能的原因**：

1. **需要 F1TV 訂閱認證**
   - TeamRadio 音檔可能是 F1TV Pro 訂閱者專屬內容
   - 需要有效的 `subscriptionToken` 或 access token

2. **受保護的內容**
   - F1 官方對音檔設置了訪問限制
   - 可能需要特定的 HTTP headers 或 cookies

3. **時效性限制**
   - 音檔可能只在賽事期間可用
   - 歷史數據可能已被移除或歸檔

## 📝 數據格式分析

### TeamRadio.jsonStream 結構

```json
{
  "Captures": {
    "1": {
      "Utc": "2025-12-07T12:55:26.6176005Z",
      "RacingNumber": "5",
      "Path": "TeamRadio/GABBOR01_5_20251207_165505.mp3"
    }
  }
}
```

或

```json
{
  "Captures": [
    {
      "Utc": "2025-12-07T12:24:28.178Z",
      "RacingNumber": "63",
      "Path": "TeamRadio/GEORUS01_63_20251207_162402.mp3"
    }
  ]
}
```

### 音檔命名規則

格式: `{DRIVER_CODE}{LAST_NAME}{NUM}_{RACING_NUM}_{DATE}_{TIME}.mp3`

範例:
- `MAXVER01_1_20251207_171228.mp3` (Max Verstappen, #1)
- `LANNOR01_4_20251207_170931.mp3` (Lando Norris, #4)
- `OSCPIA01_81_20251207_171436.mp3` (Oscar Piastri, #81)

## 🔧 解決方案

### 方案 1: 使用 F1TV 認證 (推薦)

需要：
1. 有效的 F1TV Pro 訂閱
2. 獲取 `subscriptionToken` 或 access token
3. 在 HTTP 請求中添加認證 headers

```python
headers = {
    'Authorization': f'Bearer {access_token}',
    'User-Agent': 'Mozilla/5.0...'
}
```

### 方案 2: 使用即時串流

在賽事進行時通過 SignalR WebSocket 連接獲取即時 TeamRadio：
- 需要即時訂閱（見 `signalrcore_client.py`）
- 可以在賽事期間錄製

### 方案 3: 替代資源

- F1 官方 YouTube 頻道的 Team Radio 精選
- 第三方 F1 數據服務（需付費）

## 💡 後續開發建議

### 短期 (已實現)

1. ✅ 下載 TeamRadio 數據流
2. ✅ 解析 URL 和車手資訊
3. ✅ 生成結構化 JSON 記錄

### 中期 (需要認證)

1. ⏳ 實現 F1TV 認證流程
2. ⏳ 成功下載 .mp3 檔案
3. ⏳ 實現音檔管理系統

### 長期 (進階功能)

1. ⏳ 語音轉文字（需要 SpeechRecognition）
2. ⏳ 語音播放器整合
3. ⏳ 即時 TeamRadio 錄製系統
4. ⏳ TeamRadio 時間軸視覺化

## 📦 輸出檔案

1. `team_radio_data/TeamRadio_2025_Abu_Dhabi_R.jsonStream`
   - 原始數據流（3 KB）

2. `team_radio_data/TeamRadio_2025_Abu_Dhabi_R_parsed.json`
   - 解析後的結構化數據（包含所有 URL 和元數據）

3. `team_radio_data/audio/`
   - 音檔儲存目錄（目前為空，因 403 錯誤）

4. `team_radio_data/transcripts/`
   - 轉錄文字儲存目錄（待實現）

## 🎯 結論

**目前功能狀態**：
- ✅ 可以成功獲取 TeamRadio 的**元數據**（URL、時間戳、車手編號）
- ❌ 無法下載實際的 **.mp3 音檔**（需要 F1TV 認證）
- ⏳ 語音轉文字功能已實現但無法測試

**要實現完整的 TeamRadio 下載和轉錄**，需要：
1. 取得 F1TV Pro 訂閱
2. 實現認證 token 獲取機制
3. 在 HTTP 請求中加入認證 headers

**目前可用的功能**：
- 查詢哪些車手在賽事中有 TeamRadio
- 統計各車手的語音次數
- 記錄語音時間戳
- 保存結構化的元數據供後續使用

---

**建立時間**: 2026-01-12  
**測試賽事**: 2025 Abu Dhabi Grand Prix (Race)  
**腳本**: `download_team_radio.py`
