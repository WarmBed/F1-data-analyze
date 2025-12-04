# 數據驗證路線圖 - 從歷史到即時

## 🎯 驗證策略

**核心原則**: 先用靜態歷史數據完全驗證邏輯，再接入即時 live 數據

---

## 📋 驗證階段規劃

### 階段 0: 現有驗證 ✅ **已完成**

**目標**: 驗證單一數據源（CarData.z）

**已完成的工作**:
- ✅ `extract_lap10_livetiming.py` - 下載並解碼 CarData.z
- ✅ 提取 HAM Lap 10 速度數據
- ✅ 與 FastF1 對比驗證
- ✅ 確認 `.z` 解碼邏輯正確（`wbits=-15`）

**驗證結果**:
```
Live Timing samples: 714
FastF1 samples: 714
Mean delta: ~2 km/h
```

**結論**: ✅ **CarData.z 解碼完全正確**

---

### 階段 1: 多數據源整合驗證 ⚠️ **建議下一步**

**目標**: 驗證三個核心數據源的整合邏輯

#### 1.1 下載所有需要的數據

```python
# test_multi_source_download.py
"""
驗證階段 1: 下載三個核心數據源
"""

BASE_URL = "https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/"

FILES_TO_DOWNLOAD = {
    "timing": "TimingData.jsonStream",      # 圈數來源
    "cardata": "CarData.z.jsonStream",      # 遙測數據
    "position": "Position.z.jsonStream",    # 位置數據
}

def download_all_sources():
    """下載所有數據源"""
    data = {}
    
    for key, filename in FILES_TO_DOWNLOAD.items():
        url = BASE_URL + filename
        print(f"📥 下載 {filename}...")
        
        response = requests.get(url, timeout=300)
        content = response.content.decode('utf-8-sig')
        
        # 保存到本地以便重複測試
        output_file = f"test_data_{key}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ 已保存到 {output_file}")
        data[key] = content
    
    return data

if __name__ == "__main__":
    data = download_all_sources()
    print(f"\n✅ 所有數據源下載完成！")
```

**驗證點**:
- [ ] TimingData.jsonStream 下載成功
- [ ] CarData.z.jsonStream 下載成功
- [ ] Position.z.jsonStream 下載成功
- [ ] 檔案大小合理（MB 級別）

---

#### 1.2 解析 TimingData（圈數來源）

```python
# test_timing_data_parse.py
"""
驗證階段 1.2: 解析 TimingData 提取圈數
"""

def parse_timing_data(content: str):
    """
    解析 TimingData.jsonStream
    提取所有車手的圈數資訊
    """
    lines = content.strip().split('\r\n')
    
    lap_records = []
    
    for line in lines:
        if not line:
            continue
        
        # 時間戳 + JSON
        timestamp = line[:12]
        json_data = json.loads(line[12:])
        
        # 提取圈數資訊
        if 'Lines' in json_data:
            for driver_no, driver_data in json_data['Lines'].items():
                lap_number = driver_data.get('NumberOfLaps')
                if lap_number:
                    lap_records.append({
                        'timestamp': timestamp,
                        'driver': driver_no,
                        'lap_number': int(lap_number),
                        'lap_time': driver_data.get('LastLapTime', {}).get('Value'),
                        'sector1': driver_data.get('Sectors', [{}])[0].get('Value'),
                        'sector2': driver_data.get('Sectors', [{}])[1].get('Value'),
                        'sector3': driver_data.get('Sectors', [{}])[2].get('Value'),
                    })
    
    df = pd.DataFrame(lap_records)
    return df

def test_timing_data():
    """測試 TimingData 解析"""
    with open('test_data_timing.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    df = parse_timing_data(content)
    
    print(f"📊 TimingData 解析結果:")
    print(f"   總記錄數: {len(df)}")
    print(f"   車手數量: {df['driver'].nunique()}")
    print(f"   圈數範圍: {df['lap_number'].min()} - {df['lap_number'].max()}")
    
    # 檢查 HAM (44) 的數據
    ham_data = df[df['driver'] == '44']
    print(f"\n🏎️ HAM 數據:")
    print(f"   總圈數: {len(ham_data)}")
    print(f"   Lap 10 存在: {'✅' if 10 in ham_data['lap_number'].values else '❌'}")
    
    # 顯示 Lap 9, 10, 11
    print(f"\n   Lap 9-11 詳細資訊:")
    for lap in [9, 10, 11]:
        lap_data = ham_data[ham_data['lap_number'] == lap]
        if not lap_data.empty:
            row = lap_data.iloc[0]
            print(f"   Lap {lap}: {row['timestamp']} | 圈速: {row['lap_time']}")
    
    return df

if __name__ == "__main__":
    df = test_timing_data()
    df.to_csv('parsed_timing_data.csv', index=False)
    print(f"\n✅ 已保存到 parsed_timing_data.csv")
```

