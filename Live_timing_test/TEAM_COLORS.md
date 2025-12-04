# F1 車隊配色方案 (2024/2025 賽季)

## 經典 F1 97/96 風格配色

### 車隊配色映射

```python
TEAM_COLORS_F1_97 = {
    # Red Bull Racing - 深藍 + 紅
    'Red Bull Racing': {
        'primary': '#0600EF',    # 深藍
        'secondary': '#FF0000',   # 紅色
        'text': '#FFFFFF'
    },
    
    # Ferrari - 紅色
    'Ferrari': {
        'primary': '#DC0000',
        'secondary': '#FFFF00',  # 黃色點綴
        'text': '#FFFFFF'
    },
    
    # Mercedes - 銀色/青綠
    'Mercedes': {
        'primary': '#00D2BE',    # 青綠
        'secondary': '#C0C0C0',  # 銀色
        'text': '#000000'
    },
    
    # McLaren - 橘色
    'McLaren': {
        'primary': '#FF8700',
        'secondary': '#47C7FC',  # 藍色
        'text': '#FFFFFF'
    },
    
    # Aston Martin - 綠色
    'Aston Martin': {
        'primary': '#006F62',
        'secondary': '#00352F',
        'text': '#FFFFFF'
    },
    
    # Alpine - 粉藍
    'Alpine': {
        'primary': '#0090FF',
        'secondary': '#FF87BC',
        'text': '#FFFFFF'
    },
    
    # Williams - 藍色
    'Williams': {
        'primary': '#005AFF',
        'secondary': '#FFFFFF',
        'text': '#FFFFFF'
    },
    
    # RB (AlphaTauri) - 深藍
    'RB': {
        'primary': '#2B4562',
        'secondary': '#6692FF',
        'text': '#FFFFFF'
    },
    
    # Kick Sauber - 綠色
    'Kick Sauber': {
        'primary': '#00E701',
        'secondary': '#000000',
        'text': '#000000'
    },
    
    # Haas - 灰白紅
    'Haas F1 Team': {
        'primary': '#B6BABD',
        'secondary': '#ED1C24',
        'text': '#000000'
    }
}
```

## F1 96 復古風格配色（更鮮豔）

```python
TEAM_COLORS_F1_96 = {
    'Red Bull Racing': {
        'primary': '#0000FF',    # 寶藍
        'secondary': '#FFFF00',  # 黃色
        'text': '#FFFFFF'
    },
    
    'Ferrari': {
        'primary': '#FF0000',    # 純紅
        'secondary': '#FFFFFF',
        'text': '#FFFFFF'
    },
    
    'Mercedes': {
        'primary': '#00FFFF',    # 青色
        'secondary': '#C0C0C0',
        'text': '#000000'
    },
    
    'McLaren': {
        'primary': '#FF6600',    # 橘紅
        'secondary': '#000000',
        'text': '#FFFFFF'
    },
    
    # ... 其他車隊
}
```

## 使用方式

### 在表格中應用配色

```python
# LiveRankingTableWidget.update_display 中
team_name = driver_data.get('team_name')
if team_name in TEAM_COLORS:
    colors = TEAM_COLORS[team_name]
    
    # 設置行背景色
    for col in range(self.table.columnCount()):
        item = self.table.item(row, col)
        item.setBackground(QColor(colors['primary']))
        item.setForeground(QColor(colors['text']))
```

### 在賽道地圖中應用配色

```python
# TrackMapWidget._draw_driver_markers 中
team_name = driver_data.get('team_name')
color = QColor(TEAM_COLORS[team_name]['primary'])
painter.setBrush(QBrush(color))
```

## 顯示效果

```
排名  車手        圈數  速度    ...
[藍色背景] 1   VER (1)     27   231     
[紅色背景] 2   LEC (16)    27   203     
[青綠背景] 3   HAM (44)    27   198     
```

## 您希望使用哪種配色？

1. **F1 97 風格** - 較現代、符合當前車隊配色
2. **F1 96 風格** - 更鮮豔復古、經典風格
3. **混合風格** - 我可以調整

請告訴我您的偏好！
