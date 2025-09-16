#!/usr/bin/env python3
"""
F1 Analysis API 中間件模組
提供錯誤處理、日誌記錄、CORS 等中間件功能

版本: 2.0 (重構版)
作者: F1 Analysis Team
"""

from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.base import BaseHTTPMiddleware
import time
import json
import traceback
from typing import Callable


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """統一錯誤處理中間件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求並統一錯誤格式"""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # 添加處理時間頭
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-API-Version"] = "2.0.0"
            
            return response
            
        except HTTPException as http_exc:
            # HTTP 異常 - 已經格式化
            process_time = time.time() - start_time
            
            error_response = {
                "success": False,
                "error": {
                    "type": "http_error",
                    "status_code": http_exc.status_code,
                    "message": http_exc.detail,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "process_time": f"{process_time:.3f}s"
                }
            }
            
            return Response(
                content=json.dumps(error_response, ensure_ascii=False),
                status_code=http_exc.status_code,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "X-Process-Time": str(process_time),
                    "X-API-Version": "2.0.0"
                }
            )
            
        except Exception as exc:
            # 未預期的異常
            process_time = time.time() - start_time
            
            # 記錄詳細錯誤 (開發環境)
            error_details = {
                "type": str(type(exc).__name__),
                "message": str(exc),
                "traceback": traceback.format_exc()
            }
            
            print(f"[ERROR] 未處理的異常: {error_details}")
            
            error_response = {
                "success": False,
                "error": {
                    "type": "internal_error",
                    "status_code": 500,
                    "message": "內部服務器錯誤",
                    "details": str(exc),  # 生產環境中可能需要隱藏
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "process_time": f"{process_time:.3f}s"
                }
            }
            
            return Response(
                content=json.dumps(error_response, ensure_ascii=False),
                status_code=500,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "X-Process-Time": str(process_time),
                    "X-API-Version": "2.0.0"
                }
            )


class LoggingMiddleware(BaseHTTPMiddleware):
    """請求日誌記錄中間件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """記錄請求和響應信息"""
        start_time = time.time()
        
        # 記錄請求
        print(f"[REQUEST] {request.method} {request.url.path}")
        if request.query_params:
            print(f"[QUERY] {dict(request.query_params)}")
        
        response = await call_next(request)
        
        # 記錄響應
        process_time = time.time() - start_time
        print(f"[RESPONSE] {response.status_code} - {process_time:.3f}s")
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全頭中間件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """添加安全相關的 HTTP 頭"""
        response = await call_next(request)
        
        # 添加安全頭
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


def setup_cors_middleware(app):
    """設置 CORS 中間件"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # React 開發服務器
            "http://localhost:8080",  # Vue 開發服務器
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            "http://localhost:5173",  # Vite 開發服務器
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )


def setup_custom_middleware(app):
    """設置自定義中間件"""
    # 添加中間件 (注意順序：最後添加的最先執行)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware) 
    app.add_middleware(SecurityHeadersMiddleware)
