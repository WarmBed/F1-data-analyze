# 🏎️ FIA 官方資料收集指南

## 📋 官方資料來源

**唯一認可的資料來源：**
```
https://www.fia.com/documents/championships/fia-formula-one-world-championship-14
```

## ✅ 資料收集原則

### 1. **僅使用 FIA 官方文件**
- ✅ FIA 技術文件
- ✅ FIA Event Notes
- ✅ FIA Scrutineering Documents
- ❌ 禁止使用媒體報導（除非引用 FIA 來源）
- ❌ 禁止使用社群媒體資訊
- ❌ 禁止使用猜測或傳聞

### 2. **資料驗證標準**
- 必須有 FIA 文件編號
- 必須有官方發布日期
- 必須註明資料來源（PDF 檔名）

### 3. **資料完整性**
- 無法從 FIA 文件確認的升級 → 標記為「未確認」
- 部分資訊缺失 → 標記為「部分資訊」
- 完整資訊 → 標記為「已確認」

## 📥 資料收集流程

### 步驟 1: 訪問 FIA 文件頁面
```
https://www.fia.com/documents/championships/fia-formula-one-world-championship-14
```

### 步驟 2: 選擇分站
例如：JAPANESE GRAND PRIX → 點擊進入

### 步驟 3: 查找相關文件
需要檢查的文件類型：
- **Event Notes** - 賽事須知（可能包含新部件申報）
- **Technical Directives** - 技術指令（新技術規定）
- **Scrutineering Documents** - 技術檢驗文件
- **Stewards Decisions** - 幹事決定（技術違規）

### 步驟 4: 下載並分析 PDF
手動閱讀 PDF，尋找關鍵字：
- "new parts"
- "upgrade"
- "modified"
- "technical update"
- 車隊名稱 + 部件名稱

### 步驟 5: 記錄到資料庫
使用標準化格式：
```python
python upgrade_tracker.py --add "Red Bull Racing" "Japan" "front_wing" "aerodynamic" "新前翼設計 - FIA Doc: 2025_japan_event_notes.pdf"
```

## 🎯 Red Bull Racing 2025 資料收集計畫

### 已完成的分站（基於公開資訊和賽季模式）

| 分站 | 輪次 | 日期 | 升級項目 | 資料狀態 |
|------|------|------|----------|----------|
| Bahrain | 1 | 2025-03-02 | 開季升級包 | ⚠️ 需 FIA 文件確認 |
| Saudi Arabia | 2 | 2025-03-09 | 高速後翼 | ⚠️ 需 FIA 文件確認 |
| Japan | 4 | 2025-04-06 | 側箱+地板 | ⚠️ 需 FIA 文件確認 |
| Spain | 9 | 2025-06-01 | 第二代地板 | ⚠️ 需 FIA 文件確認 |

### 待收集的分站

需要訪問 FIA 網站並下載文件：
- [ ] Australia (Round 3)
- [ ] China (Round 5)
- [ ] Miami (Round 6)
- [ ] Emilia Romagna (Round 7)
- [ ] Monaco (Round 8)
- [ ] Canada (Round 10)
- [ ] Austria (Round 11)
- [ ] Great Britain (Round 12)
- [ ] Belgium (Round 13)
- [ ] Hungary (Round 14)
- [ ] Netherlands (Round 15)
- [ ] Italy (Round 16)
- [ ] Azerbaijan (Round 17)
- [ ] Singapore (Round 18)

## 📝 手動整理範本

### FIA 文件檢查清單（每站）

```markdown
## [分站名稱] - Round [X] - [日期]

### FIA 文件檢查
- [ ] Event Notes PDF 已下載
- [ ] Technical Directive 已檢查
- [ ] Scrutineering Documents 已檢查
- [ ] Stewards Decisions 已檢查

### 發現的升級（Red Bull Racing）
- 車手：VER / PER / 兩者
- 部件：[部件名稱]
- 類別：aerodynamic / mechanical / power_unit
- 描述：[詳細描述]
- FIA 來源：[PDF 檔名 + 頁碼]

### 資料品質
- [ ] 已確認：完整的 FIA 文件證據
- [ ] 部分確認：間接證據
- [ ] 未確認：無 FIA 文件證據
```

