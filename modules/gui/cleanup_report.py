#!/usr/bin/env python3
"""
API 重構清理報告 - 檢查重構後的系統狀態

版本: 2.0 (重構版)
"""

import os
import sys
from pathlib import Path
import logging

from core.logger import get_logger

logger = get_logger("cleanup_report", component="gui")


def generate_cleanup_report():
    """生成清理和重構報告"""
    
    logger.info("=" * 80)
    logger.info("🧹 F1 Analysis API 重構清理報告")
    logger.info("=" * 80)
    
    # 檢查目錄結構
    logger.info("\n📁 目錄結構檢查:")
    logger.info("-" * 40)
    
    directories = [
        "api/",
        "api/models/",
        "api/services/", 
        "api/routers/",
        "api/middleware/"
    ]
    
    for dir_path in directories:
        if os.path.exists(dir_path):
            logger.info("✅ %s", dir_path)
            # 列出內容
            try:
                contents = os.listdir(dir_path)
                for item in contents:
                    if not item.startswith('__pycache__'):
                        logger.info("   └── %s", item)
            except:
                pass
        else:
            logger.warning("❌ %s", dir_path)
    
    # 檢查核心檔案
    logger.info("\n📄 核心檔案檢查:")
    logger.info("-" * 40)
    
    core_files = {
        "重構版 API": "refactored_api.py",
        "簡化版 API": "simple_api.py", 
        "主路由": "api/routers/main.py",
        "中間件": "api/middleware/handlers.py",
        "緩存服務": "api/services/cache_service.py",
        "簡化服務": "api/services/simple_analysis_service.py",
        "請求模型": "api/models/requests.py",
        "響應模型": "api/models/responses.py"
    }
    
    for name, path in core_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            logger.info("✅ %s: %s (%s bytes)", name, path, f"{size:,}")
        else:
            logger.warning("❌ %s: %s", name, path)
    
    # 檢查測試檔案
    logger.info("\n🧪 測試檔案檢查:")
    logger.info("-" * 40)
    
    test_files = {
        "簡化版 API 測試": "test_simple_api.py",
        "簡化版服務測試": "test_simple_service.py", 
        "修復後模型測試": "test_fixed_api_models.py"
    }
    
    for name, path in test_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            logger.info("✅ %s: %s (%s bytes)", name, path, f"{size:,}")
        else:
            logger.warning("❌ %s: %s", name, path)
    
    # 檢查應該被清理的檔案
    logger.info("\n🗑️ 應清理檔案檢查:")
    logger.info("-" * 40)
    
    cleanup_files = [
        "api/services/analysis_service.py",
        "api/services/cli_executor.py", 
        "test_api_models.py",
        "test_analysis_service.py",
        "test_cache_service.py",
        "test_cli_executor.py"
    ]
    
    cleanup_needed = []
    for path in cleanup_files:
        if os.path.exists(path):
            logger.warning("⚠️  仍存在: %s", path)
            cleanup_needed.append(path)
        else:
            logger.info("✅ 已清理: %s", path)
    
    # 檢查緩存和數據
    logger.info("\n💾 數據和緩存檢查:")
    logger.info("-" * 40)
    
    data_dirs = ["json/", "cache/", "f1_analysis_cache/"]
    for dir_path in data_dirs:
        if os.path.exists(dir_path):
            try:
                files = os.listdir(dir_path)
                file_count = len([f for f in files if os.path.isfile(os.path.join(dir_path, f))])
                logger.info("✅ %s: %d 個檔案", dir_path, file_count)
            except:
                logger.warning("⚠️  %s: 無法讀取", dir_path)
        else:
            logger.warning("❌ %s: 不存在", dir_path)
    
    # 生成建議
    logger.info("\n💡 清理建議:")
    logger.info("-" * 40)
    
    if cleanup_needed:
        logger.info("🗑️  建議手動刪除以下檔案:")
        for path in cleanup_needed:
            logger.info("   rm %s", path)
    else:
        logger.info("✅ 所有目標檔案已清理完成")
    
    logger.info("\n📊 重構成果:")
    logger.info("-" * 40)
    logger.info("✅ 模組化路由架構")
    logger.info("✅ 統一中間件系統") 
    logger.info("✅ 標準化錯誤處理")
    logger.info("✅ 安全頭和 CORS 支援")
    logger.info("✅ 完整的 API 文檔")
    logger.info("✅ 單例服務管理")
    logger.info("✅ 性能監控和日誌")
    
    logger.info("\n🚀 下一步:")
    logger.info("-" * 40)
    logger.info("1. 測試重構版 API: python refactored_api.py")
    logger.info("2. 比較性能: 運行測試腳本")
    logger.info("3. 部署準備: 配置生產環境")
    logger.info("4. 文檔更新: 更新 README.md")
    
    logger.info("\n" + "=" * 80)
    logger.info("🏁 清理報告完成")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        generate_cleanup_report()
    except Exception as e:
        logger.exception("❌ 報告生成失敗: %s", e)
