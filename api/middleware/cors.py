#!/usr/bin/env python3
"""
F1 Analysis API - CORS 中間件
處理跨域請求

版本: 2.0 (重構版)
作者: F1 Analysis Team
"""

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import json


class CORSConfigMiddleware:
    """CORS 配置中間件工廠"""
    
    @staticmethod
    def create_cors_middleware():
        """創建 CORS 中間件配置"""
        return CORSMiddleware(
            allow_origins=[
                "http://localhost:3000",  # React 開發服務器
                "http://localhost:8080",  # Vue 開發服務器
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
                "http://localhost:5000",  # 其他前端框架
                "http://127.0.0.1:5000"
            ],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=[
                "Content-Type",
                "Authorization",
                "X-Requested-With",
                "Accept",
                "Origin",
                "X-Request-ID"
            ],
            expose_headers=[
                "X-Process-Time",
                "X-Request-ID",
                "X-Total-Count"
            ]
        )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全標頭中間件"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """添加安全標頭"""
        
        response = await call_next(request)
        
        # 添加安全標頭
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # API 識別標頭
        response.headers["X-API-Name"] = "F1-Analysis-API"
        response.headers["X-API-Version"] = "2.0.0"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """簡單的速率限制中間件"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.request_times = {}  # IP -> [timestamp, ...]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """檢查請求速率"""
        
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # 清理舊記錄 (超過1分鐘)
        if client_ip in self.request_times:
            self.request_times[client_ip] = [
                t for t in self.request_times[client_ip]
                if current_time - t < 60
            ]
        else:
            self.request_times[client_ip] = []
        
        # 檢查請求數量
        if len(self.request_times[client_ip]) >= self.calls_per_minute:
            return Response(
                content=json.dumps({
                    "error": "Rate limit exceeded",
                    "message": f"最多每分鐘 {self.calls_per_minute} 次請求",
                    "retry_after": 60
                }),
                status_code=429,
                headers={"Content-Type": "application/json"}
            )
        
        # 記錄請求時間
        self.request_times[client_ip].append(current_time)
        
        # 繼續處理請求
        response = await call_next(request)
        
        # 添加速率限制標頭
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.calls_per_minute - len(self.request_times[client_ip])
        )
        
        return response
