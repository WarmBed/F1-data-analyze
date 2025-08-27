#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 Analysis API - 完整版本
支援所有年份賽事、賽段選擇的 REST API 介面

版本: 2.0 
作者: F1 Analysis Team
支援功能: 1-22 + 所有子功能 (4.1-4.5, 6.1-6.7, 7.1-7.2, 11.1-11.2, 12.1-12.2, 14.1-14.4, 16.1-16.4)
"""

import os
import sys
import json
import traceback
import logging
import asyncio
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

# FastAPI 相關導入
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 設定日誌 - 遵循核心開發原則，輸出到 logs/ 目錄
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/f1_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI 應用初始化
app = FastAPI(
    title="F1 Analysis API",
    description="F1 賽事數據分析 REST API - 完整功能版本",
    version="2.0.0"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 設定常數
DEBUG_MODE = True
API_VERSION = "2.0.0"

# 支援的年份和選項
RACE_OPTIONS = {
    2024: ["Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami", "Emilia Romagna", 
           "Monaco", "Canada", "Spain", "Austria", "Great Britain", "Hungary", "Belgium", 
           "Netherlands", "Italy", "Azerbaijan", "Singapore", "United States", "Mexico", 
           "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"],
    2025: ["Australia", "China", "Japan", "Bahrain", "Saudi Arabia", "Miami", "Emilia Romagna",
           "Monaco", "Canada", "Spain", "Austria", "Great Britain", "Hungary", "Belgium",
           "Netherlands", "Italy", "Azerbaijan", "Singapore", "United States", "Mexico",
           "Brazil", "Abu Dhabi"]
}

SESSION_TYPES = ["R", "Q", "FP1", "FP2", "FP3", "S"]

# Pydantic 模型
class AnalysisRequest(BaseModel):
    """分析請求模型"""
    year: int = Field(..., description="賽季年份", ge=2024, le=2025)
    race: str = Field(..., description="賽事名稱")
    session: str = Field(..., description="賽段類型")
    function_id: Union[str, int] = Field(..., description="功能編號")
    driver1: Optional[str] = Field(None, description="車手1代碼 (單車手分析或雙車手比較用)")
    driver2: Optional[str] = Field(None, description="車手2代碼 (雙車手比較用)")
    corner_number: Optional[int] = Field(None, description="彎道編號 (彎道分析用)")
    
    class Config:
        schema_extra = {
            "example": {
                "year": 2024,
                "race": "Bahrain",
                "session": "R",
                "function_id": "5",
                "driver1": "VER",
                "driver2": None,
                "corner_number": None
            }
        }

class APIResponse(BaseModel):
    """API 響應模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