**驗證點**:
- [ ] 能正確解析所有記錄
- [ ] `NumberOfLaps` 欄位存在且有效
- [ ] HAM Lap 10 能找到
- [ ] 時間戳格式正確（12 字元）

---

#### 1.3 計算圈時間範圍

```python
# test_lap_time_range.py
"""
驗證階段 1.3: 計算每圈的時間範圍
"""

def calculate_lap_time_ranges(timing_df: pd.DataFrame, driver: str = '44'):
    """
    計算每圈的開始/結束時間
    
    關鍵邏輯（複製 LiveF1）:
    - Lap N 開始時間 = Lap N-1 完成時間
    - Lap N 結束時間 = Lap N 完成時間
    """
    driver_data = timing_df[timing_df['driver'] == driver].copy()
    driver_data = driver_data.sort_values('lap_number')
    
    # 計算開始時間（前一圈的結束時間）
    driver_data['lap_start_time'] = driver_data['timestamp'].shift(1)
    driver_data['lap_end_time'] = driver_data['timestamp']
    
    # Lap 1 的開始時間設為最早的時間戳
    if not driver_data.empty:
        driver_data.loc[driver_data.index[0], 'lap_start_time'] = "000000000000"
    
    return driver_data

def test_lap_time_range():
    """測試圈時間範圍計算"""
    timing_df = pd.read_csv('parsed_timing_data.csv')
    
    ham_laps = calculate_lap_time_ranges(timing_df, driver='44')
    
    print(f"📊 HAM 圈時間範圍:")
    print(f"   總圈數: {len(ham_laps)}")
    
    # 顯示 Lap 9-11
    print(f"\n   Lap 9-11 時間範圍:")
    for lap in [9, 10, 11]:
        lap_data = ham_laps[ham_laps['lap_number'] == lap]
        if not lap_data.empty:
            row = lap_data.iloc[0]
            print(f"\n   Lap {lap}:")
            print(f"      開始: {row['lap_start_time']}")
            print(f"      結束: {row['lap_end_time']}")
            print(f"      圈速: {row['lap_time']}")
    
    return ham_laps

if __name__ == "__main__":
    ham_laps = test_lap_time_range()
    ham_laps.to_csv('ham_lap_time_ranges.csv', index=False)
    print(f"\n✅ 已保存到 ham_lap_time_ranges.csv")
```

**驗證點**:
- [ ] 每圈都有開始/結束時間
- [ ] Lap 10 的時間範圍正確
- [ ] 時間戳遞增順序正確

---

#### 1.4 在時間範圍內提取遙測數據

