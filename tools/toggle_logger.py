#!/usr/bin/env python3
"""
Logger 開關工具

用途：快速開啟或關閉 logging 系統以測試性能影響

使用方式：
    python tools/toggle_logger.py --status           # 查看當前狀態
    python tools/toggle_logger.py --disable          # 關閉 logger
    python tools/toggle_logger.py --enable           # 開啟 logger
    python tools/toggle_logger.py --set-level DEBUG  # 設定日誌等級
"""

import argparse
import json
import sys
from pathlib import Path

# 設定檔路徑
CONFIG_FILE = Path(__file__).parent.parent / "config" / "logging_config.json"


def load_config():
    """載入 logging 設定"""
    if not CONFIG_FILE.exists():
        return {
            "enabled": True,
            "level": "INFO",
            "console_level": None,
            "patch_print": True,
            "comment": "Logger settings - Set 'enabled' to false to disable all logging for performance"
        }
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config):
    """儲存 logging 設定"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def show_status():
    """顯示當前 logger 狀態"""
    config = load_config()
    print("\n" + "="*60)
    print("📊 Logger 設定狀態")
    print("="*60)
    print(f"  ✅ 啟用狀態: {'啟用' if config['enabled'] else '❌ 禁用'}")
    print(f"  📝 日誌等級: {config['level']}")
    print(f"  🖥️  控制台等級: {config.get('console_level', '繼承主等級')}")
    print(f"  🔧 Patch Print: {'啟用' if config.get('patch_print', True) else '禁用'}")
    print(f"  📁 設定檔: {CONFIG_FILE}")
    print("="*60)
    
    if not config['enabled']:
        print("\n⚠️  Logger 目前已禁用，所有日誌輸出將被忽略")
        print("   這可能提升性能，但會失去除錯資訊")
    
    print()


def enable_logger():
    """啟用 logger"""
    config = load_config()
    config['enabled'] = True
    save_config(config)
    print("✅ Logger 已啟用")
    show_status()


def disable_logger():
    """禁用 logger"""
    config = load_config()
    config['enabled'] = False
    save_config(config)
    print("❌ Logger 已禁用")
    print("⚠️  重要：請重新啟動 F1T GUI 以套用變更")
    show_status()


def set_level(level):
    """設定日誌等級"""
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    level_upper = level.upper()
    
    if level_upper not in valid_levels:
        print(f"❌ 錯誤：無效的日誌等級 '{level}'")
        print(f"   有效選項: {', '.join(valid_levels)}")
        return
    
    config = load_config()
    config['level'] = level_upper
    save_config(config)
    print(f"✅ 日誌等級已設定為: {level_upper}")
    print("⚠️  重要：請重新啟動 F1T GUI 以套用變更")
    show_status()


def set_console_level(level):
    """設定控制台日誌等級"""
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'NONE']
    level_upper = level.upper()
    
    if level_upper not in valid_levels:
        print(f"❌ 錯誤：無效的日誌等級 '{level}'")
        print(f"   有效選項: {', '.join(valid_levels)}")
        return
    
    config = load_config()
    config['console_level'] = None if level_upper == 'NONE' else level_upper
    save_config(config)
    print(f"✅ 控制台日誌等級已設定為: {level_upper}")
    print("⚠️  重要：請重新啟動 F1T GUI 以套用變更")
    show_status()


def toggle_patch_print():
    """切換 patch_print 設定"""
    config = load_config()
    config['patch_print'] = not config.get('patch_print', True)
    save_config(config)
    status = "啟用" if config['patch_print'] else "禁用"
    print(f"✅ Patch Print 已{status}")
    print("⚠️  重要：請重新啟動 F1T GUI 以套用變更")
    show_status()


def main():
    parser = argparse.ArgumentParser(
        description='Logger 開關工具 - 控制 F1T 的日誌系統',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python tools/toggle_logger.py --status              # 查看狀態
  python tools/toggle_logger.py --disable             # 關閉 logger（提升性能）
  python tools/toggle_logger.py --enable              # 開啟 logger
  python tools/toggle_logger.py --set-level DEBUG     # 設定為 DEBUG 等級
  python tools/toggle_logger.py --console-level ERROR # 只在控制台顯示錯誤
  python tools/toggle_logger.py --toggle-print        # 切換 print patch
        """
    )
    
    parser.add_argument('--status', action='store_true',
                       help='顯示當前 logger 狀態')
    parser.add_argument('--enable', action='store_true',
                       help='啟用 logger')
    parser.add_argument('--disable', action='store_true',
                       help='禁用 logger（提升性能）')
    parser.add_argument('--set-level', type=str, metavar='LEVEL',
                       help='設定日誌等級 (DEBUG/INFO/WARNING/ERROR/CRITICAL)')
    parser.add_argument('--console-level', type=str, metavar='LEVEL',
                       help='設定控制台日誌等級 (DEBUG/INFO/WARNING/ERROR/CRITICAL/NONE)')
    parser.add_argument('--toggle-print', action='store_true',
                       help='切換 patch_print 設定')
    
    args = parser.parse_args()
    
    # 如果沒有任何參數，顯示狀態
    if len(sys.argv) == 1:
        show_status()
        return
    
    if args.status:
        show_status()
    elif args.enable:
        enable_logger()
    elif args.disable:
        disable_logger()
    elif args.set_level:
        set_level(args.set_level)
    elif args.console_level:
        set_console_level(args.console_level)
    elif args.toggle_print:
        toggle_patch_print()


if __name__ == '__main__':
    main()
