#!/usr/bin/env python3
"""
F1 Analysis API - 系統相關路由
處理健康檢查、系統信息等端點

版本: 2.0 (重構版)
作者: F1 Analysis Team
"""

from fastapi import APIRouter
from typing import Dict, Any
import time
import sys
import os
import platform

# 創建路由器
router = APIRouter(
    prefix="/system",
    tags=["系統管理"],
    responses={
        500: {"description": "系統錯誤"}
    }
)


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    系統健康檢查
    
    檢查所有系統組件的健康狀態
    """
    
    try:
        # 檢查 Python 版本
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # 檢查工作目錄
        current_dir = os.getcwd()
        
        # 檢查必要文件
        cli_file_exists = os.path.exists("f1_analysis_modular_main.py")
        json_dir_exists = os.path.exists("json")
        cache_dir_exists = os.path.exists("cache")
        
        # 系統信息
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": python_version,
            "working_directory": current_dir
        }
        
        # 文件系統檢查
        file_checks = {
            "cli_main_file": cli_file_exists,
            "json_directory": json_dir_exists,
            "cache_directory": cache_dir_exists
        }
        
        # 計算健康分數
        total_checks = len(file_checks)
        passed_checks = sum(file_checks.values())
        health_score = (passed_checks / total_checks) * 100
        
        # 確定狀態
        if health_score == 100:
            status = "healthy"
        elif health_score >= 80:
            status = "degraded"
        else:
            status = "unhealthy"
            
        return {
            "success": True,
            "status": status,
            "health_score": health_score,
            "message": f"系統健康檢查完成 ({passed_checks}/{total_checks} 項檢查通過)",
            "system_info": system_info,
            "checks": file_checks,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "message": "健康檢查執行失敗",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/info")
async def get_system_info() -> Dict[str, Any]:
    """
    獲取系統信息
    
    返回詳細的系統和應用程式信息
    """
    
    try:
        # Python 環境信息
        python_info = {
            "version": sys.version,
            "executable": sys.executable,
            "platform": sys.platform,
            "path": sys.path[:5]  # 只顯示前5個路徑
        }
        
        # 作業系統信息
        os_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
        
        # 應用程式信息
        app_info = {
            "name": "F1 Analysis API",
            "version": "2.0.0",
            "description": "Formula 1 賽車數據分析 API",
            "working_directory": os.getcwd(),
            "startup_time": time.time()
        }
        
        # 目錄信息
        directory_info = {}
        important_dirs = ["json", "cache", "api", "CLI_modules", "modules"]
        
        for dir_name in important_dirs:
            if os.path.exists(dir_name):
                try:
                    # 計算目錄大小
                    total_size = 0
                    file_count = 0
                    
                    for root, dirs, files in os.walk(dir_name):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                total_size += os.path.getsize(file_path)
                                file_count += 1
                            except Exception:
                                continue
                    
                    directory_info[dir_name] = {
                        "exists": True,
                        "files": file_count,
                        "size_mb": round(total_size / (1024*1024), 3)
                    }
                    
                except Exception:
                    directory_info[dir_name] = {
                        "exists": True,
                        "error": "無法計算大小"
                    }
            else:
                directory_info[dir_name] = {"exists": False}
        
        return {
            "success": True,
            "message": "系統信息獲取成功",
            "python_info": python_info,
            "os_info": os_info,
            "app_info": app_info,
            "directory_info": directory_info,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "系統信息獲取失敗",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/version")
async def get_version() -> Dict[str, Any]:
    """
    獲取 API 版本信息
    
    返回當前 API 版本和相關信息
    """
    
    return {
        "success": True,
        "api_version": "2.0.0",
        "api_name": "F1 Analysis API",
        "build_type": "重構版 (Refactored)",
        "features": [
            "模組化路由結構",
            "智能緩存系統",
            "52種分析功能",
            "自動API文檔",
            "中間件支持",
            "錯誤處理"
        ],
        "endpoints": {
            "analysis": "/analysis/*",
            "cache": "/cache/*", 
            "system": "/system/*",
            "docs": "/docs"
        },
        "release_date": "2025-09-17",
        "timestamp": time.time()
    }
