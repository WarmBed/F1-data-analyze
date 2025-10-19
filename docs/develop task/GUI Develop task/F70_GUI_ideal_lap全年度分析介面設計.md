# 🖥️ 功能 70 GUI 介面設計：全年度車手一致性分析

**功能 ID**: 70  
**GUI 模組名稱**: Season Driver Consistency Analysis  
**開發狀態**: 📋 規劃階段  
**依賴後端**: CLI 功能 70 (JSON 數據輸出)  
**目標賽季**: 2025  
**框架**: PyQt5 + Matplotlib

---

## 📊 GUI 設計方案

### 主布局 (Dashboard Layout)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 🏁 2025 賽季車手一致性分析                                      [匯出報告] [?]      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  篩選: [2025 ▼] [所有賽事 ▼] [正賽 Race ▼]              已載入: 24 場賽事          │
├────────────────────────┬────────────────────────────────────────────────────────────┤
│ 🏆 車手一致性排名表     │ 📊 核心指標總覽                                            │
│ ┌──┬─────┬────────┐   │ ┌─────────┬─────────┬─────────┬─────────┐                │
│ │排│車手 │一致性  │   │ │平均差距 │完美圈率 │分段一致 │改善趨勢 │                │
│ │名│     │分數    │   │ ├─────────┼─────────┼─────────┼─────────┤                │
│ ├──┼─────┼────────┤   │ │ 0.082s  │ 33.3%   │ 94.5%   │ ↗ +0.15│                │
│ │1 │ VER │ 95.2   │◄─┐│ │  🟢     │  🟢     │  🟢     │  🟢    │                │
│ │2 │ NOR │ 93.8   │  ││ │ 第 1/20 │ 第 1/20 │ 第 1/20 │賽季最佳│                │
│ │3 │ LEC │ 91.5   │  ││ └─────────┴─────────┴─────────┴─────────┘                │
│ │4 │ PIA │ 90.8   │  ││                                                           │
│ │..│ ... │ ...    │  ││ 📈 賽季趨勢圖 (Season Trend - Mean Gap)                   │
│ └──┴─────┴────────┘  ││  差距│                                                    │
│                       ││  (s) │                                                    │
│ 🎯 選中: VER          ││ 0.20 │              ●                                     │
│ [詳細數據] [對比車手] ││ 0.10 │  ●  ●  ●        ●  ●  ●                           │
│                       ││ 0.00 ├──┬──┬──┬──┬──┬──┬──────────                       │
│                       ││      BHR SAU AUS JPN CHN MIA ...                         │
├───────────────────────┴┴───────────────────────────────────────────────────────────┤
│ 📊 多維度分析 (Multi-Dimensional Analysis)                                         │
│ [Tab 1: 四指標雷達圖] [Tab 2: 完美圈分析] [Tab 3: 分段熱力圖] [Tab 4: 改善趨勢]   │
│ [Tab 5: 詳細數據表] ◄─ 新增：完整統計數據                                          │
│                                                                                     │
│  🎯 四核心指標雷達圖 (4-Metric Radar Chart)                                        │
│                    Mean Gap (0-100)                                                │
│                          100                                                       │
│                           │                                                        │
│                        95 ●  ← VER                                                 │
│                        /  │  \                                                     │
│      Trend      80 ●──────┼──────● 80    Perfect Rate                             │
│      Score         │      │      │                                                 │
│      (0-100)       │      ●      │       (0-100)                                   │
│                 40 ●──────┼──────● 40                                              │
│                           │                                                        │
│                 Sector Consistency (0-100)                                         │
│                                                                                     │
│  圖例: ─── VER  ─── NOR  ─── LEC  ─── 全體平均                         [切換車手]  │
│                                                                                     │
│  💡 提示: 點擊 Tab 5 查看完整統計數據表                                            │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📑 Tab 詳細設計

### Tab 1: 四指標雷達圖 (4-Metric Radar Chart)

**功能**：多維度車手對比
**組件**：
- 雷達圖 (Matplotlib Polar Plot)
- 車手排名表
- 車手選擇器 (多選)

