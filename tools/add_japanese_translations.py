#!/usr/bin/env python3
"""
自動添加日文翻譯到 GUI 國際化模組
Automatically add Japanese translations to GUI i18n module
"""

import re
import os

# 日文翻譯對照表 (常用GUI詞彙)
JA_TRANSLATIONS = {
    # 基本操作
    'Select All': 'すべて選択',
    'Clear All': 'すべてクリア',
    'Restore Default': 'デフォルトに戻す',
    'OK': 'OK',
    'Cancel': 'キャンセル',
    'Close': '閉じる',
    'Save': '保存',
    'Open': '開く',
    'Exit': '終了',
    'Apply': '適用',
    'Reset': 'リセット',
    
    # 視窗控制
    'Cascade Windows': 'ウィンドウを重ねて表示',
    'Tile Windows': 'ウィンドウを並べて表示',
    'Close Window': 'ウィンドウを閉じる',
    'Close All Windows': 'すべてのウィンドウを閉じる',
    'Restore Window': 'ウィンドウを元に戻す',
    'Maximize Window': 'ウィンドウを最大化',
    'Minimize Window': 'ウィンドウを最小化',
    'Cascade All Windows': 'すべてのウィンドウを重ねて表示',
    'Tile All Windows': 'すべてのウィンドウを並べて表示',
    
    # 分析類型
    'Telemetry Analysis Options': 'テレメトリー分析オプション',
    'Please select telemetry charts to display': '表示するテレメトリーチャートを選択してください',
    'Driver & Lap Selection': 'ドライバーとラップの選択',
    'Driver 1 (Required):': 'ドライバー1（必須）:',
    'Driver 2 (Optional):': 'ドライバー2（オプション）:',
    'Lap:': 'ラップ:',
    'Telemetry Options': 'テレメトリーオプション',
    'Fastest Lap': '最速ラップ',
    'None': 'なし',
    
    # 標籤
    'Year:': '年:',
    'Race:': 'レース:',
    'Session:': 'セッション:',
    'Driver 1:': 'ドライバー1:',
    'Driver 2:': 'ドライバー2:',
    
    # 分析模組
    'Rain Analysis': '降雨分析',
    'Track Analysis': 'トラック分析',
    'Accident Analysis': '事故分析',
    'Tire Analysis': 'タイヤ分析',
    'Lap Analysis': 'ラップ分析',
    'Telemetry Analysis': 'テレメトリー分析',
    'Driver Analysis': 'ドライバー分析',
    'Pitstop Analysis': 'ピットストップ分析',
    
    # 工作站
    'F1T Racing Analysis Workstation': 'F1Tレーシング分析ワークステーション',
    'F1 TelemetryStation Pro v0.0': 'F1 TelemetryStation Pro v0.0',
    
    # 狀態訊息
    'Ready': '準備完了',
    'Loading data...': 'データ読み込み中...',
    'Processing...': '処理中...',
    'Generating data...': 'データ生成中...',
    
    # 錯誤訊息
    'Failed to load JSON file': 'JSONファイルの読み込みに失敗しました',
    'Error occurred while searching files': 'ファイル検索中にエラーが発生しました',
    'Data processing failed': 'データ処理に失敗しました',
    'CLI analysis failed': 'CLI分析に失敗しました',
    'Encoding error': 'エンコーディングエラー',
    'Unable to decode partial output': '出力の一部をデコードできません',
    'CLI execution error': 'CLI実行エラー',
    'Load failed': '読み込みに失敗しました',
    'Chart update failed': 'チャート更新に失敗しました',
    'Parameter update failed': 'パラメーター更新に失敗しました',
    
    # CLI訊息
    'Starting CLI Analysis: {year} {race} {session}': 'CLI分析開始: {year} {race} {session}',
    'CLI analysis completed successfully': 'CLI分析が正常に完了しました',
    'Return code': 'リターンコード',
    'Error output': 'エラー出力',
    'Error output encoding issue': 'エラー出力のエンコーディング問題',
    'Analysis cancelled by user': 'ユーザーによって分析がキャンセルされました',
    
    # 語言切換
    'Language': '言語',
    'Switch Language': '言語切り替え',
    'Traditional Chinese': '繁体字中国語',
    'English': '英語',
    'Japanese': '日本語',
    'Language switched': '言語が切り替わりました',
    'Some changes require program restart to take full effect': '一部の変更は、完全に有効にするためにプログラムの再起動が必要です',
    'Language switched to: {language}': '言語が{language}に切り替わりました',
    
    # 選單
    'File': 'ファイル',
    'Edit': '編集',
    'View': '表示',
    'Tools': 'ツール',
    'Help': 'ヘルプ',
    'Analysis': '分析',
    
    # 其他常用詞
    'Lap': 'ラップ',
    'Speed': '速度',
    'Throttle': 'スロットル',
    'Brake': 'ブレーキ',
    'Gear': 'ギア',
    'RPM': 'RPM',
    'Specific Lap': '特定ラップ',
}

def add_japanese_to_translations():
    """為所有翻譯鍵值添加日文"""
    
    file_path = 'c:\\Users\\mike2\\OneDrive\\Code\\F1-data-analyze\\core\\gui_i18n.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 尋找所有的翻譯鍵值模式
    # 模式: 'key': {'zh': '中文', 'en': 'English'}
    pattern = r"'([^']+)':\s*\{\s*'zh':\s*'([^']*)',\s*'en':\s*'([^']*)'\s*\}"
    
    def replace_with_ja(match):
        key = match.group(1)
        zh_text = match.group(2)
        en_text = match.group(3)
        
        # 嘗試從對照表獲取日文翻譯
        ja_text = JA_TRANSLATIONS.get(en_text, en_text)  # 如果找不到，使用英文
        
        # 返回包含日文的新格式
        return f"'{key}': {{'zh': '{zh_text}', 'en': '{en_text}', 'ja': '{ja_text}'}}"
    
    # 執行替換
    new_content = re.sub(pattern, replace_with_ja, content)
    
    # 寫回檔案
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 日文翻譯已成功添加到所有鍵值")
    print(f"📝 處理的翻譯鍵值數量: {len(re.findall(pattern, content))}")

if __name__ == '__main__':
    add_japanese_to_translations()
