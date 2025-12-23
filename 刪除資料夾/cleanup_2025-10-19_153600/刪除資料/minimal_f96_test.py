#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function 96 精簡測試 - 使用內建的 Python 日誌
"""
import sys
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('f96_execution.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

try:
    logging.info("=" * 80)
    logging.info("開始測試 Function 96")
    logging.info("=" * 80)
    
    # 模擬命令列參數
    sys.argv = ["f1_analysis_modular_main.py", "-f", "96", "-y", "2025", "-r", "Japan"]
    
    logging.info("Step 1: 導入模組...")
    from f1_analysis_modular_main import F1AnalysisModularCLI
    logging.info("✅ 導入成功")
    
    logging.info("\nStep 2: 創建 CLI 實例...")
    app = F1AnalysisModularCLI()
    logging.info("✅ 實例創建成功")
    
    logging.info("\nStep 3: 執行 app.run()...")
    result = app.run()
    logging.info(f"✅ 執行完成，結果: {result}")
    
    logging.info("\n" + "=" * 80)
    logging.info(f"測試結果: {'成功' if result else '失敗'}")
    logging.info("=" * 80)
    
    sys.exit(0 if result else 1)
    
except Exception as e:
    logging.error(f"\n❌ 錯誤: {type(e).__name__}: {str(e)}")
    import traceback
    logging.error("Traceback:")
    for line in traceback.format_exc().split('\n'):
        logging.error(line)
    sys.exit(1)