**實現重點**：
```python
# modules/gui/season_consistency/radar_chart_widget.py
class RadarChartWidget(QWidget):
    def plot_radar(self, driver_data: dict):
        # 4 個軸: Mean Gap, Perfect Rate, Sector Consistency, Trend
        categories = ['平均差距', '完美圈率', '分段一致性', '改善趨勢']
        
        # 正規化到 0-100
        values = [
            self._normalize_mean_gap(driver_data['mean_gap']),
            driver_data['perfect_lap_rate'],
            driver_data['sector_consistency_score'],
            self._normalize_trend(driver_data['trend_slope'])
        ]
```

---

### Tab 2: 完美圈分析 (Perfect Lap Analysis)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Tab 2: 完美圈分析 (Perfect Lap Analysis)                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│ ┌──────────────────────────────┐  ┌──────────────────────────────────────────┐    │
│ │ 📊 完美圈率分布圖              │  │ 📅 逐場完美圈追蹤 (Race-by-Race)          │    │
│ │                              │  │                                          │    │
│ │ Rate│                         │  │ 完美圈│  ✓   ✓       ✓   ✓   ✓           │    │
│ │ (%) │                         │  │ 達成? │  │   │   ✗   │   │   │   ✗   ✗   │    │
│ │  40 ├────────┐                │  │       ├──┼───┼───┼───┼───┼───┼───┼───┼── │    │
│ │     │ VER    │                │  │       BHR SAU AUS JPN CHN MIA ...        │    │
│ │  30 ├────────┴──┐             │  │                                          │    │
│ │     │ NOR       │             │  │ ✓ = 理想圈 = 實際最快圈 (誤差 < 0.01s)    │    │
│ │  20 ├───────────┴──┬──┐       │  │ ✗ = 未達成                                │    │
│ │     │ LEC   PIA    │  │       │  │                                          │    │
│ │  10 ├──────────────┴──┴──┐    │  │ 統計: VER 完美圈 8/24 = 33.3%             │    │
│ │     │ HAM SAI RUS ALO ...│    │  │                                          │    │
│ │   0 └────────────────────┘    │  └──────────────────────────────────────────┘    │
│ │       VER NOR LEC PIA ...     │                                                  │
│ └──────────────────────────────┘                                                  │
│                                                                                     │
│ 🔍 完美圈詳情 - VER (Perfect Lap Details)                                           │
│ ┌────┬──────────┬──────────┬──────────┬──────────┬──────────┬────────────────┐   │
│ │場次│賽事      │理想圈    │實際最快圈│差距      │是否完美  │備註            │   │
│ ├────┼──────────┼──────────┼──────────┼──────────┼──────────┼────────────────┤   │
│ │ 1  │ Bahrain  │ 1:31.447 │ 1:31.447 │ 0.000s   │ ✓ 是     │ 完美執行！     │   │
│ │ 2  │ Saudi    │ 1:29.205 │ 1:29.205 │ 0.000s   │ ✓ 是     │ 完美執行！     │   │
│ │ 3  │ Australia│ 1:18.328 │ 1:18.475 │ 0.147s   │ ✗ 否     │ S3 未能串聯    │   │
│ │ ...│ ...      │ ...      │ ...      │ ...      │ ...      │ ...            │   │
│ └────┴──────────┴──────────┴──────────┴──────────┴──────────┴────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**實現重點**：
- 水平柱狀圖 (Horizontal Bar Chart)
- 逐場追蹤時間線 (Timeline with Checkmarks)
- 詳細表格 (QTableWidget with sorting)

---

