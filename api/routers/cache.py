#!/usr/bin/env python3
"""
F1 Analysis API - 緩存相關路由
處理所有緩存管理相關的端點

版本: 2.0 (重構版)
作者: F1 Analysis Team
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import time

# 導入服務
from api.services.cache_service import F1AnalysisCacheService

# 創建路由器
router = APIRouter(
    prefix="/cache",
    tags=["緩存管理"],
    responses={
        404: {"description": "緩存項目不存在"},
        500: {"description": "緩存服務錯誤"}
    }
)

# 初始化緩存服務
cache_service = F1AnalysisCacheService()


@router.get("/status")
async def get_cache_status() -> Dict[str, Any]:
    """
    獲取緩存狀態和統計信息
    
    返回緩存目錄狀態、文件統計、支持功能等信息
    """
    
    try:
        stats = cache_service.get_cache_statistics()
        
        return {
            "success": True,
            "message": "緩存狀態獲取成功",
            "cache_summary": {
                "total_files": stats["summary"]["total_files"],
                "total_size_mb": stats["summary"]["total_size_mb"],
                "cache_directory": stats["summary"]["cache_directory"]
            },
            "recent_files": {
                "count": len(stats["recent_files"]),
                "files": stats["recent_files"][:5]  # 只顯示前5個最近文件
            },
            "supported_functions": {
                "count": len(stats["supported_functions"]),
                "functions": stats["supported_functions"]
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "緩存狀態獲取失敗",
                "message": str(e),
                "timestamp": time.time()
            }
        )


@router.get("/search")
async def search_cache(
    function_id: int = Query(..., ge=1, le=52, description="分析功能 ID"),
    year: Optional[int] = Query(None, ge=2024, le=2025, description="賽季年份"),
    race: Optional[str] = Query(None, min_length=3, description="賽事名稱"),
    session: Optional[str] = Query(None, description="會話類型"),
    driver1: Optional[str] = Query(None, min_length=3, max_length=3, description="車手代碼1"),
    driver2: Optional[str] = Query(None, min_length=3, max_length=3, description="車手代碼2")
) -> Dict[str, Any]:
    """
    搜尋緩存中的分析結果
    
    根據提供的參數搜尋匹配的緩存文件
    """
    
    try:
        # 建構搜尋參數
        search_params = {}
        if year:
            search_params["year"] = year
        if race:
            search_params["race"] = race
        if session:
            search_params["session"] = session
        if driver1:
            search_params["driver1"] = driver1.upper()
        if driver2:
            search_params["driver2"] = driver2.upper()
            
        # 搜尋緩存
        result = cache_service.search_cached_analysis(function_id, **search_params)
        
        if result:
            return {
                "success": True,
                "message": "緩存搜尋成功",
                "cache_hit": True,
                "search_params": {
                    "function_id": function_id,
                    **search_params
                },
                "data_size": len(str(result)),
                "data_type": type(result).__name__,
                "data_keys": list(result.keys()) if isinstance(result, dict) else None,
                "timestamp": time.time()
            }
        else:
            return {
                "success": True,
                "message": "緩存搜尋完成，未找到匹配結果",
                "cache_hit": False,
                "search_params": {
                    "function_id": function_id,
                    **search_params
                },
                "timestamp": time.time()
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "緩存搜尋失敗",
                "message": str(e),
                "search_params": {
                    "function_id": function_id,
                    **search_params
                },
                "timestamp": time.time()
            }
        )


@router.get("/files")
async def list_cache_files(
    pattern: Optional[str] = Query(None, description="文件名模式 (支持通配符)"),
    limit: int = Query(20, ge=1, le=100, description="返回文件數量限制")
) -> Dict[str, Any]:
    """
    列出緩存文件
    
    根據模式篩選並列出緩存目錄中的文件
    """
    
    try:
        import glob
        import os
        
        cache_dir = cache_service.json_directory
        
        if pattern:
            # 使用模式搜尋
            search_pattern = os.path.join(cache_dir, pattern)
            files = glob.glob(search_pattern)
        else:
            # 列出所有 JSON 文件
            search_pattern = os.path.join(cache_dir, "*.json")
            files = glob.glob(search_pattern)
        
        # 獲取文件信息
        file_info = []
        for file_path in files[:limit]:
            try:
                stat = os.stat(file_path)
                file_info.append({
                    "filename": os.path.basename(file_path),
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024*1024), 3),
                    "modified_time": stat.st_mtime
                })
            except Exception:
                continue
        
        # 按修改時間排序
        file_info.sort(key=lambda x: x["modified_time"], reverse=True)
        
        return {
            "success": True,
            "message": f"緩存文件列表 (顯示 {len(file_info)} 個文件)",
            "search_pattern": pattern or "*.json",
            "total_found": len(files),
            "displayed": len(file_info),
            "cache_directory": cache_dir,
            "files": file_info,
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "文件列表獲取失敗",
                "message": str(e),
                "timestamp": time.time()
            }
        )


@router.delete("/clear")
async def clear_cache(
    confirm: bool = Query(False, description="確認清理緩存"),
    older_than_days: Optional[int] = Query(None, ge=1, description="清理多少天前的文件")
) -> Dict[str, Any]:
    """
    清理緩存文件
    
    ⚠️ 注意：這會刪除緩存文件，請謹慎使用
    """
    
    if not confirm:
        return {
            "success": False,
            "message": "清理操作需要確認",
            "required_parameter": "confirm=true",
            "warning": "這會刪除緩存文件，請謹慎使用",
            "timestamp": time.time()
        }
    
    try:
        import glob
        import os
        import time as time_module
        
        cache_dir = cache_service.json_directory
        pattern = os.path.join(cache_dir, "*.json")
        files = glob.glob(pattern)
        
        deleted_count = 0
        deleted_size = 0
        
        current_time = time_module.time()
        cutoff_time = current_time - (older_than_days * 24 * 3600) if older_than_days else 0
        
        for file_path in files:
            try:
                stat = os.stat(file_path)
                
                # 如果指定了天數，只刪除舊文件
                if older_than_days and stat.st_mtime > cutoff_time:
                    continue
                
                file_size = stat.st_size
                os.remove(file_path)
                deleted_count += 1
                deleted_size += file_size
                
            except Exception:
                continue
        
        return {
            "success": True,
            "message": f"緩存清理完成",
            "deleted_files": deleted_count,
            "deleted_size_mb": round(deleted_size / (1024*1024), 3),
            "older_than_days": older_than_days,
            "cache_directory": cache_dir,
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "緩存清理失敗",
                "message": str(e),
                "timestamp": time.time()
            }
        )
