#!/usr/bin/env python3
"""
F1 Analysis Simple Service - 簡化版分析服務
重新開始的簡單實現，專注核心功能

版本: 2.0 (簡化版)
作者: F1 Analysis Team
"""

import os
import sys
import asyncio
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, Optional

# 添加專案根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 導入已經工作的組件
from api.services.cache_service import F1AnalysisCacheService
from api.models.function_specs import FUNCTION_SPECS, FunctionSpec, get_function_spec


class SimpleF1AnalysisService:
    """簡化版 F1 分析服務 - 專注核心功能"""
    
    def __init__(self):
        self.cache_service = F1AnalysisCacheService()
        self._function_specs = FUNCTION_SPECS
        print("[SERVICE] 簡化版分析服務已初始化")

    def _get_spec(self, function_id: int) -> FunctionSpec:
        """Return metadata for the requested function."""

        try:
            return get_function_spec(function_id)
        except KeyError as exc:
            raise ValueError(f"Unsupported function_id: {function_id}") from exc

    def _prepare_params(self, spec: FunctionSpec, raw_params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and extract parameters required by the CLI."""

        prepared: Dict[str, Any] = {}

        for name in spec.required_params:
            if name not in raw_params or raw_params[name] in (None, ""):
                raise ValueError(f"Missing required parameter '{name}' for function {spec.function_id}")
            prepared[name] = raw_params[name]

        for name in spec.optional_params:
            if name in raw_params and raw_params[name] not in (None, ""):
                prepared[name] = raw_params[name]

        return prepared

    def _build_cli_command(self, spec: FunctionSpec, params: Dict[str, Any]) -> list[str]:
        """Construct the CLI command for the given specification."""

        cmd = [
            "python",
            "f1_analysis_modular_main.py",
            "-f", str(spec.function_id)
        ]

        for param_name, flag in spec.cli_flag_map.items():
            if param_name in params:
                value = params[param_name]
                if value in (None, ""):
                    continue
                cmd.extend([flag, str(value)])

        return cmd
    
    async def execute_analysis(self, function_id: int, **params) -> Dict[str, Any]:
        """
        執行分析 - 簡化版邏輯
        
        Args:
            function_id: 功能 ID (1-52)
            **params: 分析參數
            
        Returns:
            Dict: 簡化的響應格式
        """
        request_id = f"req_{int(time.time() * 1000)}"
        print(f"[SERVICE] 開始分析 {request_id}: 功能 {function_id}")
        
        start_time = time.time()
        
        try:
            spec = self._get_spec(function_id)
            prepared_params = self._prepare_params(spec, params)
            force_refresh = bool(params.get("force_refresh"))

            if not force_refresh:
                print(f"[SERVICE] 檢查緩存...")
                cached_result = self.cache_service.search_cached_analysis(function_id, **prepared_params)

                if cached_result:
                    execution_time = time.time() - start_time
                    print(f"[SERVICE] ✅ 緩存命中! (耗時: {execution_time:.3f}s)")

                    return {
                        "success": True,
                        "message": f"分析完成 (功能 {function_id})",
                        "data": cached_result,
                        "source": "cache",
                        "execution_time": f"{execution_time:.3f}s",
                        "request_id": request_id,
                        "timestamp": datetime.now().isoformat(),
                        "function_spec": spec.__dict__,
                    }

            print(f"[SERVICE] ❌ 緩存未命中，嘗試 CLI 執行...")
            cli_result = await self._simple_cli_execution(spec, prepared_params)
            
            execution_time = time.time() - start_time
            
            if cli_result["success"]:
                print(f"[SERVICE] ✅ CLI 執行成功! (耗時: {execution_time:.3f}s)")
                return {
                    "success": True,
                    "message": f"分析完成 (功能 {spec.function_id})",
                    "data": cli_result["data"],
                    "source": "cli",
                    "execution_time": f"{execution_time:.3f}s",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat(),
                    "function_spec": spec.__dict__,
                    "cli_info": cli_result.get("cli_info", {})
                }
            else:
                print(f"[SERVICE] ❌ CLI 執行失敗! (耗時: {execution_time:.3f}s)")
                return {
                    "success": False,
                    "message": "分析執行失敗",
                    "error": cli_result.get("error", "未知錯誤"),
                    "source": "cli_failed",
                    "execution_time": f"{execution_time:.3f}s",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"[SERVICE] ❌ 服務異常! (耗時: {execution_time:.3f}s): {e}")
            
            return {
                "success": False,
                "message": "服務執行異常",
                "error": str(e),
                "source": "service_error",
                "execution_time": f"{execution_time:.3f}s",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _simple_cli_execution(self, spec: FunctionSpec, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        簡化版 CLI 執行
        
        Args:
            function_id: 功能 ID
            **params: 參數
            
        Returns:
            Dict: CLI 執行結果
        """
        try:
            # 建構基本 CLI 命令
            cmd = self._build_cli_command(spec, params)
            
            print(f"[CLI] 執行命令: {' '.join(cmd)}")
            
            # 簡單的同步執行 (避免複雜的非同步問題)
            start_time = time.time()
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2分鐘超時
                cwd=os.getcwd()
            )
            
            execution_time = time.time() - start_time
            
            if process.returncode == 0:
                print(f"[CLI] ✅ 命令執行成功 (耗時: {execution_time:.3f}s)")
                
                # 嘗試重新搜尋緩存，看是否生成了新文件
                await asyncio.sleep(0.5)  # 等待文件寫入
                new_cached = self.cache_service.search_cached_analysis(spec.function_id, **params)
                
                if new_cached:
                    return {
                        "success": True,
                        "data": new_cached,
                        "cli_info": {
                            "command": " ".join(cmd),
                            "execution_time": f"{execution_time:.3f}s",
                            "stdout_length": len(process.stdout),
                            "new_file_generated": True
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "CLI 執行成功但未找到輸出文件",
                        "cli_info": {
                            "command": " ".join(cmd),
                            "execution_time": f"{execution_time:.3f}s",
                            "stdout": process.stdout[:500] if process.stdout else "",
                            "new_file_generated": False
                        }
                    }
            else:
                print(f"[CLI] ❌ 命令執行失敗 (返回碼: {process.returncode})")
                return {
                    "success": False,
                    "error": f"CLI 執行失敗 (返回碼: {process.returncode})",
                    "cli_info": {
                        "command": " ".join(cmd),
                        "execution_time": f"{execution_time:.3f}s",
                        "returncode": process.returncode,
                        "stderr": process.stderr[:500] if process.stderr else "",
                        "stdout": process.stdout[:500] if process.stdout else ""
                    }
                }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "CLI 執行超時 (超過2分鐘)",
                "cli_info": {
                    "command": " ".join(cmd),
                    "timeout": True
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"CLI 執行異常: {str(e)}",
                "cli_info": {
                    "command": " ".join(cmd),
                    "exception": str(e)
                }
            }
    
    async def get_cache_status(self) -> Dict[str, Any]:
        """獲取緩存狀態 - 簡化版"""
        try:
            print("[SERVICE] 獲取緩存狀態...")
            stats = self.cache_service.get_cache_statistics()
            
            return {
                "success": True,
                "message": "緩存狀態獲取成功",
                "cache_summary": {
                    "total_files": stats["summary"]["total_files"],
                    "total_size_mb": stats["summary"]["total_size_mb"],
                    "cache_directory": stats["summary"]["cache_directory"]
                },
                "recent_files_count": len(stats["recent_files"]),
                "supported_functions_count": len(stats["supported_functions"]),
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": "緩存狀態獲取失敗",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查 - 簡化版"""
        try:
            # 測試緩存服務
            cache_test = await self.get_cache_status()
            cache_healthy = cache_test["success"]
            
            # 簡單的系統檢查
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            current_dir = os.getcwd()
            
            return {
                "success": True,
                "status": "healthy" if cache_healthy else "degraded",
                "message": "服務運行正常",
                "checks": {
                    "cache_service": "healthy" if cache_healthy else "error",
                    "python_version": python_version,
                    "working_directory": current_dir,
                    "cli_file_exists": os.path.exists("f1_analysis_modular_main.py")
                },
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "success": False,
                "status": "unhealthy", 
                "message": "健康檢查失敗",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