### Tab 3: 分段熱力圖 (Sector Heatmap)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Tab 3: 分段一致性熱力圖 (Sector Consistency Heatmap)                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│ 🔥 分段變異係數熱力圖 (Sector CV - 越綠越穩定)                                      │
│                                                                                     │
│      賽事 → BHR SAU AUS JPN CHN MIA EMI MON ESP CAN AUT GBR HUN BEL NED ITA ...    │
│ 車手 ↓                                                                              │
│      ┌──────────────────────────────────────────────────────────────────────────┐  │
│ VER  │ 🟢  🟢  🟡  🟢  🟢  🟡  🟢  🔴  🟢  🟢  🟢  🟡  🟢  🟢  🟢  🟢  🟢  🟡 ...│  │
│      │ S1  S1  S1  S1  S1  S1  S1  S1  S1  S1  S1  S1  S1  S1  S1  S1  S1  S1     │  │
│      │ 🟢  🟢  🟢  🟢  🟢  🟢  🟢  🟡  🟢  🟢  🟢  🟢  🟢  🟢  🟢  🟢  🟢  🟢 ...│  │
│      │ S2  S2  S2  S2  S2  S2  S2  S2  S2  S2  S2  S2  S2  S2  S2  S2  S2  S2     │  │
│      │ 🟢  🟢  🟡  🟢  🟢  🟡  🟢  🟡  🟢  🟢  🟢  🟢  🟢  🟢  🟢  🟢  🟢  🟢 ...│  │
│      │ S3  S3  S3  S3  S3  S3  S3  S3  S3  S3  S3  S3  S3  S3  S3  S3  S3  S3     │  │
│      ├──────────────────────────────────────────────────────────────────────────┤  │
│ NOR  │ 🟢  🟢  🟢  🟡  🟢  🟡  🟢  🔴  🟢  🟢  🟡  🟡  🟢  🟢  🟢  🟢  🟢  🟢 ...│  │
│      │ ... (同上 3 行分段結構)                                                     │  │
│      └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
│ 圖例: 🟢 優秀 (CV < 5%)  🟡 普通 (5-10%)  🔴 不穩定 (> 10%)                         │
│                                                                                     │
│ 📊 分段一致性分數排名 (Sector Consistency Score Ranking)                            │
│ ┌────┬─────┬──────────┬──────────┬──────────┬──────────┐                         │
│ │排名│車手 │S1 分數   │S2 分數   │S3 分數   │總分      │                         │
│ ├────┼─────┼──────────┼──────────┼──────────┼──────────┤                         │
│ │ 1  │ VER │  96.2%   │  94.8%   │  92.5%   │  94.5%   │ ◄─ 最穩定               │
│ │ 2  │ NOR │  94.8%   │  93.2%   │  90.4%   │  92.8%   │                         │
│ │ 3  │ LEC │  91.5%   │  90.8%   │  88.6%   │  90.3%   │                         │
│ │ ...│ ... │  ...     │  ...     │  ...     │  ...     │                         │
│ └────┴─────┴──────────┴──────────┴──────────┴──────────┘                         │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**實現重點**：
```python
# Matplotlib Heatmap with seaborn
import seaborn as sns
sns.heatmap(sector_cv_matrix, annot=True, cmap='RdYlGn_r')
```

---