def log_message(message: str, level: str = "INFO"):
    """記錄訊息"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    level_emoji = {
        "DEBUG": "🔍",
        "INFO": "ℹ️", 
        "WARNING": "⚠️",
        "ERROR": "❌",
        "SUCCESS": "✅",
        "CRITICAL": "🚨"
    }
    emoji = level_emoji.get(level, "📝")
    print(f"[{timestamp}] {emoji} [{level}] {message}")
    
    if level == "DEBUG":
        logger.debug(message)
    elif level == "INFO":
        logger.info(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
    elif level == "CRITICAL":
        logger.critical(message)
    else:
        logger.info(message)

def _process_analysis_result(result, start_time: float, function_id: Union[str, int], 
                           year: int, race: str, session: str) -> Dict[str, Any]:
    """處理分析結果的輔助函數"""
    end_time = datetime.now().timestamp()
    execution_time = round(end_time - start_time, 2)
    
    if result and result.returncode == 0:
        log_message(f"功能 {function_id} 執行成功", "SUCCESS")
        
        # 嘗試解析輸出中的JSON數據
        output_data = {}
        if result.stdout:
            try:
                # 查找輸出中的JSON檔案路徑
                lines = result.stdout.split('\n')
                json_files = []
                for line in lines:
                    if 'JSON輸出已保存到:' in line or 'JSON輸出已儲存到:' in line:
                        json_path = line.split(':')[-1].strip()
                        if os.path.exists(json_path):
                            json_files.append(json_path)
                
                # 讀取JSON檔案
                if json_files:
                    for json_file in json_files:
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                file_data = json.load(f)
                                output_data[os.path.basename(json_file)] = file_data
                        except Exception as e:
                            log_message(f"讀取JSON檔案 {json_file} 失敗: {e}", "WARNING")
                            
            except Exception as e:
                log_message(f"解析輸出數據失敗: {e}", "WARNING")
        
        return {
            "success": True,
            "message": f"功能 {function_id} 分析完成",
            "execution_time": f"{execution_time}秒",
            "function_id": str(function_id),
            "parameters": {
                "year": year,
                "race": race,
                "session": session
            },
            "output": result.stdout,
            "json_data": output_data if output_data else None
        }
    else:
        error_msg = result.stderr if result and result.stderr else "未知錯誤"
        log_message(f"功能 {function_id} 執行失敗: {error_msg}", "ERROR")
        
        return {
            "success": False,
            "message": f"功能 {function_id} 分析失敗",
            "error": error_msg,
            "execution_time": f"{execution_time}秒",
            "function_id": str(function_id),
            "parameters": {
                "year": year,
                "race": race,
                "session": session
            }
        }

@app.get("/", response_model=APIResponse)
async def root():
    """API 根路由"""
    supported_modules = [
        # 基礎分析模組 (1-4)
        "rain_analysis", "track_path_analysis", "pitstop_analysis", "accident_analysis",
        # 單車手分析模組 (5-13)
        "single_driver_analysis", "single_driver_telemetry", "driver_comparison", 
        "race_position_changes", "race_overtaking_statistics", "single_driver_overtaking",
        "single_dnf_analysis", "corner_detailed_analysis", "single_driver_all_corners",
        # 全部車手分析模組 (14-17)
        "all_drivers_analysis", "driver_statistics_overview", "driver_telemetry_statistics",
        "driver_overtaking_analysis", "driver_fastest_lap_ranking", "corner_speed_analysis",
        # 超車分析子模組 (16.1-16.4)
        "all_drivers_annual_overtaking", "all_drivers_overtaking_performance",
        "all_drivers_overtaking_visualization", "all_drivers_overtaking_trends",
        # DNF分析 (17)
        "all_dnf_analysis"
    ]
    
    return APIResponse(
        success=True,
        message="F1 Analysis API is running",
        data={
            "version": API_VERSION,
            "description": "F1 賽事數據分析 REST API - 完整功能版本",
            "debug_mode": DEBUG_MODE,
            "endpoints": ["/analyze", "/health", "/modules", "/supported-functions", "/drivers"],
            "supported_modules": supported_modules,
            "total_modules": len(supported_modules),
            "supported_years": list(RACE_OPTIONS.keys()),
            "session_types": SESSION_TYPES
        }
    )

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/modules")
async def get_modules():
    """獲取支援的模組列表"""
    modules = {
        "basic_analysis": {
            "1": "降雨強度分析 (Rain Intensity Analysis)",
            "2": "賽道路線分析 (Track Path Analysis)", 
            "3": "進站策略分析 (Pitstop Strategy Analysis)",
            "3.1": "單場賽事進站統計 (Race Pitstop Statistics)",
            "4": "獨立事故分析 (Independent Accident Analysis)",
            "4.1": "關鍵事件摘要 (Key Events Summary)",
            "4.2": "特殊事件報告 (Special Incident Reports)",
            "4.3": "車手嚴重程度分數統計 (Driver Severity Scores)",
            "4.4": "車隊風險分數統計 (Team Risk Scores)",
            "4.5": "所有事件詳細列表 (All Incidents Summary)"
        },
        "single_driver_analysis": {
            "5": "單一車手綜合分析 (Single Driver Comprehensive Analysis)",
            "6": "單一車手詳細遙測分析 (Single Driver Detailed Telemetry)",
            "6.1": "詳細圈次分析 (Complete Lap Analysis)",
            "6.2": "詳細輪胎策略分析 (Detailed Tire Strategy)",
            "6.3": "輪胎性能詳細分析 (Tire Performance Analysis)",
            "6.4": "進站記錄 (Pitstop Records)",
            "6.5": "特殊事件分析 (Special Events)",
            "6.6": "最快圈速度遙測數據 (Fastest Lap Speed Data)",
            "6.7": "指定圈次完整遙測數據 (Specific Lap Full Telemetry)",
            "7": "雙車手比較分析 (Two Driver Comparison)",
            "7.1": "速度差距分析 + 原始數據 (Speed Gap Analysis + Raw Data)",
            "7.2": "距離差距分析 + 原始數據 (Distance Gap Analysis + Raw Data)",
            "8": "賽事位置變化圖 + Raw Data (Race Position Changes Chart + Raw Data)",
            "9": "賽事超車統計分析 + Raw Data (Race Overtaking Statistics + Raw Data)",
            "10": "單一車手超車分析 (Single Driver Overtaking Analysis)",
            "11": "獨立單一車手DNF分析 (Independent Single Driver DNF)",
            "11.1": "詳細DNF與責任事故分析 (Detailed DNF & Incident Analysis + Raw Data)",
            "11.2": "年度DNF統計摘要 (Annual DNF Statistics Summary + Raw Data)",
            "12": "單賽事指定彎道詳細分析 (Single Race Specific Corner Detailed Analysis)",
            "12.1": "單一車手詳細彎道分析 (Single Driver Corner Analysis + JSON)",
            "12.2": "團隊車手對比分析 (Team Drivers Corner Comparison + JSON)",
            "13": "單一車手指定賽事全部彎道詳細分析 (Single Driver All Corners Detailed Analysis)"
        },
        "all_drivers_analysis": {
            "14": "所有車手綜合分析 (All Drivers Comprehensive Analysis)",
            "14.1": "車手數據統計總覽 (Driver Statistics Overview)",
            "14.2": "車手遙測資料統計 (Driver Telemetry Statistics)",
            "14.3": "車手超車分析 (Driver Overtaking Analysis)",
            "14.4": "最速圈排名分析 (Fastest Lap Ranking Analysis)",
            "14.9": "完整綜合分析 (Full Comprehensive Analysis)",
            "15": "彎道速度分析 (Corner Speed Analysis)",
            "16": "全部車手超車分析 (All Drivers Overtaking)",
            "16.1": "年度超車統計 (Annual Overtaking Statistics)",
            "16.2": "表現比較分析 (Performance Comparison)",
            "16.3": "視覺化分析 (Visualization Analysis)",
            "16.4": "趨勢分析 (Trends Analysis)",
            "17": "獨立全部車手DNF分析 (Independent All Drivers DNF)"
        },
        "system_functions": {
            "18": "重新載入賽事數據 (Reload Race Data)",
            "19": "顯示模組狀態 (Show Module Status)",
            "20": "顯示幫助信息 (Show Help)",
            "21": "超車暫存管理 (Overtaking Cache Management)",
            "22": "DNF暫存管理 (DNF Cache Management)"
        }
    }
    
    return APIResponse(
        success=True,
        message="支援的分析模組列表",
        data=modules
    )

@app.get("/supported-functions")
async def get_supported_functions():
    """獲取所有支援的功能編號"""
    functions = [
        # 基礎功能 1-22
        "1", "2", "3", "3.1", "4", "5", "6", "7", "8", "9", "10", 
        "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22",
        # 事故分析子功能 4.x
        "4.1", "4.2", "4.3", "4.4", "4.5",
        # 遙測分析子功能 6.x
        "6.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7",
        # 車手比較子功能 7.x
        "7.1", "7.2",
        # DNF分析子功能 11.x
        "11.1", "11.2",
        # 彎道分析子功能 12.x
        "12.1", "12.2",
        # 車手統計子功能 14.x
        "14.1", "14.2", "14.3", "14.4", "14.9",
        # 超車分析子功能 16.x
        "16.1", "16.2", "16.3", "16.4"
    ]
    
    return APIResponse(
        success=True,
        message="所有支援的功能編號",
        data={
            "functions": functions,
            "total_functions": len(functions),
            "categories": {
                "basic": ["1", "2", "3", "3.1"],
                "accident": ["4"] + [f"4.{i}" for i in range(1, 6)],
                "single_driver": ["5", "6", "7", "8", "9", "10", "11", "12", "13"] + 
                               [f"6.{i}" for i in range(1, 8)] + ["7.1", "7.2"] + 
                               ["11.1", "11.2"] + ["12.1", "12.2"],
                "all_drivers": ["14", "15", "16", "17"] + 
                              [f"14.{i}" for i in [1, 2, 3, 4, 9]] + 
                              [f"16.{i}" for i in range(1, 5)],
                "system": ["18", "19", "20", "21", "22"]
            },
            "parameter_requirements": {
                "single_driver_functions": ["5", "6", "8", "9", "10", "11", "13"] + 
                                         [f"6.{i}" for i in range(1, 8)] + ["11.1", "11.2"],
                "dual_driver_functions": ["7", "7.1", "7.2"],
                "corner_analysis_functions": ["12.1", "12.2"],
                "note": "參數 driver1, driver2, corner_number 由 API 接收但不傳遞給主程式，各模組會在內部自動處理車手和彎道選擇"
            }
        }
    )

@app.get("/drivers")
async def get_common_drivers():
    """獲取常用車手代碼列表"""
    drivers = {
        "2024_drivers": {
            "VER": "Max Verstappen (Red Bull)",
            "PER": "Sergio Perez (Red Bull)",
            "LEC": "Charles Leclerc (Ferrari)",
            "SAI": "Carlos Sainz (Ferrari)",
            "NOR": "Lando Norris (McLaren)",
            "PIA": "Oscar Piastri (McLaren)",
            "RUS": "George Russell (Mercedes)",
            "HAM": "Lewis Hamilton (Mercedes)",
            "ALO": "Fernando Alonso (Aston Martin)",
            "STR": "Lance Stroll (Aston Martin)",
            "TSU": "Yuki Tsunoda (AlphaTauri)",
            "RIC": "Daniel Ricciardo (AlphaTauri)",
            "ALB": "Alexander Albon (Williams)",
            "SAR": "Logan Sargeant (Williams)",
            "HUL": "Nico Hulkenberg (Haas)",
            "MAG": "Kevin Magnussen (Haas)",
            "GAS": "Pierre Gasly (Alpine)",
            "OCO": "Esteban Ocon (Alpine)",
            "BOT": "Valtteri Bottas (Alfa Romeo)",
            "ZHO": "Zhou Guanyu (Alfa Romeo)"
        },
        "2025_drivers": {
            "VER": "Max Verstappen (Red Bull)",
            "PER": "Sergio Perez (Red Bull)",
            "LEC": "Charles Leclerc (Ferrari)",
            "HAM": "Lewis Hamilton (Ferrari)",
            "NOR": "Lando Norris (McLaren)",
            "PIA": "Oscar Piastri (McLaren)",
            "RUS": "George Russell (Mercedes)",
            "ANT": "Andrea Kimi Antonelli (Mercedes)",
            "ALO": "Fernando Alonso (Aston Martin)",
            "STR": "Lance Stroll (Aston Martin)"
        },
        "common_codes": ["VER", "LEC", "HAM", "NOR", "RUS", "ALO", "PER", "SAI", "PIA", "GAS"]
    }
    
    return APIResponse(
        success=True,
        message="支援的車手代碼列表",
        data=drivers
    )

@app.post("/analyze", response_model=APIResponse)
async def analyze_data(request: AnalysisRequest):
    """執行F1數據分析"""
    log_message(f"收到分析請求: 功能{request.function_id}, {request.year} {request.race} {request.session}", "INFO")
    
    try:
        # 驗證年份
        if request.year not in RACE_OPTIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"不支援的年份: {request.year}。支援的年份: {list(RACE_OPTIONS.keys())}"
            )
        
        # 驗證賽事
        if request.race not in RACE_OPTIONS[request.year]:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的賽事: {request.race}。{request.year}年支援的賽事: {RACE_OPTIONS[request.year]}"
            )
        
        # 驗證賽段類型
        if request.session not in SESSION_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的賽段類型: {request.session}。支援的類型: {SESSION_TYPES}"
            )
        
        # 使用統一的功能映射器 - 符合核心開發原則的參數化模式
        start_time = datetime.now().timestamp()
        
        try:
            # 初始化數據載入器
            current_dir = os.path.dirname(os.path.abspath(__file__))
            modules_dir = os.path.join(current_dir, 'modules')
            if modules_dir not in sys.path:
                sys.path.insert(0, modules_dir)
            
            # 動態導入核心模組
            log_message("載入核心模組...", "INFO")
            from modules.compatible_data_loader import CompatibleF1DataLoader
            from modules.function_mapper import F1AnalysisFunctionMapper
            
            # 創建數據載入器並載入數據
            data_loader = CompatibleF1DataLoader()
            
            log_message(f"載入數據: {request.year} {request.race} {request.session}", "INFO")
            if not data_loader.load_race_data(request.year, request.race, request.session):
                return APIResponse(
                    success=False,
                    message="數據載入失敗",
                    data={
                        "error": f"無法載入 {request.year} {request.race} {request.session} 的數據",
                        "function_id": str(request.function_id),
                        "parameters": {
                            "year": request.year,
                            "race": request.race,
                            "session": request.session
                        }
                    }
                )
            
            # 創建功能映射器 - 根據核心開發原則
            log_message("初始化功能映射器...", "INFO")
            mapper = F1AnalysisFunctionMapper(
                data_loader=data_loader,
                dynamic_team_mapping=None,  # 將從數據載入器獲取
                f1_analysis_instance=None,  # 將在映射器內部創建
                driver=request.driver1,     # 主要車手
                driver2=request.driver2     # 次要車手
            )
            
            # 執行分析功能 - 遵循統一執行標準
            log_message(f"執行功能: {request.function_id}", "INFO")
            
            # 設定執行參數 - 確保兼容性
            execution_params = {
                "function_id": request.function_id,
                "driver1": request.driver1,
                "driver2": request.driver2,
                "corner_number": request.corner_number,
                "year": request.year,
                "race": request.race,
                "session": request.session
            }
            
            # 嘗試執行分析，如果失敗則嘗試不同參數組合
            analysis_result = None
            try:
                # 首先嘗試完整參數
                analysis_result = mapper.execute_function_by_number(
                    function_id=request.function_id,
                    driver1=request.driver1,
                    driver2=request.driver2,
                    corner_number=request.corner_number,
                    show_detailed_output=True,  # API 預設顯示詳細輸出
                    year=request.year,
                    race=request.race,
                    session=request.session
                )
            except TypeError as te:
                log_message(f"參數錯誤，嘗試簡化參數: {te}", "WARNING")
                # 如果有參數問題，嘗試簡化參數
                try:
                    analysis_result = mapper.execute_function_by_number(
                        function_id=request.function_id,
                        driver1=request.driver1,
                        driver2=request.driver2,
                        corner_number=request.corner_number
                    )
                except Exception as e2:
                    log_message(f"簡化參數也失敗: {e2}", "ERROR")
                    analysis_result = {
                        "success": False,
                        "message": f"功能執行失敗: 參數錯誤",
                        "error": f"TypeError: {te}, 簡化嘗試: {e2}"
                    }
            except Exception as e:
                log_message(f"執行異常: {e}", "ERROR")
                analysis_result = {
                    "success": False,
                    "message": f"功能執行失敗",
                    "error": str(e)
                }
            
            # 確保分析結果為字典格式
            if not isinstance(analysis_result, dict):
                log_message("分析結果格式異常，使用默認格式", "WARNING")
                analysis_result = {
                    "success": False,
                    "message": "分析結果格式異常",
                    "error": f"返回結果類型: {type(analysis_result)}",
                    "function_id": str(request.function_id),
                    "raw_result": str(analysis_result)[:500]  # 截取前500字符作為調試信息
                }
            
            # 計算執行時間
            end_time = datetime.now().timestamp()
            execution_time = round(end_time - start_time, 2)
            
            # 增強分析結果 - 添加執行元數據
            analysis_result.update({
                "execution_time": f"{execution_time}秒",
                "function_id": str(request.function_id),
                "parameters": {
                    "year": request.year,
                    "race": request.race,
                    "session": request.session,
                    "driver1": request.driver1,
                    "driver2": request.driver2,
                    "corner_number": request.corner_number
                },
                "api_version": API_VERSION,
                "timestamp": datetime.now().isoformat(),
                "cache_used": analysis_result.get("cache_used", False)
            })
            
            # 嘗試載入 JSON 數據 - 增加數據豐富度
            if analysis_result.get("success"):
                try:
                    # 查找 json 目錄中的相關文件
                    json_dir = os.path.join(os.getcwd(), "json")
                    if os.path.exists(json_dir):
                        # 查找最新的相關 JSON 文件
                        json_files = []
                        for file in os.listdir(json_dir):
                            if file.endswith('.json') and str(request.function_id) in file:
                                json_path = os.path.join(json_dir, file)
                                json_files.append(json_path)
                        
                        # 載入找到的 JSON 文件
                        if json_files:
                            analysis_result["json_files"] = []
                            for json_file in json_files[:3]:  # 最多3個文件，避免過大
                                try:
                                    with open(json_file, 'r', encoding='utf-8') as f:
                                        json_data = json.load(f)
                                        analysis_result["json_files"].append({
                                            "filename": os.path.basename(json_file),
                                            "path": json_file,
                                            "data": json_data
                                        })
                                        log_message(f"成功載入 JSON 文件: {os.path.basename(json_file)}", "SUCCESS")
                                except Exception as e:
                                    log_message(f"載入 JSON 文件失敗 {json_file}: {e}", "WARNING")
                        else:
                            log_message(f"未找到功能 {request.function_id} 的 JSON 文件", "WARNING")
                    else:
                        log_message("json 目錄不存在", "WARNING")
                except Exception as e:
                    log_message(f"搜索 JSON 文件時發生錯誤: {e}", "WARNING")
            
            # 驗證分析結果
            if not analysis_result.get("success"):
                log_message(f"功能 {request.function_id} 執行失敗: {analysis_result.get('message', '未知錯誤')}", "ERROR")
            else:
                log_message(f"功能 {request.function_id} 執行成功", "SUCCESS")
            
        except ImportError as e:
            log_message(f"模組載入失敗: {str(e)}", "ERROR")
            analysis_result = {
                "success": False,
                "message": "系統模組載入失敗",
                "error": str(e),
                "function_id": str(request.function_id),
                "traceback": traceback.format_exc() if DEBUG_MODE else None
            }
        except Exception as e:
            log_message(f"分析執行異常: {str(e)}", "ERROR")
            analysis_result = {
                "success": False,
                "message": "分析執行失敗",
                "error": str(e),
                "function_id": str(request.function_id),
                "traceback": traceback.format_exc() if DEBUG_MODE else None
            }
        
        return APIResponse(
            success=analysis_result.get("success", False),
            message=analysis_result.get("message", "分析完成"),
            data=analysis_result
        )
        
    except subprocess.TimeoutExpired:
        log_message(f"分析超時: 功能 {request.function_id}", "ERROR")
        return APIResponse(
            success=False,
            message="分析超時",
            data={
                "error": "分析執行超過5分鐘時間限制",
                "function_id": str(request.function_id)
            }
        )
        
    except Exception as e:
        log_message(f"分析執行異常: {str(e)}", "ERROR")
        log_message(traceback.format_exc(), "DEBUG")
        
        return APIResponse(
            success=False,
            message="分析執行失敗",
            data={
                "error": str(e),
                "function_id": str(request.function_id),
                "traceback": traceback.format_exc() if DEBUG_MODE else None
            }
        )

# 錯誤處理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 錯誤處理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """一般錯誤處理"""
    log_message(f"未處理的錯誤: {str(exc)}", "ERROR")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "內部服務器錯誤",
            "error": str(exc) if DEBUG_MODE else "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    try:
        import uvicorn
    except ImportError:
        print("❌ 缺少 uvicorn 套件")
        print("安裝命令: pip install uvicorn")
        sys.exit(1)
    
    try:
        import fastapi
        import pydantic
    except ImportError:
        print("❌ 缺少 FastAPI 相關套件")
        print("安裝命令: pip install fastapi pydantic")
        sys.exit(1)
    
    log_message("🚀 啟動 F1 Analysis API 服務器...", "INFO")
    log_message(f"📋 API 版本: {API_VERSION}", "INFO")
    log_message(f"🔧 調試模式: {DEBUG_MODE}", "INFO")
    log_message("🎯 核心開發原則: API完全可呼叫", "INFO")
    
    print("\n📋 API 端點:")
    print("   • 根端點: http://localhost:8000/")
    print("   • 分析端點: http://localhost:8000/analyze")
    print("   • 健康檢查: http://localhost:8000/health")
    print("   • API文檔: http://localhost:8000/docs")
    print("   • 模組列表: http://localhost:8000/modules")
    print("\n🔧 使用 Ctrl+C 停止服務器")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info" if not DEBUG_MODE else "debug",
            reload=DEBUG_MODE
        )
    except KeyboardInterrupt:
        log_message("🛑 API 服務器已停止", "INFO")
    except Exception as e:
        log_message(f"❌ API 服務器啟動失敗: {e}", "ERROR")
        sys.exit(1)
