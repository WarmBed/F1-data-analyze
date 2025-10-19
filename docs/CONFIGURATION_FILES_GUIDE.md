# 配置檔案說明 - Configuration Files Guide

## 語言配置檔案 (Language Configuration)

### 📋 概述

`gui_language_config.json` 是**自動生成**的個人配置檔案，用於保存用戶的語言設定。

### 🔄 自動生成機制

#### 初次使用
```
1. 用戶啟動應用程式
   └─> 找不到配置檔案
       └─> 使用預設語言 (English)
       
2. 用戶切換語言 (例如：切換到日文)
   └─> 自動創建 gui_language_config.json
       └─> 保存設定: {"language": "ja"}
       
3. 下次啟動
   └─> 自動讀取配置
       └─> 載入上次選擇的語言 (日文)
```

### 📂 檔案位置

| 模式 | 路徑 | 說明 |
|------|------|------|
| **開發模式** | `core/gui_language_config.json` | 專案目錄中 |
| **EXE 模式** | `~/.f1telemetrystation/gui_language_config.json` | 用戶目錄中 |

**Windows EXE 實際路徑**：
```
C:\Users\<用戶名>\.f1telemetrystation\gui_language_config.json
```

### 🚫 不需要上傳到 GitHub

#### 為什麼？

1. **個人設定** - 這是每個用戶的個人語言偏好
2. **自動生成** - 程式會在需要時自動創建
3. **避免衝突** - 不同用戶有不同的語言偏好

#### .gitignore 設定

已在 `.gitignore` 中添加：
```gitignore
# ⭐ 個人語言配置檔案（會自動生成，不應上傳）
core/gui_language_config.json
```

### ✅ 給其他用戶的使用體驗

#### 情境 1: 下載源代碼
```
1. git clone https://github.com/WarmBed/F1-data-analyze.git
2. python f1t_gui_main.py
   └─> ✅ 自動使用預設語言 (English)
   └─> ✅ 切換語言後自動創建配置檔案
```

#### 情境 2: 下載 EXE
```
1. 下載 F1T_GUI.exe
2. 執行 F1T_GUI.exe
   └─> ✅ 自動使用預設語言 (English)
   └─> ✅ 切換語言後自動在用戶目錄創建配置
```

### 🛠️ 程式碼邏輯

#### 初始化（有容錯機制）
```python
def __init__(self, language='en'):
    # 1. 嘗試載入保存的語言
    saved_language = self._load_saved_language()
    
    # 2. 如果沒有配置檔案，使用預設值
    self.language = saved_language if saved_language else language
    
    # 3. 載入翻譯字典
    self._translations = self._load_translations()
```

#### 載入配置（容錯）
```python
def _load_saved_language(self):
    try:
        config_file = get_config_path()
        if os.path.exists(config_file):  # ✅ 檢查檔案是否存在
            # 讀取配置
            return config.get('language', 'en')
    except Exception as e:
        print(f"[GUI_I18N] 載入失敗: {e}")
    return None  # ✅ 返回 None，使用預設語言
```

#### 保存配置（自動創建）
```python
def _save_language(self, language):
    config = {'language': language}
    config_file = get_config_path()
    
    # ✅ 自動創建目錄（如果不存在）
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    # ✅ 寫入配置
    with open(config_file, 'w') as f:
        json.dump(config, f)
```

### 📝 配置檔案格式

```json
{
  "language": "ja"
}
```

**支援的語言**：
- `"en"` - English (英文)
- `"zh"` - 繁體中文
- `"ja"` - 日本語 (日文)

### 🔍 手動檢查配置

#### 開發模式
```powershell
# Windows
Get-Content "core\gui_language_config.json"

# 或
cat core/gui_language_config.json
```

#### EXE 模式
```powershell
# Windows
Get-Content "$env:USERPROFILE\.f1telemetrystation\gui_language_config.json"

# Linux/Mac
cat ~/.f1telemetrystation/gui_language_config.json
```

### 🧪 測試腳本

執行測試以驗證配置系統：
```powershell
python test_language_switch.py
```

### ❓ 常見問題

#### Q1: 如果我刪除配置檔案會怎樣？
**A**: 程式會自動使用預設語言 (English)，並在下次切換語言時重新創建配置檔案。

#### Q2: 我可以手動編輯配置檔案嗎？
**A**: 可以！只要確保格式正確：
```json
{
  "language": "ja"
}
```

#### Q3: 為什麼我的配置沒有生效？
**A**: 確認：
1. 語言代碼正確 (`en`, `zh`, `ja`)
2. JSON 格式正確
3. 重啟應用程式（語言切換需要重啟）

#### Q4: 我需要在 GitHub 上傳這個檔案嗎？
**A**: ❌ **不需要！** 這是個人配置，已在 `.gitignore` 中排除。

#### Q5: 其他用戶下載我的專案後會有問題嗎？
**A**: ✅ **不會！** 程式會自動處理：
- 找不到配置 → 使用預設語言
- 用戶切換語言 → 自動創建配置
- 完全自動化，無需手動干預

### 📚 相關文件

- `core/gui_i18n.py` - 語言系統實現
- `test_language_switch.py` - 測試腳本
- `EXE_LANGUAGE_FIX_REPORT.md` - EXE 語言修復報告
- `.gitignore` - Git 忽略規則

### 🎯 總結

| 問題 | 答案 |
|------|------|
| 需要上傳配置檔案嗎？ | ❌ 不需要（已在 .gitignore） |
| 其他用戶需要手動創建嗎？ | ❌ 不需要（自動生成） |
| 刪除配置會有問題嗎？ | ❌ 不會（自動使用預設值） |
| 支援多用戶嗎？ | ✅ 支援（每個用戶獨立配置） |
| EXE 模式正常運作嗎？ | ✅ 正常（使用用戶目錄） |

**結論**: 配置檔案完全自動化，開發者和用戶都無需手動管理！🎉