### Tab 4: 改善趨勢分析 (Improvement Trend)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Tab 4: 改善趨勢分析 (Gap Improvement Trend Analysis)                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│ 📈 單車手全年度理想圈差距趨勢 (Individual Driver Season Trend)                      │
│                                                                                     │
│ 🎯 選擇車手: [VER ▼]  對比: [☐ NOR] [☐ 車隊平均] [☐ 全體平均]  [切換車手]          │
│                                                                                     │
│ ┌─────────────────────────────────────────────────────────────────────────────┐   │
│ │ VER - Max Verstappen 全年度理想圈差距變化                                    │   │
│ │                                                                             │   │
│ │ 差距 (s)                                                                    │   │
│ │ 0.20 │                                                                      │   │
│ │      │                                                                      │   │
│ │ 0.15 │        ●                                                             │   │
│ │      │           ●   ●                                                      │   │
│ │ 0.10 │  ●                 ●                        ●                        │   │
│ │      │                       ●   ●           ●                              │   │
│ │ 0.05 │     ●                    ●       ●       ●   ●   ●   ●   ●   ●      │   │
│ │      │                                                                      │   │
│ │ 0.00 │━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │   │
│ │      ├──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┤ │   │
│ │      BHR SAU AUS JPN CHN MIA EMI MON ESP CAN AUT GBR HUN BEL NED ITA AZE  │   │
│ │      SIN USA MEX BRA QAT AbuDhabi                                          │   │
│ │                                                                             │   │
│ │ 📊 趨勢線: y = -0.002x + 0.095  (R² = 0.35)                                 │   │
│ │ 🎯 起始 5 場平均: 0.088s  →  結束 5 場平均: 0.075s  →  改善: -0.013s (-14.8%)│   │
│ │ 💡 評價: 維持穩定 (趨勢不顯著但持續優異)                                     │   │
│ └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│ 📋 全車手年初 vs 年尾對比表 (Season Start vs End Comparison)                        │
│ ┌────┬─────┬──────────┬──────────┬──────────┬────────┬────────┬──────────────┐  │
│ │排名│車手 │起始差距  │結束差距  │改善幅度  │改善率  │趨勢斜率│評價          │  │
│ │    │     │(前5場均) │(後5場均) │(秒)      │(%)     │(s/race)│              │  │
│ ├────┼─────┼──────────┼──────────┼──────────┼────────┼────────┼──────────────┤  │
│ │ 1  │ ANT │ 0.245s   │ 0.085s   │ -0.160s  │ -65.3% │ -0.008 │🚀 顯著進步   │  │
│ │    │     │  🔴      │  🟢      │  🟢🟢🟢  │        │  🟢    │              │  │
│ ├────┼─────┼──────────┼──────────┼──────────┼────────┼────────┼──────────────┤  │
│ │ 2  │ PIA │ 0.138s   │ 0.092s   │ -0.046s  │ -33.3% │ -0.003 │↗ 穩定進步    │  │
│ │    │     │  🟡      │  🟢      │  🟢🟢    │        │  🟢    │              │  │
│ ├────┼─────┼──────────┼──────────┼──────────┼────────┼────────┼──────────────┤  │
│ │ 3  │ HAM │ 0.142s   │ 0.108s   │ -0.034s  │ -23.9% │ -0.002 │↗ 小幅進步    │  │
│ │ 4  │ VER │ 0.088s   │ 0.075s   │ -0.013s  │ -14.8% │ -0.002 │→ 維持穩定    │  │
│ │ 5  │ NOR │ 0.102s   │ 0.088s   │ -0.014s  │ -13.7% │ -0.001 │→ 維持穩定    │  │
│ │ ...│ ... │ ...      │ ...      │ ...      │ ...    │ ...    │ ...          │  │
│ └────┴─────┴──────────┴──────────┴──────────┴────────┴────────┴──────────────┘  │
│                                                                                     │
│ 💡 解讀說明: 差距越小 = 執行力越強 | 負值改善幅度 = 進步                            │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**實現重點**：
- Matplotlib Line Plot with Regression Line
- 可選對比線 (Optional Comparison Lines)
- 統計表格 (Start vs End Comparison Table)

---

### Tab 5: 詳細數據表 (Detailed Statistics Table)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Tab 5: 詳細數據表 (Detailed Statistics Table)                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│ 📋 完整統計數據 (Complete Statistics)                      [匯出 CSV] [複製數據]   │
│                                                                                     │
│ ┌──┬─────┬─────────┬────────┬────────┬────────┬────────┬────────┬────────┬──────┬─────┬─────┬─────┬─────┐│
│ │排│車手 │車隊     │平均差距│標準差  │中位數  │完美圈率│分段一致│趨勢斜率│一致性│起始 │結束 │改善 │改善 ││
│ │名│     │         │Mean Gap│Std Dev │Median  │Perfect%│Sector% │Slope   │Score │差距 │差距 │幅度 │率   ││
│ │  │     │         │        │        │        │        │        │        │      │(前5)│(後5)│(秒) │(%)  ││
│ ├──┼─────┼─────────┼────────┼────────┼────────┼────────┼────────┼────────┼──────┼─────┼─────┼─────┼─────┤│
│ │1 │ VER │Red Bull │ 0.082s │ 0.045s │ 0.075s │ 33.3%  │ 94.5%  │ -0.002 │ 95.2 │0.088│0.075│-0.013│-14.8││
│ │  │     │Racing   │  🟢    │  🟢    │  🟢    │  🟢    │  🟢    │  🟢    │      │ 🟢 │ 🟢 │ 🟢  │     ││
│ │  │     │         │ 第1/20 │ 第2/20 │ 第1/20 │ 第1/20 │ 第1/20 │ 第4/20 │      │ 第4 │ 第1 │ 第4  │     ││
│ ├──┼─────┼─────────┼────────┼────────┼────────┼────────┼────────┼────────┼──────┼─────┼─────┼─────┼─────┤│
│ │2 │ NOR │McLaren  │ 0.095s │ 0.051s │ 0.088s │ 29.2%  │ 92.8%  │ -0.001 │ 93.8 │0.102│0.088│-0.014│-13.7││
│ │  │     │         │  🟢    │  🟡    │  🟢    │  🟢    │  🟢    │  🟡    │      │ 🟢 │ 🟢 │ 🟢  │     ││
│ │ ...│ ...│ ...     │ ...    │ ...    │ ...    │ ...    │ ...    │ ...    │ ...  │ ... │ ... │ ... │ ... ││
│ └──┴─────┴─────────┴────────┴────────┴────────┴────────┴────────┴────────┴──────┴─────┴─────┴─────┴─────┘│
│                                                                                     │
│ 🎨 顏色編碼: 🟢 優秀 (前 33%)  🟡 普通 (中 34%)  🔴 需改善 (後 33%)                 │
│                                                                                     │
│ 📊 統計摘要:                                                                        │
│   • 平均差距範圍: 0.082s - 0.245s (跨度 0.163s)                                     │
│   • 完美圈率範圍: 0.0% - 33.3% (最高 VER 8/24 場)                                   │
│   • 進步車手: ANT (-0.160s, -65.3%), PIA (-0.046s, -33.3%)                         │
│                                                                                     │
│ 🔍 篩選與排序:                                                                      │
│   顯示欄位: [☑ 8 核心指標] [☑ 4 年初年尾對比] [☐ 僅前 10 名]                       │
│   排序依據: [一致性分數 ▼] [平均差距] [完美圈率] [改善幅度]                        │
│   車隊篩選: [全部車隊 ▼] [Red Bull] [McLaren] [Ferrari] [Mercedes]                │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**實現重點**：
- QTableWidget with Custom Delegates
- 三層資訊顯示：數值 + 顏色 + 排名
- CSV 匯出功能
- 可排序、可篩選

