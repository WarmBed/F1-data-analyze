#!/usr/bin/env python3
"""
F1 Analysis API - 日誌中間件
記錄所有 API 請求和響應

版本: 2.0 (重構版)
作者: F1 Analysis Team
"""

import time
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging


class LoggingMiddleware(BaseHTTPMiddleware):
    """日誌記錄中間件"""
    
    def __init__(self, app, logger_name: str = "f1_api"):
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)
        
        # 配置日誌格式
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求和響應日誌"""
        
        # 記錄請求開始時間
        start_time = time.time()
        
        # 提取請求信息
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 記錄請求
        self.logger.info(
            f"🔵 REQUEST: {method} {url} | IP: {client_ip} | UA: {user_agent[:50]}"
        )
        
        try:
            # 執行請求
            response = await call_next(request)
            
            # 計算處理時間
            process_time = time.time() - start_time
            
            # 記錄響應
            self.logger.info(
                f"🟢 RESPONSE: {response.status_code} | "
                f"Time: {process_time:.3f}s | "
                f"Size: {response.headers.get('content-length', 'unknown')} bytes"
            )
            
            # 添加響應標頭
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = f"req_{int(start_time * 1000)}"
            
            return response
            
        except Exception as e:
            # 記錄錯誤
            process_time = time.time() - start_time
            self.logger.error(
                f"🔴 ERROR: {method} {url} | "
                f"Error: {str(e)} | "
                f"Time: {process_time:.3f}s"
            )
            raise