## 🔍 實際案例：如何從 FIA 文件識別升級

### 案例 1: Event Notes 中的新部件申報

FIA 文件通常這樣記錄：
```
Team: Red Bull Racing
Car Number: 1 (VER)
New Parts: Front Wing Endplates (Spec 2)
Modification: Aerodynamic optimization for high-speed circuits
```

記錄為：
```python
python upgrade_tracker.py --add "Red Bull Racing" "Bahrain" "front_wing_endplate" "aerodynamic" "Spec 2 前翼端板 - FIA Event Notes Doc 1"
```

### 案例 2: Technical Directive 禁止某升級

如果 FIA 發布技術指令禁止某設計：
```
Technical Directive 025/2025
Subject: Flexible Floor Edge
All teams must modify floor edge by Spain GP
```

這表示所有車隊將在 Spain 有升級！

### 案例 3: Scrutineering Document 中的新部件

賽前技術檢驗文件可能列出：
```
Scrutineering Check - Red Bull RB21 #1
New Components:
- Rear Wing Main Plane (Monaco Spec)
- Floor Edge (Revision 3)
```

## ⚠️ 注意事項

### 資料收集限制

1. **FIA 不會公開所有升級**
   - 車隊有權保密部分技術細節
   - 某些升級不需要向 FIA 申報
   - 內部升級（如軟體、設定）不會記錄

2. **文件發布延遲**
   - FIA 文件可能在比賽後數天才發布
   - 技術細節可能經過編輯
   - 某些文件可能不公開

3. **需要專業判斷**
   - 技術術語需要理解
   - 某些升級需要推測（例如：floor modification 具體是什麼？）
   - 車隊聲明 vs FIA 記錄可能不一致

### 資料完整性聲明

由於以上限制，我們的資料庫將包含：
- ✅ **已確認**：有明確 FIA 文件證據
- ⚠️  **推測**：基於賽季模式和常見升級週期
- ❌ **無資料**：FIA 未公開或無法確認

## 🎯 目前狀態

### Red Bull Racing 2025 資料狀態

```
總升級項目：20 項
資料來源：
  - FIA 官方文件：0 項（待收集）
  - 賽季模式推測：20 項
  - 待驗證：100%
```

### 下一步行動

1. **立即行動**：訪問 FIA 網站下載已結束分站的文件
2. **持續追蹤**：每場比賽後檢查 FIA 文件
3. **資料更新**：用 FIA 文件替換推測資料

## 📚 參考資源

### FIA 文件類型說明

- **Event Notes**: 賽前發布，包含賽道資訊、特殊規定
- **Technical Directive**: 技術規則的官方解釋
- **Scrutineering Documents**: 賽前技術檢驗結果
- **Stewards Decisions**: 賽中/賽後的處罰決定
- **Technical Report**: 賽後技術檢驗報告

### 升級部件分類（FIA 標準）

**Aerodynamic (空氣動力)**
- Front Wing (前翼)
- Rear Wing (後翼)
- Floor (地板)
- Diffuser (擴散器)
- Sidepod (側箱)
- Beam Wing
- Endplates (端板)

**Mechanical (機械)**
- Suspension (懸吊)
- Brake Ducts (煞車風道)
- Cooling System (散熱系統)
- Steering (轉向系統)

**Power Unit (動力單元)**
- ICE (內燃機)
- MGU-K
- MGU-H
- Turbo (渦輪)
- Energy Store (電池)

---

**最後更新**: 2025-11-06  
**資料來源政策**: 僅使用 FIA 官方文件  
**維護者**: F1T 開發團隊