---

## 🎨 視覺化組件

### 1. 雷達圖 (Radar Chart) - 多維度對比
**用途**: 一次展示 4 個核心指標，直觀看出車手強弱項  
**技術**: Matplotlib Polar Plot  
**特點**: 支援多車手疊加對比

**實現範例**：
```python
import matplotlib.pyplot as plt
import numpy as np

def create_radar_chart(driver_metrics: dict):
    categories = ['平均差距', '完美圈率', '分段一致性', '改善趨勢']
    N = len(categories)
    
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    values = [
        driver_metrics['mean_gap_score'],
        driver_metrics['perfect_lap_rate'],
        driver_metrics['sector_consistency_score'],
        driver_metrics['trend_score']
    ]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
    ax.plot(angles, values, 'o-', linewidth=2, label='VER')
    ax.fill(angles, values, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles), categories)
    ax.set_ylim(0, 100)
    
    return fig
```

---

### 2. 箱型圖 (Box Plot) - 分布分析
```
 差距│  ┌─┐      ← 異常值
 (s) │  │ │  ┌─┐
0.20 │  │ │  │ │
0.15 │┌─┼─┼──┼─┼─┐  ← Q3
0.10 │├─┼─┼──┼─┼─┤  ← 中位數
0.05 │└─┼─┼──┼─┼─┘  ← Q1
0.00 │  │ │  │ │
     └──┴─┴──┴─┴───
       VER NOR LEC PIA
```
**用途**: 分析車手表現分布、識別離群值  
**統計意義**: 四分位數、異常值檢測

---

### 3. 熱力圖 (Heatmap) - 模式識別
**用途**: 快速識別異常賽事、賽季模式  
**顏色系統**:
- 🟢 綠色: CV < 5% (優秀)
- 🟡 黃色: 5-10% (普通)
- 🔴 紅色: > 10% (不穩定)

**實現範例**：
```python
import seaborn as sns

def create_sector_heatmap(sector_cv_data: np.ndarray):
    plt.figure(figsize=(14, 10))
    sns.heatmap(
        sector_cv_data,
        annot=True,
        fmt='.1f',
        cmap='RdYlGn_r',
        vmin=0,
        vmax=15,
        cbar_kws={'label': 'CV (%)'}
    )
    plt.xlabel('賽事')
    plt.ylabel('車手')
    plt.title('分段變異係數熱力圖')
    
    return plt.gcf()
```

---