```python
# test_telemetry_extraction.py
"""
驗證階段 1.4: 在圈時間範圍內提取 CarData
"""

def extract_telemetry_for_lap(
    cardata_content: str,
    lap_start_time: str,
    lap_end_time: str,
    driver: str = '44'
):
    """
    在指定時間範圍內提取車手的遙測數據
    """
    lines = cardata_content.strip().split('\r\n')
    
    telemetry_records = []
    
    for line in lines:
        if not line or len(line) < 13:
            continue
        
        timestamp = line[:12]
        
        # 檢查時間範圍
        if timestamp <= lap_start_time or timestamp > lap_end_time:
            continue
        
        # 解碼 .z 數據
        decoded = decode_z_data(line[12:])
        if not decoded:
            continue
        
        # 提取該車手的數據
        for entry in decoded.get('Entries', []):
            if entry.get('Utc') != driver:
                continue
            
            # 提取遙測
            channels = entry.get('Cars', {}).get(driver, {}).get('Channels', {})
            
            telemetry_records.append({
                'timestamp': timestamp,
                'speed': channels.get('2'),      # 速度
                'rpm': channels.get('0'),        # RPM
                'gear': channels.get('3'),       # 檔位
                'throttle': channels.get('4'),   # 油門
                'brake': channels.get('5'),      # 煞車
            })
    
    return pd.DataFrame(telemetry_records)

def test_telemetry_extraction():
    """測試遙測提取"""
    # 讀取圈時間範圍
    ham_laps = pd.read_csv('ham_lap_time_ranges.csv')
    lap10 = ham_laps[ham_laps['lap_number'] == 10].iloc[0]
    
    print(f"🔍 提取 HAM Lap 10 遙測數據:")
    print(f"   時間範圍: {lap10['lap_start_time']} → {lap10['lap_end_time']}")
    
    # 讀取 CarData
    with open('test_data_cardata.txt', 'r', encoding='utf-8') as f:
        cardata_content = f.read()
    
    # 提取遙測
    telemetry = extract_telemetry_for_lap(
        cardata_content,
        lap10['lap_start_time'],
        lap10['lap_end_time'],
        driver='44'
    )
    
    print(f"\n📊 提取結果:")
    print(f"   數據點數: {len(telemetry)}")
    
    if len(telemetry) > 0:
        print(f"   速度範圍: {telemetry['speed'].min():.0f} - {telemetry['speed'].max():.0f} km/h")
        print(f"   前 5 筆數據:")
        print(telemetry.head())
    else:
        print(f"   ❌ 未找到任何數據！")
    
    return telemetry

if __name__ == "__main__":
    telemetry = test_telemetry_extraction()
    telemetry.to_csv('extracted_lap10_telemetry.csv', index=False)
    print(f"\n✅ 已保存到 extracted_lap10_telemetry.csv")
```

**驗證點**:
- [ ] 能在時間範圍內找到遙測數據
- [ ] 數據點數合理（應該 ~700 左右）
- [ ] 速度範圍與 FastF1 接近（69-309 km/h）

---

#### 1.5 與 FastF1 完整對比

```python
# test_full_comparison.py
"""
驗證階段 1.5: 完整對比驗證
"""

def compare_with_fastf1():
    """與 FastF1 完整對比"""
    # 讀取提取的遙測
    extracted = pd.read_csv('extracted_lap10_telemetry.csv')
    
    # 讀取 FastF1 數據
    fastf1_data = pd.read_csv('HAM_Lap10_telemetry.csv')
    
    print(f"📊 數據對比:")
    print(f"\n1. 數據點數對比:")
    print(f"   提取的數據: {len(extracted)}")
    print(f"   FastF1 數據: {len(fastf1_data)}")
    print(f"   差異: {abs(len(extracted) - len(fastf1_data))} ({abs(len(extracted) - len(fastf1_data)) / len(fastf1_data) * 100:.1f}%)")
    
    print(f"\n2. 速度範圍對比:")
    print(f"   提取的數據: {extracted['speed'].min():.0f} - {extracted['speed'].max():.0f} km/h")
    print(f"   FastF1 數據: {fastf1_data['Speed'].min():.0f} - {fastf1_data['Speed'].max():.0f} km/h")
    
    print(f"\n3. 驗證結果:")
    point_diff = abs(len(extracted) - len(fastf1_data))
    if point_diff < 50:
        print(f"   ✅ 數據點數接近（差異 < 50）")
    else:
        print(f"   ⚠️  數據點數差異較大（差異 = {point_diff}）")
    
    speed_match = (
        abs(extracted['speed'].min() - fastf1_data['Speed'].min()) < 5 and
        abs(extracted['speed'].max() - fastf1_data['Speed'].max()) < 5
    )
    if speed_match:
        print(f"   ✅ 速度範圍匹配")
    else:
        print(f"   ⚠️  速度範圍不匹配")

if __name__ == "__main__":
    compare_with_fastf1()
```

