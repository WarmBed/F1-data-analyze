#!/usr/bin/env python3
"""
F1 Analysis Simple Service - 簡化版分析服務
重新開始的簡單實現，專注核心功能

版本: 2.0 (簡化版)
作者: F1 Analysis Team
"""

# LOCAL_ONLY_REFACTOR:
# Despite living under api.services, this is currently the closest local
# execution engine: it checks cache and runs CLI modules without HTTP. Keep it
# as the temporary LocalAnalysisExecutor backend, then move it to core/analysis.

import os
import sys
import asyncio
import asyncio.subprocess as aio_subprocess
import time
from collections import deque
from datetime import datetime
from typing import Dict, Any, Optional, Deque, Union

from uuid import uuid4

# 添加專案根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 導入已經工作的組件
# V2 優化版緩存服務 - 減少 CPU 負載
from api.services.cache_service_v2 import F1AnalysisCacheServiceV2 as F1AnalysisCacheService
from api.models.function_specs import (
    FUNCTION_SPECS,
    FunctionSpec,
    get_function_spec,
    normalize_function_id,
)


class SimpleF1AnalysisService:
    """簡化版 F1 分析服務 - 專注核心功能"""

    def __init__(self):
        self.cache_service = F1AnalysisCacheService()
        self._function_specs = FUNCTION_SPECS

        # 服務狀態追蹤
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._recent_history: Deque[Dict[str, Any]] = deque(maxlen=25)
        self._metrics: Dict[str, Any] = {
            "total_requests": 0,
            "cache_hits": 0,
            "cli_runs": 0,
            "failures": 0,
            "avg_execution_time": 0.0,
            "last_execution_time": None,
            "last_request_id": None,
            "last_completed_request": None,
            "last_completed_source": None,
        }
        self._max_concurrency: int = int(os.getenv("F1_API_MAX_CONCURRENCY", "1"))

        print("[SERVICE] 簡化版分析服務已初始化")

    def _get_spec(self, function_id: Union[str, int, FunctionSpec]) -> FunctionSpec:
        """Return metadata for the requested function."""

        normalized_id = normalize_function_id(function_id)

        try:
            return get_function_spec(normalized_id)
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

        # ❌ 移除 Function 100 特殊處理：不再自動添加 start_year/end_year
        # 使用者需求：直接使用 -f 100 -y [year] -r [race] -s [session] 即可
        # 不需要強制添加 --start-year 和 --end-year 參數

        return prepared

    async def _check_standings_freshness(self, year: int) -> bool:
        """
        檢查積分榜數據新鮮度（Function 97 專用）
        
        直接調用 CLI 的智慧判斷邏輯來檢查數據是否過時
        
        Args:
            year: 賽季年份
            
        Returns:
            bool: True 表示數據過時需要刷新，False 表示數據還新鮮
        """
        try:
            # 導入 CLI 的新鮮度檢查功能
            from CLI_modules.cli.analyzer.championship_standings_analysis import check_standings_freshness
            
            print(f"[SERVICE] 🔍 檢查積分榜新鮮度 (year={year})...")
            
            # 在線程中執行同步的 CLI 函數
            freshness_result = await asyncio.to_thread(check_standings_freshness, year)
            
            # CLI 返回的鍵名是 "should_regenerate" (True=需要刷新)
            should_regenerate = freshness_result.get("should_regenerate", False)
            is_fresh = freshness_result.get("is_fresh", True)
            age_info = freshness_result.get("age_formatted", "未知")
            refresh_interval = freshness_result.get("refresh_interval_hours", "N/A")
            reason = freshness_result.get("reason", "")
            
            if should_regenerate:
                print(f"[SERVICE] ⚠️ 積分榜數據過時！")
                print(f"[SERVICE]    └─ 原因: {reason}")
                print(f"[SERVICE]    └─ 數據年齡: {age_info}")
                print(f"[SERVICE]    └─ 刷新間隔: {refresh_interval} 小時")
                print(f"[SERVICE]    └─ 將強制調用 CLI 刷新")
            else:
                print(f"[SERVICE] ✅ 積分榜數據還新鮮")
                print(f"[SERVICE]    └─ 原因: {reason}")
                print(f"[SERVICE]    └─ 數據年齡: {age_info}")
                print(f"[SERVICE]    └─ 刷新間隔: {refresh_interval} 小時")
            
            return should_regenerate
            
        except ImportError as e:
            print(f"[SERVICE] ⚠️ 無法導入 CLI 新鮮度檢查模組: {e}")
            print(f"[SERVICE]    └─ 降級為不強制刷新")
            return False
            
        except Exception as e:
            print(f"[SERVICE] ❌ 檢查新鮮度時發生錯誤: {e}")
            print(f"[SERVICE]    └─ 降級為不強制刷新")
            import traceback
            traceback.print_exc()
            return False

    async def _check_weather_freshness(self, year: int, event_name: str) -> bool:
        """
        檢查天氣預報數據新鮮度（Function 96 專用）
        
        調用 CLI 的天氣預報新鮮度檢查邏輯
        
        Args:
            year: 賽季年份
            event_name: 賽事名稱
            
        Returns:
            bool: True 表示數據過時需要刷新，False 表示數據還新鮮
        """
        try:
            # 導入 CLI 的新鮮度檢查功能
            from CLI_modules.cli.analyzer.race_weather_forecast import check_weather_forecast_freshness
            
            print(f"[SERVICE] 🔍 檢查天氣預報新鮮度 (year={year}, event={event_name})...")
            
            # 在線程中執行同步的 CLI 函數
            freshness_result = await asyncio.to_thread(
                check_weather_forecast_freshness, 
                year, 
                event_name
            )
            
            # CLI 返回的鍵名是 "should_regenerate" (True=需要刷新)
            should_regenerate = freshness_result.get("should_regenerate", False)
            is_fresh = freshness_result.get("is_fresh", True)
            age_info = freshness_result.get("age_formatted", "未知")
            refresh_interval = freshness_result.get("refresh_interval_hours", "N/A")
            reason = freshness_result.get("reason", "")
            
            if should_regenerate:
                print(f"[SERVICE] ⚠️ 天氣預報數據過時！")
                print(f"[SERVICE]    └─ 原因: {reason}")
                print(f"[SERVICE]    └─ 數據年齡: {age_info}")
                print(f"[SERVICE]    └─ 刷新間隔: {refresh_interval} 小時")
                print(f"[SERVICE]    └─ 將強制調用 CLI 刷新")
            else:
                print(f"[SERVICE] ✅ 天氣預報數據還新鮮")
                print(f"[SERVICE]    └─ 原因: {reason}")
                print(f"[SERVICE]    └─ 數據年齡: {age_info}")
                print(f"[SERVICE]    └─ 刷新間隔: {refresh_interval} 小時")
            
            return should_regenerate
            
        except ImportError as e:
            print(f"[SERVICE] ⚠️ 無法導入 CLI 天氣預報檢查模組: {e}")
            print(f"[SERVICE]    └─ 降級為不強制刷新")
            return False
            
        except Exception as e:
            print(f"[SERVICE] ❌ 檢查天氣預報新鮮度時發生錯誤: {e}")
            print(f"[SERVICE]    └─ 降級為不強制刷新")
            import traceback
            traceback.print_exc()
            return False
    
    async def _check_calendar_freshness(self) -> bool:
        """
        檢查 Season Calendar (Function 99) 數據的新鮮度
        
        Returns:
            True: 數據過時，需要強制刷新
            False: 數據新鮮，可以使用緩存
        """
        try:
            from CLI_modules.cli.analyzer.season_calendar_analysis import check_calendar_freshness
            
            # 在線程池中執行 CLI 的同步函數
            freshness_result = await asyncio.to_thread(
                check_calendar_freshness,
                all_years=True  # 檢查多年批量日曆
            )
            
            should_regenerate = freshness_result.get("should_regenerate", False)
            is_fresh = freshness_result.get("is_fresh", True)
            age_hours = freshness_result.get("age_hours")
            reason = freshness_result.get("reason", "未知")
            refresh_interval = freshness_result.get("refresh_interval_hours", 168)
            
            age_info = f"{age_hours:.1f} 小時" if age_hours is not None else "未知"
            
            if should_regenerate:
                print(f"[SERVICE] ⚠️ 賽季日曆數據過時！")
                print(f"[SERVICE]    └─ 原因: {reason}")
                print(f"[SERVICE]    └─ 數據年齡: {age_info}")
                print(f"[SERVICE]    └─ 刷新間隔: {refresh_interval} 小時")
                print(f"[SERVICE]    └─ 將強制調用 CLI 刷新")
            else:
                print(f"[SERVICE] ✅ 賽季日曆數據還新鮮")
                print(f"[SERVICE]    └─ 原因: {reason}")
                print(f"[SERVICE]    └─ 數據年齡: {age_info}")
                print(f"[SERVICE]    └─ 刷新間隔: {refresh_interval} 小時")
            
            return should_regenerate
            
        except ImportError as e:
            print(f"[SERVICE] ⚠️ 無法導入 CLI 賽季日曆檢查模組: {e}")
            print(f"[SERVICE]    └─ 降級為不強制刷新")
            return False
            
        except Exception as e:
            print(f"[SERVICE] ❌ 檢查賽季日曆新鮮度時發生錯誤: {e}")
            print(f"[SERVICE]    └─ 降級為不強制刷新")
            import traceback
            traceback.print_exc()
            return False

    def _build_cli_command(self, spec: FunctionSpec, params: Dict[str, Any]) -> list[str]:
        """Construct the CLI command for the given specification."""

        cmd = [
            "python",
            "f1_analysis_modular_main.py",
            "-f", str(spec.function_id)
        ]

        # 🔍 調試：顯示 Function 100 的參數
        if spec.function_id == "100":
            print(f"[SERVICE] 🔍 _build_cli_command for Function 100:")
            print(f"[SERVICE]    params = {params}")
            print(f"[SERVICE]    cli_flag_map = {spec.cli_flag_map}")

        for param_name, flag in spec.cli_flag_map.items():
            if param_name in params:
                value = params[param_name]
                if value in (None, ""):
                    continue
                
                # 處理布林旗標（action='store_true'）
                # 只有當值為 True 時才添加旗標，不帶參數值
                if isinstance(value, bool):
                    if value:
                        cmd.append(flag)
                else:
                    cmd.extend([flag, str(value)])

        # 🔍 調試：顯示 Function 100 的最終命令
        if spec.function_id == "100":
            print(f"[SERVICE] 🔍 CLI 命令: {' '.join(cmd)}")

        return cmd
    
    async def execute_analysis(self, function_id: Union[str, int], **params) -> Dict[str, Any]:
        """執行分析 - 支援非阻塞 CLI 呼叫與狀態追蹤"""

        request_id = self._generate_request_id()
        self._metrics["total_requests"] += 1
        self._metrics["last_request_id"] = request_id

        start_time = time.time()
        canonical_id: Optional[str] = None

        try:
            spec = self._get_spec(function_id)
            canonical_id = spec.function_id
            print(f"[SERVICE] 開始分析 {request_id}: 功能 {canonical_id}")
            prepared_params = self._prepare_params(spec, params)
            force_refresh = bool(params.get("force_refresh"))
            
            # 🔄 智慧刷新檢查：Function 97 (Championship Standings) 專用
            if canonical_id == "97" and not force_refresh:
                force_refresh = await self._check_standings_freshness(prepared_params.get("year"))
                if force_refresh:
                    print(f"[SERVICE] 🔄 積分榜數據過時，啟用強制刷新")
            
            # 🔄 智慧刷新檢查：Function 96 (Weather Forecast) 專用
            if canonical_id == "96" and not force_refresh:
                force_refresh = await self._check_weather_freshness(
                    prepared_params.get("year"),
                    prepared_params.get("race")
                )
                if force_refresh:
                    print(f"[SERVICE] 🔄 天氣預報數據過時，啟用強制刷新")
            
            # 🔄 智慧刷新檢查：Function 99 (Season Calendar) 專用
            if canonical_id == "99" and not force_refresh:
                force_refresh = await self._check_calendar_freshness()
                if force_refresh:
                    print(f"[SERVICE] 🔄 賽季日曆數據過時，啟用強制刷新")

            if not force_refresh:
                print("[SERVICE] 檢查緩存...")
                cached_result = await asyncio.to_thread(
                    self.cache_service.search_cached_analysis,
                    canonical_id,
                    **prepared_params,
                )

                if cached_result:
                    execution_time = time.time() - start_time
                    print(f"[SERVICE] ✅ 緩存命中! (耗時: {execution_time:.3f}s)")
                    self._metrics["cache_hits"] += 1
                    self._metrics["last_execution_time"] = execution_time
                    self._record_history(
                        request_id,
                        canonical_id,
                        execution_time,
                        success=True,
                        source="cache",
                        message="cache_hit",
                    )

                    return {
                        "success": True,
                        "message": f"分析完成 (功能 {canonical_id})",
                        "data": cached_result,
                        "source": "cache",
                        "execution_time": f"{execution_time:.3f}s",
                        "request_id": request_id,
                        "timestamp": datetime.now().isoformat(),
                        "function_spec": spec.__dict__,
                        "runtime": self.get_runtime_state(),
                    }

            task_info = self._start_active_task(request_id, canonical_id, prepared_params)
            cli_result = await self._run_cli_async(request_id, spec, prepared_params)

            execution_time = time.time() - start_time
            self._metrics["last_execution_time"] = execution_time

            if cli_result["success"]:
                self._metrics["cli_runs"] += 1
                self._update_average_execution(execution_time)

                # 等待 CLI 將結果寫入後重新讀取緩存
                await asyncio.sleep(0.5)
                refreshed_data = await asyncio.to_thread(
                    self.cache_service.search_cached_analysis,
                    canonical_id,
                    **prepared_params,
                )

                if refreshed_data:
                    print(f"[SERVICE] ✅ CLI 執行成功! (耗時: {execution_time:.3f}s)")
                    recorded = self._complete_active_task(
                        request_id,
                        status="completed",
                        message="cli_completed",
                        duration=execution_time,
                        cli_info=cli_result.get("cli_info", {}),
                        success=True,
                        source="cli",
                    )
                    if not recorded:
                        self._record_history(
                            request_id,
                            canonical_id,
                            execution_time,
                            success=True,
                            source="cli",
                            message="cli_completed",
                        )

                    return {
                        "success": True,
                        "message": f"分析完成 (功能 {canonical_id})",
                        "data": refreshed_data,
                        "source": "cli",
                        "execution_time": f"{execution_time:.3f}s",
                        "request_id": request_id,
                        "timestamp": datetime.now().isoformat(),
                        "function_spec": spec.__dict__,
                        "cli_info": cli_result.get("cli_info", {}),
                        "runtime": self.get_runtime_state(),
                    }

                error_msg = "CLI 執行成功但未找到輸出文件"
                recorded = self._complete_active_task(
                    request_id,
                    status="error",
                    message=error_msg,
                    duration=execution_time,
                    cli_info=cli_result.get("cli_info", {}),
                    success=False,
                    source="cli",
                )
                self._metrics["failures"] += 1
                if not recorded:
                    self._record_history(
                        request_id,
                        canonical_id,
                        execution_time,
                        success=False,
                        source="cli",
                        message=error_msg,
                    )

                return {
                    "success": False,
                    "message": "分析執行失敗",
                    "error": error_msg,
                    "source": "cli_no_output",
                    "execution_time": f"{execution_time:.3f}s",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat(),
                    "cli_info": cli_result.get("cli_info", {}),
                    "runtime": self.get_runtime_state(),
                }

            error_message = cli_result.get("error", "未知錯誤")
            recorded = self._complete_active_task(
                request_id,
                status="failed",
                message=error_message,
                duration=execution_time,
                cli_info=cli_result.get("cli_info", {}),
                success=False,
                source="cli",
            )
            self._metrics["failures"] += 1
            if not recorded:
                self._record_history(
                    request_id,
                    canonical_id,
                    execution_time,
                    success=False,
                    source="cli",
                    message=error_message,
                )

            print(f"[SERVICE] ❌ CLI 執行失敗! (耗時: {execution_time:.3f}s)")
            return {
                "success": False,
                "message": "分析執行失敗",
                "error": error_message,
                "source": "cli_failed",
                "execution_time": f"{execution_time:.3f}s",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "cli_info": cli_result.get("cli_info", {}),
                "runtime": self.get_runtime_state(),
            }

        except Exception as e:
            execution_time = time.time() - start_time
            self._metrics["failures"] += 1
            try:
                safe_function_id = canonical_id or normalize_function_id(function_id)
            except Exception:
                safe_function_id = str(function_id)
            recorded = self._complete_active_task(
                request_id,
                status="failed",
                message=str(e),
                duration=execution_time,
                cli_info=None,
                success=False,
                source="service_error",
            )
            if not recorded:
                self._record_history(
                    request_id,
                    safe_function_id,
                    execution_time,
                    success=False,
                    source="service_error",
                    message=str(e),
                )

            print(f"[SERVICE] ❌ 服務異常! (耗時: {execution_time:.3f}s): {e}")
            return {
                "success": False,
                "message": "服務執行異常",
                "error": str(e),
                "source": "service_error",
                "execution_time": f"{execution_time:.3f}s",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "runtime": self.get_runtime_state(),
            }

    async def _run_cli_async(
        self,
        request_id: str,
        spec: FunctionSpec,
        params: Dict[str, Any],
        timeout: float = 180.0,
    ) -> Dict[str, Any]:
        """以非阻塞方式執行 CLI 命令並追蹤進度"""

        cmd = self._build_cli_command(spec, params)
        print(f"[CLI] 執行命令: {' '.join(cmd)}")

        task_info = self._active_tasks.get(request_id)
        if task_info:
            self._update_active_task(
                request_id,
                status="starting",
                progress=0.15,
                message="排程 CLI 任務",
                command=" ".join(cmd),
            )

        start_time = time.time()
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        try:
            process = await aio_subprocess.create_subprocess_exec(
                *cmd,
                cwd=os.getcwd(),
                stdout=aio_subprocess.PIPE,
                stderr=aio_subprocess.PIPE,
            )

            self._update_active_task(
                request_id,
                status="running",
                progress=0.25,
                message="CLI 進程啟動",
                pid=process.pid,
            )

            async def _read_stream(stream, accumulator, stream_name: str) -> None:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    text = line.decode("utf-8", errors="replace").rstrip()
                    accumulator.append(text)
                    truncated = text[-160:]
                    current_progress = self._active_tasks.get(request_id, {}).get("progress", 0.0)
                    self._update_active_task(
                        request_id,
                        progress=min(current_progress + 0.05, 0.85),
                        last_log=truncated,
                        message=f"{stream_name}: {truncated}",
                    )

            readers = []
            if process.stdout is not None:
                readers.append(asyncio.create_task(_read_stream(process.stdout, stdout_lines, "stdout")))
            if process.stderr is not None:
                readers.append(asyncio.create_task(_read_stream(process.stderr, stderr_lines, "stderr")))

            try:
                await asyncio.wait_for(process.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                for reader in readers:
                    reader.cancel()
                self._update_active_task(
                    request_id,
                    status="timeout",
                    progress=0.95,
                    message=f"CLI 執行超時 (>{int(timeout)}s)",
                )

                return {
                    "success": False,
                    "error": f"CLI 執行超時 (>{int(timeout)}秒)",
                    "cli_info": {
                        "command": " ".join(cmd),
                        "timeout": True,
                        "duration_seconds": time.time() - start_time,
                        "stdout_preview": self._truncate_output("\n".join(stdout_lines)),
                        "stderr_preview": self._truncate_output("\n".join(stderr_lines)),
                    },
                }

            await asyncio.gather(*readers, return_exceptions=True)

            duration = time.time() - start_time
            exit_code = process.returncode
            stdout_text = "\n".join(stdout_lines)
            stderr_text = "\n".join(stderr_lines)

            cli_info = {
                "command": " ".join(cmd),
                "duration_seconds": duration,
                "returncode": exit_code,
                "stdout_preview": self._truncate_output(stdout_text),
                "stderr_preview": self._truncate_output(stderr_text),
                "pid": process.pid,
            }

            if exit_code == 0:
                self._update_active_task(
                    request_id,
                    status="post_processing",
                    progress=0.9,
                    message="CLI 完成，等待輸出檔案",
                    cli_info=cli_info,
                )

                return {
                    "success": True,
                    "cli_info": cli_info,
                }

            self._update_active_task(
                request_id,
                status="failed",
                progress=0.95,
                message=f"CLI 失敗 (返回碼 {exit_code})",
                cli_info=cli_info,
            )

            return {
                "success": False,
                "error": f"CLI 執行失敗 (返回碼: {exit_code})",
                "cli_info": cli_info,
            }

        except FileNotFoundError as e:
            error_message = f"無法找到 CLI 執行檔: {e}"
            self._update_active_task(
                request_id,
                status="failed",
                progress=0.95,
                message=error_message,
            )
            return {
                "success": False,
                "error": error_message,
                "cli_info": {"command": " ".join(cmd)},
            }
        except Exception as e:
            self._update_active_task(
                request_id,
                status="failed",
                progress=0.95,
                message=str(e),
            )
            return {
                "success": False,
                "error": f"CLI 執行異常: {str(e)}",
                "cli_info": {"command": " ".join(cmd)},
            }

    def _start_active_task(self, request_id: str, function_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        now = time.time()
        task_info = {
            "request_id": request_id,
            "function_id": function_id,
            "params": params.copy(),
            "status": "queued",
            "progress": 0.1,
            "message": "等待 CLI 執行",
            "started_at": now,
            "started_at_iso": datetime.fromtimestamp(now).isoformat(),
            "updated_at": now,
            "last_log": None,
            "pid": None,
            "cli_info": None,
        }

        self._active_tasks[request_id] = task_info
        return task_info

    def _update_active_task(self, request_id: str, **updates: Any) -> None:
        task_info = self._active_tasks.get(request_id)
        if not task_info:
            return

        task_info.update({k: v for k, v in updates.items() if v is not None})
        task_info["updated_at"] = time.time()

    def _complete_active_task(
        self,
        request_id: str,
        status: str,
        message: str,
        duration: float,
        cli_info: Optional[Dict[str, Any]],
        success: bool = False,
        source: str = "cli",
    ) -> bool:
        task_info = self._active_tasks.pop(request_id, None)
        finished_at = datetime.now().isoformat()

        if task_info:
            task_info.update(
                {
                    "status": status,
                    "progress": 1.0 if success else task_info.get("progress", 1.0),
                    "message": message,
                    "duration_seconds": duration,
                    "completed_at": finished_at,
                    "cli_info": cli_info,
                }
            )

            history_entry = {
                "request_id": request_id,
                "function_id": task_info.get("function_id"),
                "completed_at": finished_at,
                "duration_seconds": round(duration, 3),
                "success": success,
                "status": status,
                "message": message,
                "source": source,
            }
            self._recent_history.append(history_entry)
            self._metrics["last_completed_request"] = request_id
            self._metrics["last_completed_source"] = source
            return True

        return False

    def _record_history(
        self,
        request_id: str,
    function_id: str,
        duration: float,
        success: bool,
        source: str,
        message: str,
    ) -> None:
        entry = {
            "request_id": request_id,
            "function_id": function_id,
            "completed_at": datetime.now().isoformat(),
            "duration_seconds": round(duration, 3),
            "success": success,
            "source": source,
            "message": message,
        }
        self._recent_history.append(entry)
        self._metrics["last_completed_request"] = request_id
        self._metrics["last_completed_source"] = source

    def _truncate_output(self, text: str, limit: int = 2000) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."

    def _update_average_execution(self, duration: float) -> None:
        current_avg = self._metrics.get("avg_execution_time") or 0.0
        if current_avg <= 0:
            self._metrics["avg_execution_time"] = duration
        else:
            # 指數移動平均
            alpha = 0.3
            self._metrics["avg_execution_time"] = current_avg * (1 - alpha) + duration * alpha

    def _generate_request_id(self) -> str:
        return f"req_{uuid4().hex[:10]}"

    def get_runtime_state(self) -> Dict[str, Any]:
        now = time.time()
        active_list = []
        for task in self._active_tasks.values():
            active_list.append(
                {
                    "request_id": task["request_id"],
                    "function_id": task["function_id"],
                    "status": task["status"],
                    "progress": round(task.get("progress", 0.0), 3),
                    "message": task.get("message"),
                    "started_at": task.get("started_at_iso"),
                    "elapsed_seconds": round(now - task.get("started_at", now), 3),
                    "last_log": task.get("last_log"),
                    "pid": task.get("pid"),
                }
            )

        queue_length = max(len(active_list) - self._max_concurrency, 0)
        avg_exec = self._metrics.get("avg_execution_time") or 0.0
        estimated_completion = None
        if avg_exec > 0 and active_list:
            estimated_completion = round(avg_exec * len(active_list), 2)

        total_requests = self._metrics["total_requests"]
        cache_hits = self._metrics["cache_hits"]
        cache_hit_rate = round(cache_hits / total_requests, 3) if total_requests else None

        return {
            "busy": bool(active_list),
            "active_task_count": len(active_list),
            "queue_length": queue_length,
            "estimated_completion_seconds": estimated_completion,
            "max_concurrency": self._max_concurrency,
            "active_tasks": active_list,
            "metrics": {
                "total_requests": total_requests,
                "cache_hits": cache_hits,
                "cache_hit_rate": cache_hit_rate,
                "cli_runs": self._metrics["cli_runs"],
                "failures": self._metrics["failures"],
                "avg_execution_seconds": round(avg_exec, 3) if avg_exec else None,
                "last_execution_seconds": round(self._metrics["last_execution_time"], 3)
                if self._metrics["last_execution_time"]
                else None,
                "last_request_id": self._metrics["last_request_id"],
                "last_completed_request": self._metrics["last_completed_request"],
                "last_completed_source": self._metrics["last_completed_source"],
            },
            "recent_history": list(self._recent_history),
        }
    
    async def get_cache_status(self) -> Dict[str, Any]:
        """獲取緩存狀態 - 簡化版"""
        try:
            print("[SERVICE] 獲取緩存狀態...")
            stats = await asyncio.to_thread(self.cache_service.get_cache_statistics)
            
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
                "timestamp": datetime.now().isoformat(),
                "runtime": self.get_runtime_state(),
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": "緩存狀態獲取失敗",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "runtime": self.get_runtime_state(),
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
            runtime_state = self.get_runtime_state()
            
            return {
                "success": True,
                "status": "busy" if runtime_state.get("busy") else ("healthy" if cache_healthy else "degraded"),
                "message": "服務運行正常" if not runtime_state.get("busy") else "服務繁忙，背景執行中",
                "checks": {
                    "cache_service": "healthy" if cache_healthy else "error",
                    "python_version": python_version,
                    "working_directory": current_dir,
                    "cli_file_exists": os.path.exists("f1_analysis_modular_main.py")
                },
                "runtime": runtime_state,
                "timestamp": datetime.now().isoformat(),
            }
        
        except Exception as e:
            return {
                "success": False,
                "status": "unhealthy", 
                "message": "健康檢查失敗",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "runtime": self.get_runtime_state(),
            }
