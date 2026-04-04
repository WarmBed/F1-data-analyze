# Assetto Corsa 環境建置與驗證指南

本指南協助您完成 Assetto Corsa (AC) 的環境建置，以便進行 **Phase 2 (模擬驗證)**。由於我們的程式碼目前針對 **RSS Formula Hybrid 2025** 模組進行優化，請務必按照以下步驟操作。

> [!IMPORTANT]
> **必要前置需求**：
> 1. Assetto Corsa (Steam 版)
> 2. Content Manager (CM)
> 3. Custom Shaders Patch (CSP)
> 4. **RSS Formula Hybrid X 2026** 車輛模組 (需購買或取得，這是目前 F1 模擬的標準)

## 步驟 1: 安裝必備工具與模組

1.  **安裝 Content Manager (CM)**
    *   這是一個比官方啟動器強大許多的替代啟動器。
    *   下載解壓縮後，將 `Content Manager.exe` 放在任意位置執行即可。

2.  **安裝 Custom Shaders Patch (CSP)**
    *   在 CM 中，前往 `Settings` > `Custom Shaders Patch`，點擊 "Install" 或更新到最新推薦版本。

3.  **安裝 RSS Formula Hybrid X 2026** (關鍵!)
    *   本專案的 `data_fusion.py` 已寫死使用此車輛模型 (`rss_formula_hybrid_x_2026`)。
    *   將下載的壓縮檔直接拖進 CM 視窗進行安裝，或者解壓縮到 `assettocorsa/content/cars/`。
    *   請確認 CM 中能看到這台車。

## 步驟 1.2: 安裝 F1 賽季塗裝 (Skins)

RSS 的車輛預設只有原廠塗裝。要讓畫面變成真正的 F1 2026：

1.  **下載**: 前往 **Overtake.gg** 搜尋：
    *   `"RSS Formula Hybrid X 2026 F1 2026 Skin Pack"`
    *   或 `"RSS Formula Hybrid X 2026 Liveries"`
2.  **安裝**:
    *   將下載的壓縮檔直接拖進 **Content Manager**。
    *   點擊 "Install"。
    *   (或者手動解壓到 `assettocorsa/content/cars/rss_formula_hybrid_x_2026/skins/`)

3.  **注意**: 安裝後，在選擇車輛時，您就可以選到 Red Bull, Ferrari 等真實隊伍的塗裝了。

4.  **安裝 2026 賽季塗裝 (Optional but Recommended)**
    *   為了讓 `entry_list.ini` 正確對應車隊，建議安裝 2026 F1 塗裝包 (Skin Pack)。
    *   若無塗裝，車輛仍會載入，但可能會顯示為全黑或預設塗裝。

## 步驟 1.5: 取得並安裝賽道 (關鍵)

Assetto Corsa 原廠並不包含 F1 澳洲站 (Albert Park) 的現代布局。您需要下載模組：

1.  **搜尋關鍵字**: 在 Google 或 **Overtake.gg** (前身為 RaceDepartment) 搜尋 `"Assetto Corsa Albert Park F1 2025"` 或 `"Melbourne Grand Prix Circuit 2025"`.
    *   推薦尋找 **Pyyer** 製作的 extension (通常需要一個基礎賽道)。
    *   或者尋找獨立的賽道包。
2.  **安裝方式**:
    *   下載後通常是一個壓縮檔 (`.zip` / `.7z` / `.rar`)。
    *   **最簡單安裝法**: 直接把壓縮檔拖進 **Content Manager** 視窗，右上角漢堡選單會變成綠色，點擊 "Install" 即可。
    *   **手動安裝法**: 解壓縮後，將資料夾放入 `assettocorsa/content/tracks/`。

> [!TIP]
> **哪裡可以下載全年度賽道？**
> 由於版權原因，通常沒有官方的「一鍵全下載」包。最快的方法是：
> 1.  Google 搜尋 **"Assetto Corsa F1 2024 Track Spreadsheet"** (或 2025)。通常會有玩家整理好的 Google 表格，裡面有每一站的下載連結。
> 2.  前往 **GTPlanet** 論壇的 Assetto Corsa 專區，那裡有非常完整的賽道列表。

## 步驟 2: 準備 AC Server

為了讓我們的 `entry_list.ini` 生效並控制所有 AI 的確切參數 (Ballast/Restrictor)，最簡單的方法是使用 CM 內建的 "Local Server" 功能。

1.  開啟 **Content Manager**。
2.  前往 **Server** 分頁。
3.  點擊左上角的 `+` 新增一個伺服器設定。
4.  **Entry List**: 這是我們程式產生的重點。
    *   稍後我們會將生成的內容貼到這裡，或直接替換檔案。

## 步驟 3: 生成模擬設定

回到我們的開發環境，執行 Phase 1 的腳本來生成設定檔。

```powershell
# 確保您已經有 2025 澳洲站 FP2 的數據
# python f1_analysis_modular_main.py -f 121 -y 2025 -r Australia -s FP2 (若還沒跑過)

# 執行模擬設定生成
python run_ac_simulation_phase1.py
```

執行成功後，您會在 `ac_sim_output/` 資料夾下看到：
- `sim_config_2025_Australia_FP2.json` (給人類看的摘要)
- `entry_list_2025_Australia_FP2.ini` (給 Server 用的)

## 步驟 4: 執行驗證 (Phase 2)

1.  找到生成的 `entry_list_2025_Australia_FP2.ini`。
2.  將其**內容複製**。
3.  回到 **Content Manager** > **Server** > **Entry List** 頁面。
4.  在列表區域右鍵選擇 "View in Folder" 或直接找到該 Server 設定的 `entry_list.ini` 進行覆蓋 (通常在 `%LOCALAPPDATA%\AcTools Content Manager\Progress\Servers\...` 下，或直接用 CM 介面匯入)。
    *   *最簡單的方法*：在 CM 的 Entry List 頁面，確認車輛選擇了 "RSS Formula Hybrid X 2026"，然後手動或透過工具匯入我們的設定。
    *   **注意**: 由於 CM 的 Entry List UI 操作較繁瑣，建議直接找到 Server 的設定檔資料夾，用我們的 ini 覆蓋原本的。

5.  **設定賽事**:
    *   Track: Albert Park (Australia)
    *   Sessions: Practice (或 Race), 設定 10-15 分鐘。
    *   Opponents: 20 (與我們的列表一致)。

6.  **點擊 "Run"** 啟動伺服器與遊戲。

7.  **觀察**:
    *   進入遊戲後，切換到觀察者模式 (Replay cameras)。
    *   觀察 **Verstappen (P1)** 與後段班車手的在大直線的速度差 (Top Speed)。
    *   觀察過彎時，加重 (Ballast) 的車輛是否明顯較慢。

## 下一步

執行完一場模擬後，請告訴我：
1.  Ballast (每10kg) 的影響是否太明顯？還是太無感？
2.  Restrictor (進氣限制) 對尾速的影響是否符合預期？

我將根據您的回饋調整 `data_fusion.py` 中的係數。