### 4. 趨勢線圖 (Trend Line) - 時間序列分析
**用途**: 清楚顯示進步/退步趨勢  
**統計支援**: R² 值驗證趨勢顯著性  
**置信區間**: 顯示預測區間

**實現範例**：
```python
from scipy import stats

def create_trend_chart(race_gaps: list):
    x = np.arange(1, len(race_gaps) + 1)
    y = np.array(race_gaps)
    
    # 線性回歸
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # 繪製
    plt.figure(figsize=(12, 6))
    plt.plot(x, y, 'o-', label='實際差距', markersize=8)
    plt.plot(x, slope * x + intercept, '--', label=f'趨勢線 (R²={r_value**2:.2f})')
    plt.xlabel('賽事順序')
    plt.ylabel('理想圈差距 (s)')
    plt.title('全年度理想圈差距變化')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    return plt.gcf()
```

---

## 🔧 技術實現架構

### 模組結構
```
modules/gui/season_consistency/
├── __init__.py
├── season_consistency_loader.py      # UniversalDataLoader 子類
├── season_consistency_mdi.py         # MDI 主窗口
├── widgets/
│   ├── radar_chart_widget.py         # Tab 1: 雷達圖
│   ├── perfect_lap_widget.py         # Tab 2: 完美圈分析
│   ├── sector_heatmap_widget.py      # Tab 3: 分段熱力圖
│   ├── trend_chart_widget.py         # Tab 4: 趨勢分析
│   └── detailed_table_widget.py      # Tab 5: 詳細數據表
└── utils/
    ├── color_coding.py                # 顏色編碼邏輯
    └── export_utils.py                # CSV 匯出功能
```

---

### 數據載入器實現

```python
# modules/gui/season_consistency/season_consistency_loader.py
from modules.gui.base.universal_data_loader import UniversalDataLoader

class SeasonConsistencyLoader(UniversalDataLoader):
    """
    全年度一致性分析數據載入器
    
    依賴: CLI 功能 70 JSON 輸出
    """
    
    def __init__(self):
        super().__init__(
            data_type="season_consistency",
            cli_function=70,
            debug_enabled=True
        )
    
    def _search_json_files(self, **kwargs) -> list:
        """搜索 JSON 檔案"""
        year = kwargs.get('year', 2025)
        session = kwargs.get('session', 'R')
        
        # 搜索模式: season_consistency_2025_Race.json
        pattern = f"season_consistency_{year}_{session}.json"
        return self._glob_search(pattern)
    
    def _validate_data_format(self, raw_data: dict) -> bool:
        """驗證 JSON 結構"""
        required_keys = ['metadata', 'driver_rankings', 'statistics']
        return all(key in raw_data for key in required_keys)
    
    def _transform_data_for_display(self, raw_data: dict) -> dict:
        """轉換為 GUI 顯示格式"""
        return {
            'rankings': raw_data['driver_rankings'],
            'stats': raw_data['statistics'],
            'metadata': raw_data['metadata']
        }
```

---

### MDI 窗口實現

```python
# modules/gui/season_consistency/season_consistency_mdi.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from .widgets.radar_chart_widget import RadarChartWidget
from .widgets.perfect_lap_widget import PerfectLapWidget
from .widgets.sector_heatmap_widget import SectorHeatmapWidget
from .widgets.trend_chart_widget import TrendChartWidget
from .widgets.detailed_table_widget import DetailedTableWidget

class SeasonConsistencyMDI(QWidget):
    def __init__(self, year: int, session: str, data: dict):
        super().__init__()
        self.year = year
        self.session = session
        self.data = data
        
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        """初始化介面"""
        layout = QVBoxLayout(self)
        
        # 創建 Tab Widget
        self.tab_widget = QTabWidget()
        
        # Tab 1: 雷達圖
        self.radar_widget = RadarChartWidget()
        self.tab_widget.addTab(self.radar_widget, "四指標雷達圖")
        
        # Tab 2: 完美圈分析
        self.perfect_lap_widget = PerfectLapWidget()
        self.tab_widget.addTab(self.perfect_lap_widget, "完美圈分析")
        
        # Tab 3: 分段熱力圖
        self.heatmap_widget = SectorHeatmapWidget()
        self.tab_widget.addTab(self.heatmap_widget, "分段熱力圖")
        
        # Tab 4: 趨勢分析
        self.trend_widget = TrendChartWidget()
        self.tab_widget.addTab(self.trend_widget, "改善趨勢")
        
        # Tab 5: 詳細數據表
        self.table_widget = DetailedTableWidget()
        self.tab_widget.addTab(self.table_widget, "詳細數據表")
        
        layout.addWidget(self.tab_widget)
        self.setWindowTitle(f"🏁 {self.year} 賽季車手一致性分析")
    
    def _load_data(self):
        """載入數據到各個 Tab"""
        self.radar_widget.load_data(self.data)
        self.perfect_lap_widget.load_data(self.data)
        self.heatmap_widget.load_data(self.data)
        self.trend_widget.load_data(self.data)
        self.table_widget.load_data(self.data)
```