**驗證點**:
- [ ] 數據點數差異 < 50
- [ ] 速度範圍差異 < 5 km/h
- [ ] 整體邏輯正確性確認

---

### 階段 2: 完整 Medallion 架構驗證 🚧 **未來工作**

**目標**: 實作完整的 Bronze → Silver 數據湖

#### 2.1 Bronze Layer 儲存
- 原始數據按檔案分類儲存
- 時間戳索引建立

#### 2.2 Silver Layer 生成
- 自動化 ETL 管道
- laps 表格生成
- carTelemetry 表格生成

#### 2.3 查詢介面
- `get_laps()` 方法
- `get_car_telemetry()` 方法
- 圈數篩選功能

---

### 階段 3: 即時數據接入 🔮 **最終目標**

**目標**: 連接 SignalR WebSocket 接收即時數據

#### 3.1 SignalR 連線測試
- 協商 (Negotiate)
- WebSocket 連線
- 訂閱主題

#### 3.2 即時數據處理
- 接收即時數據流
- 即時解碼 .z 數據
- 即時寫入資料庫

#### 3.3 混合模式
- 歷史數據分析
- 即時數據監控
- 無縫切換

---

## 🎯 推薦執行順序

### 立即開始（今天）

```bash
# 步驟 1: 下載所有數據源
python test_multi_source_download.py

# 步驟 2: 解析 TimingData
python test_timing_data_parse.py

# 步驟 3: 計算圈時間範圍
python test_lap_time_range.py

# 步驟 4: 提取遙測數據
python test_telemetry_extraction.py

# 步驟 5: 完整對比驗證
python test_full_comparison.py
```

**預期結果**: 
- ✅ 確認能從 TimingData 提取圈數
- ✅ 確認時間範圍計算正確
- ✅ 確認能在範圍內提取遙測
- ✅ 與 FastF1 數據匹配

---

### 下一階段（本週）

1. 實作完整的數據載入器類別
2. 建立 Bronze Layer 儲存
3. 實作 Silver Layer ETL

---

### 最終階段（未來）

1. SignalR 連線實作
2. 即時數據處理
3. GUI 整合

---

## ✅ 驗證成功標準

### 階段 1 通過條件

- [ ] TimingData 解析成功率 > 99%
- [ ] HAM Lap 10 能精確定位
- [ ] 提取的遙測數據與 FastF1 差異 < 5%
- [ ] 速度範圍匹配（誤差 < 5 km/h）
- [ ] 數據點數接近（誤差 < 50 點）

### 階段 2 通過條件

- [ ] Bronze Layer 儲存完整無遺漏
- [ ] Silver Layer 自動生成成功
- [ ] 查詢介面功能正常
- [ ] 效能可接受（< 5 秒生成）

### 階段 3 通過條件

- [ ] SignalR 連線穩定
- [ ] 即時數據延遲 < 2 秒
- [ ] 無數據遺漏
- [ ] 長時間運行穩定

---

## 📝 總結

**當前狀態**: 階段 0 已完成 ✅

**下一步行動**: 執行階段 1.1-1.5 驗證多數據源整合

**預計時間**: 2-3 小時完成階段 1 全部驗證

**關鍵優勢**: 
- 使用靜態數據，可重複測試
- 不需要等待比賽直播
- 邏輯驗證完全獨立於即時連線

準備好開始階段 1 了嗎？我可以立即幫您生成測試腳本！
