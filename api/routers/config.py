#!/usr/bin/env python3
"""
F1 Analysis API - 配置數據路由
提供靜態配置數據的 API 端點

版本: 2.0
作者: F1 Analysis Team
日期: 2025-12-05
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import json
import os
import time
from pathlib import Path

# 創建路由器
router = APIRouter(
    prefix="/config",
    tags=["配置數據"],
    responses={
        404: {"description": "配置文件不存在"},
        500: {"description": "配置讀取錯誤"}
    }
)

# 配置目錄路徑
CONFIG_DIR = Path(__file__).parents[2] / "config"


def _load_json_config(filename: str) -> Dict[str, Any]:
    """
    載入 JSON 配置文件
    
    Args:
        filename: 配置文件名稱
        
    Returns:
        配置數據字典
        
    Raises:
        HTTPException: 文件不存在或讀取失敗
    """
    file_path = CONFIG_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "error": "config_not_found",
                "message": f"配置文件 {filename} 不存在",
                "path": str(file_path),
                "timestamp": time.time()
            }
        )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "json_parse_error",
                "message": f"配置文件 {filename} 解析失敗: {str(e)}",
                "timestamp": time.time()
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "config_read_error",
                "message": f"配置文件 {filename} 讀取失敗: {str(e)}",
                "timestamp": time.time()
            }
        )


@router.get("/tire-degradation")
async def get_tire_degradation_database() -> Dict[str, Any]:
    """
    獲取輪胎衰退數據庫
    
    返回各賽道、各輪胎類型的衰退係數和最佳 stint 長度
    
    用途:
    - Driver Strategy 模組的輪胎預測
    - Ranking Tower 的最佳進站時機計算
    """
    data = _load_json_config("tire_degradation_database.json")
    
    return {
        "success": True,
        "message": "輪胎衰退數據庫獲取成功",
        "config_type": "tire_degradation",
        "data": data,
        "timestamp": time.time()
    }


@router.get("/fuel-coefficients")
async def get_fuel_coefficients_database() -> Dict[str, Any]:
    """
    獲取燃油係數數據庫
    
    返回各賽道的燃油消耗率和單圈燃油影響係數
    
    用途:
    - Driver Strategy 模組的燃油校正計算
    - 圈速預測的燃油影響修正
    """
    data = _load_json_config("fuel_coefficients_database.json")
    
    return {
        "success": True,
        "message": "燃油係數數據庫獲取成功",
        "config_type": "fuel_coefficients",
        "data": data,
        "timestamp": time.time()
    }


@router.get("/track-features")
async def get_track_features_database() -> Dict[str, Any]:
    """
    獲取賽道特性數據庫
    
    返回各賽道的策略特性（進站次數、輪胎選擇等）
    
    用途:
    - Driver Strategy 模組的策略預測
    - 進站視窗計算
    """
    data = _load_json_config("track_features_database.json")
    
    return {
        "success": True,
        "message": "賽道特性數據庫獲取成功",
        "config_type": "track_features",
        "data": data,
        "timestamp": time.time()
    }


@router.get("/pit-loss")
async def get_pit_loss_database() -> Dict[str, Any]:
    """
    獲取進站時間損失數據庫
    
    返回各賽道的進站時間損失（秒）
    
    用途:
    - 進站策略計算
    - Undercut/Overcut 分析
    """
    data = _load_json_config("pit_loss_database.json")
    
    return {
        "success": True,
        "message": "進站時間損失數據庫獲取成功",
        "config_type": "pit_loss",
        "data": data,
        "timestamp": time.time()
    }


@router.get("/throttle-baseline")
async def get_throttle_baseline_database() -> Dict[str, Any]:
    """
    獲取 Throttle Baseline 數據庫
    
    返回各賽道的全油門比例基準值，用於省胎行為分析
    
    用途:
    - Ranking Tower 的 SF% (省胎比例) 計算
    - Driver Strategy 模組的駕駛風格分析
    - 當 current_ratio < baseline_mean - threshold 時判斷為省胎
    
    數據來源:
    - LiveF1 歷史 CarData.json 2023-2025
    - 基於 Throttle >= 95% 的採樣比例統計
    """
    data = _load_json_config("throttle_baseline_database.json")
    
    return {
        "success": True,
        "message": "Throttle Baseline 數據庫獲取成功",
        "config_type": "throttle_baseline",
        "data": data,
        "timestamp": time.time()
    }


@router.get("/throttle-baseline/{circuit}")
async def get_throttle_baseline_for_circuit(circuit: str) -> Dict[str, Any]:
    """
    獲取特定賽道的 Throttle Baseline
    
    Args:
        circuit: 賽道名稱 (例如 Monza, Spa, Suzuka)
    
    返回:
    - full_throttle_ratio: 該賽道的全油門比例基準值
    - avg_throttle: 平均油門值
    - 用於計算 SF% 的閾值
    """
    data = _load_json_config("throttle_baseline_database.json")
    
    circuits = data.get("circuits", {})
    global_baseline = data.get("global_baseline", {})
    
    # 嘗試找到賽道數據
    circuit_data = circuits.get(circuit)
    
    if not circuit_data:
        # 嘗試模糊匹配
        for key in circuits:
            if key.lower() == circuit.lower() or circuit.lower() in key.lower():
                circuit_data = circuits[key]
                circuit = key
                break
    
    if circuit_data:
        return {
            "success": True,
            "message": f"Throttle Baseline for {circuit}",
            "circuit": circuit,
            "data": circuit_data,
            "tire_saving_threshold": {
                "description": "當 full_throttle_ratio 低於此值時判斷為省胎",
                "threshold": circuit_data["full_throttle_ratio"]["mean"] - 0.05,
                "formula": "SF% = max(0, (baseline - current) / baseline * 100)"
            },
            "timestamp": time.time()
        }
    else:
        # 使用全局基準值
        return {
            "success": True,
            "message": f"Circuit {circuit} not found, using global baseline",
            "circuit": circuit,
            "data": {
                "full_throttle_ratio": global_baseline.get("full_throttle_ratio", {"mean": 0.35}),
                "avg_throttle": global_baseline.get("avg_throttle", {"mean": 43.0}),
                "is_global_baseline": True
            },
            "tire_saving_threshold": {
                "description": "使用全局基準值",
                "threshold": global_baseline.get("full_throttle_ratio", {}).get("mean", 0.35) - 0.05,
                "formula": "SF% = max(0, (baseline - current) / baseline * 100)"
            },
            "timestamp": time.time()
        }


@router.get("/all")
async def get_all_configs() -> Dict[str, Any]:
    """
    獲取所有配置數據庫
    
    一次性返回所有靜態配置，減少 API 調用次數
    
    用途:
    - 模組初始化時批量載入配置
    """
    configs = {}
    errors = []
    
    config_files = {
        "tire_degradation": "tire_degradation_database.json",
        "fuel_coefficients": "fuel_coefficients_database.json",
        "track_features": "track_features_database.json",
        "pit_loss": "pit_loss_database.json",
        "throttle_baseline": "throttle_baseline_database.json"
    }
    
    for key, filename in config_files.items():
        try:
            configs[key] = _load_json_config(filename)
        except HTTPException as e:
            errors.append({
                "config": key,
                "error": e.detail.get("message", str(e))
            })
        except Exception as e:
            errors.append({
                "config": key,
                "error": str(e)
            })
    
    return {
        "success": len(errors) == 0,
        "message": f"配置數據獲取完成 ({len(configs)}/{len(config_files)} 成功)",
        "data": configs,
        "errors": errors if errors else None,
        "timestamp": time.time()
    }


@router.get("/list")
async def list_available_configs() -> Dict[str, Any]:
    """
    列出可用的配置文件
    
    返回 config 目錄中所有 JSON 配置文件的列表
    """
    try:
        if not CONFIG_DIR.exists():
            return {
                "success": False,
                "message": "配置目錄不存在",
                "config_directory": str(CONFIG_DIR),
                "timestamp": time.time()
            }
        
        config_files = []
        for file_path in CONFIG_DIR.glob("*.json"):
            try:
                stat = file_path.stat()
                config_files.append({
                    "filename": file_path.name,
                    "size_bytes": stat.st_size,
                    "modified_time": stat.st_mtime
                })
            except Exception:
                continue
        
        # 按文件名排序
        config_files.sort(key=lambda x: x["filename"])
        
        return {
            "success": True,
            "message": f"找到 {len(config_files)} 個配置文件",
            "config_directory": str(CONFIG_DIR),
            "files": config_files,
            "api_endpoints": {
                "tire_degradation": "/api/v2/config/tire-degradation",
                "fuel_coefficients": "/api/v2/config/fuel-coefficients",
                "track_features": "/api/v2/config/track-features",
                "pit_loss": "/api/v2/config/pit-loss",
                "throttle_baseline": "/api/v2/config/throttle-baseline",
                "throttle_baseline_circuit": "/api/v2/config/throttle-baseline/{circuit}",
                "all": "/api/v2/config/all"
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "list_configs_failed",
                "message": str(e),
                "timestamp": time.time()
            }
        )