---

## 📋 開發檢查清單

### 階段 1: Widget 基礎組件 (預計 3 小時)
- [ ] 實現 `RadarChartWidget` (雷達圖)
- [ ] 實現 `PerfectLapWidget` (完美圈分析)
- [ ] 實現 `SectorHeatmapWidget` (分段熱力圖)
- [ ] 實現 `TrendChartWidget` (趨勢線圖)
- [ ] 實現 `DetailedTableWidget` (詳細數據表)

### 階段 2: 數據載入器 (預計 1 小時)
- [ ] 實現 `SeasonConsistencyLoader`
- [ ] JSON 檔案搜索邏輯
- [ ] 數據格式驗證
- [ ] 數據轉換邏輯

### 階段 3: MDI 窗口整合 (預計 2 小時)
- [ ] 實現 `SeasonConsistencyMDI`
- [ ] Tab Widget 布局
- [ ] 數據分發到各 Tab
- [ ] 窗口標題和圖標

### 階段 4: GUI 主選單整合 (預計 1 小時)
- [ ] 在 `f1t_gui_main.py` 添加選單項目
- [ ] 連接數據載入器
- [ ] MDI 窗口創建和顯示
- [ ] 錯誤處理

### 階段 5: 視覺化優化 (預計 2 小時)
- [ ] Matplotlib 中文字體設定
- [ ] 顏色編碼一致性
- [ ] 圖表主題統一
- [ ] 響應式布局調整

### 階段 6: 功能完善 (預計 2 小時)
- [ ] CSV 匯出功能
- [ ] 複製到剪貼簿
- [ ] 可排序表格
- [ ] 車隊篩選
- [ ] 車手多選對比

### 階段 7: 測試與優化 (預計 2 小時)
- [ ] GUI 啟動測試
- [ ] 各 Tab 渲染測試
- [ ] 大量數據載入測試
- [ ] 中文字體顯示測試
- [ ] 記憶體洩漏測試

---

## 🎯 成功標準

### 功能性
- ✅ 所有 5 個 Tab 正常渲染
- ✅ 雷達圖、熱力圖、趨勢圖正確顯示
- ✅ 車手選擇功能正常切換
- ✅ 排名表可排序、可篩選
- ✅ CSV 匯出功能正常

### 視覺化
- ✅ 中文字體正常顯示
- ✅ 顏色編碼一致 (🟢🟡🔴)
- ✅ 圖表主題統一
- ✅ 響應式布局

### 性能
- ✅ 數據載入 < 2 秒
- ✅ Tab 切換流暢
- ✅ 無記憶體洩漏

---

## 📚 參考資料

### PyQt5 視覺化
- **Matplotlib + PyQt5**: https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html
- **QTableWidget 排序**: https://doc.qt.io/qt-5/qtablewidget.html#sorting

### Matplotlib 圖表
- **雷達圖教學**: https://matplotlib.org/stable/gallery/specialty_plots/radar_chart.html
- **Seaborn 熱力圖**: https://seaborn.pydata.org/generated/seaborn.heatmap.html

### 顏色編碼
- **F1 官方色系**: Red Bull (#0600EF), Ferrari (#DC0000), McLaren (#FF8700)

---

## 📞 聯絡資訊

**開發者**: AI Assistant  
**GUI 負責人**: 待分配  
**最後更新**: 2025-10-10  
**版本**: v1.0.0-draft

---

**🖥️ 準備打造專業的 F1 數據分析 GUI！**
