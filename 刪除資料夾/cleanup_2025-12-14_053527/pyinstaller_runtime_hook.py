# -*- coding: utf-8 -*-
"""
PyInstaller Runtime Hook
在 EXE 啟動時執行，用於設置環境變數和初始化配置
這是 PyInstaller 最早執行的 Python 代碼
"""
import os
import sys
import io

# ========== 最優先：修正 GUI 模式的 stdout/stderr ==========
# PyInstaller GUI 模式 (console=False) 時，sys.stdout/stderr 可能是 None
# 這會導致任何 print() 語句崩潰，必須在這裡修正

class NullWriter:
    """靜默輸出器，永不關閉，避免 I/O operation on closed file"""
    def write(self, text):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False

def _fix_stdio():
    """修正 stdout/stderr，確保 print() 不會崩潰"""
    # 情況 1: stdout/stderr 是 None (GUI 模式) - 使用 NullWriter
    if sys.stdout is None:
        sys.stdout = NullWriter()
    if sys.stderr is None:
        sys.stderr = NullWriter()
    
    # 情況 2: 嘗試包裝成 UTF-8 (如果有 buffer)
    if hasattr(sys.stdout, 'buffer') and hasattr(sys.stdout, 'encoding'):
        try:
            if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer,
                    encoding='utf-8',
                    errors='replace',
                    line_buffering=True
                )
        except Exception:
            pass
    
    if hasattr(sys.stderr, 'buffer') and hasattr(sys.stderr, 'encoding'):
        try:
            if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer,
                    encoding='utf-8',
                    errors='replace',
                    line_buffering=True
                )
        except Exception:
            pass

_fix_stdio()

# 設置日誌級別為 INFO（生產環境）
# 如需調試，可改為 DEBUG
os.environ.setdefault('F1_LOG_LEVEL', 'INFO')

# 確保 stdout/stderr 使用 UTF-8 編碼
if sys.platform == 'win32':
    # Windows 環境下設置 UTF-8 編碼
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    os.environ.setdefault('PYTHONUTF8', '1')

# 禁用 numexpr 的多線程警告
os.environ.setdefault('NUMEXPR_MAX_THREADS', '16')

# 設置 matplotlib 使用非交互式後端（避免某些環境問題）
os.environ.setdefault('MPLBACKEND', 'Qt5Agg')
