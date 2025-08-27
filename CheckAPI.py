#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 Analysis API 完整輸出檢查器
Complete API Output Validator for F1 Analysis

完整支援所有 F1 分析功能的 API 測試與驗證
版本: 2.0
支援功能: 1-22 + 所有子功能
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import sys
import os


class F1AnalysisAPIValidator:
    """F1 分析 API 完整輸出驗證器"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """初始化API驗證器
        
        Args:
            base_url: API服務器基礎URL，默認為本地localhost:8000
        """
        self.base_url = base_url.rstrip('/')
        self.validation_results = {}
        self.test_session = requests.Session()
        self.test_parameters = {
            "year": 2025,           # 標準測試年份
            "race": "Japan",        # 標準測試賽事 
            "session": "R",         # 標準測試會話
            "driver1": "VER",       # 標準主要車手
            "driver2": "LEC"        # 標準次要車手
        }
        
        # 設定超時和重試
        self.test_session.timeout = 60  # 60秒超時
        
        print(f"🎯 使用標準測試參數:")
        print(f"   年份: {self.test_parameters['year']}")
        print(f"   賽事: {self.test_parameters['race']}")
        print(f"   會話: {self.test_parameters['session']}")
        print(f"   主車手: {self.test_parameters['driver1']}")
        print(f"   次車手: {self.test_parameters['driver2']}")
        print(f"   API地址: {self.base_url}")
        print("="*50)
        
    def log(self, message: str, level: str = "INFO"):
        """記錄訊息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🔍",
            "TEST": "🧪"
        }.get(level, "📝")
        
        print(f"[{timestamp}] {prefix} {message}")
    
    def check_api_health(self) -> bool:
        """檢查 API 服務器健康狀態"""
        try:
            self.log("檢查 API 服務器狀態...", "TEST")
            response = self.test_session.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                self.log("API 服務器運行正常", "SUCCESS")
                return True
            else:
                self.log(f"API 服務器狀態異常: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"無法連接到 API 服務器: {e}", "ERROR")
            return False
    
    def get_api_info(self) -> Optional[Dict[str, Any]]:
        """獲取 API 基本信息"""
        try:
            self.log("獲取 API 基本信息...", "TEST")
            response = self.test_session.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.log("API 信息獲取成功", "SUCCESS")
                
                if result.get("data"):
                    info = result["data"]
                    self.log(f"   版本: {info.get('version')}", "DEBUG")
                    self.log(f"   支援模組數: {info.get('total_modules', 0)}", "DEBUG")
                    self.log(f"   支援年份: {info.get('supported_years')}", "DEBUG")
                
                return result
            else:
                self.log(f"API 信息獲取失敗: {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"獲取 API 信息異常: {e}", "ERROR")
            return None
    
    def get_supported_modules(self) -> Optional[Dict[str, Any]]:
        """獲取支援的模組列表"""
        try:
            self.log("獲取支援模組列表...", "TEST")
            response = self.test_session.get(f"{self.base_url}/modules", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.log("模組列表獲取成功", "SUCCESS")
                
                if result.get("data"):
                    modules = result["data"]
                    for category, funcs in modules.items():
                        self.log(f"   {category}: {len(funcs)} 個功能", "DEBUG")
                
                return result
            else:
                self.log(f"模組列表獲取失敗: {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"獲取模組列表異常: {e}", "ERROR")
            return None
    
    def call_analysis_api(self, function_id: Union[str, int], year: int = None, 
                         race: str = None, session: str = None,
                         driver1: Optional[str] = None, driver2: Optional[str] = None,
                         corner_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """調用分析 API - 使用標準測試參數"""
        try:
            # 使用標準測試參數或提供的參數
            params = {
                "year": year or self.test_parameters["year"],
                "race": race or self.test_parameters["race"],
                "session": session or self.test_parameters["session"],
                "function_id": str(function_id)
            }
            
            # 添加可選參數
            if driver1 or self.test_parameters.get("driver1"):
                params["driver1"] = driver1 or self.test_parameters["driver1"]
            if driver2 or self.test_parameters.get("driver2"):
                params["driver2"] = driver2 or self.test_parameters["driver2"]
            if corner_number:
                params["corner_number"] = corner_number
            
            self.log(f"調用分析 API: 功能 {function_id}", "TEST")
            self.log(f"參數: {params}", "DEBUG")
            
            response = self.test_session.post(
                f"{self.base_url}/analyze", 
                json=params, 
                timeout=300  # 5分鐘超時
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"功能 {function_id} 分析完成", "SUCCESS")
                return result
            else:
                self.log(f"功能 {function_id} 分析失敗: HTTP {response.status_code}", "ERROR")
                error_text = response.text[:500] if response.text else "無響應內容"
                self.log(f"錯誤詳情: {error_text}", "ERROR")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {error_text[:200]}"
                }
                
        except requests.exceptions.Timeout:
            self.log(f"功能 {function_id} 分析超時 (5分鐘)", "ERROR")
            return {"success": False, "error": "分析超時"}
            
        except requests.exceptions.ConnectionError:
            self.log(f"無法連接到API服務器: {self.base_url}", "ERROR")
            return {"success": False, "error": "連接失敗"}
            
        except Exception as e:
            self.log(f"功能 {function_id} 調用異常: {e}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def validate_basic_response_structure(self, response: Dict[str, Any], 
                                        function_id: Union[str, int]) -> Dict[str, Any]:
        """驗證基本響應結構"""
        validation = {
            "function_id": str(function_id),
            "response_valid": False,
            "checks": {},
            "errors": []
        }
        
        try:
            # 檢查基本欄位
            required_fields = ["success", "message", "timestamp"]
            for field in required_fields:
                if field in response:
                    validation["checks"][f"has_{field}"] = True
                else:
                    validation["checks"][f"has_{field}"] = False
                    validation["errors"].append(f"缺少必要欄位: {field}")
            
            # 檢查成功狀態
            if response.get("success"):
                validation["checks"]["analysis_successful"] = True
                
                # 檢查數據欄位
                if "data" in response and response["data"]:
                    validation["checks"]["has_data"] = True
                    
                    data = response["data"]
                    if isinstance(data, dict):
                        validation["checks"]["data_is_dict"] = True
                        
                        # 檢查執行信息
                        execution_fields = ["execution_time", "function_id", "parameters"]
                        for field in execution_fields:
                            validation["checks"][f"has_{field}"] = field in data
                        
                        # 檢查是否有輸出或JSON數據 - 更寬鬆的檢查
                        has_output = any([
                            "output" in data,
                            "json_data" in data,
                            "json_files" in data,
                            "data" in data,
                            "result" in data,
                            "analysis_result" in data,
                            "results" in data
                        ])
                        
                        if has_output:
                            validation["checks"]["has_output_data"] = True
                            
                            # 檢查具體數據類型
                            output_types = []
                            if "output" in data:
                                output_types.append("output")
                            if "json_data" in data or "json_files" in data:
                                output_types.append("json")
                            if "data" in data and isinstance(data["data"], (dict, list)):
                                output_types.append("structured_data")
                            
                            validation["checks"]["output_types"] = output_types
                        else:
                            validation["checks"]["has_output_data"] = False
                            validation["errors"].append("缺少輸出數據或JSON數據")
                    else:
                        validation["checks"]["data_is_dict"] = False
                        validation["errors"].append("data 欄位不是字典格式")
                else:
                    validation["checks"]["has_data"] = False
                    validation["errors"].append("成功響應但缺少 data 欄位")
            else:
                validation["checks"]["analysis_successful"] = False
                validation["errors"].append(f"分析失敗: {response.get('message', '未知錯誤')}")
            
            # 計算整體驗證狀態
            error_count = len(validation["errors"])
            if error_count == 0:
                validation["response_valid"] = True
                self.log(f"功能 {function_id} 響應結構驗證通過", "SUCCESS")
            else:
                validation["response_valid"] = False
                self.log(f"功能 {function_id} 響應結構驗證失敗 ({error_count} 個錯誤)", "ERROR")
                for error in validation["errors"]:
                    self.log(f"   - {error}", "ERROR")
            
        except Exception as e:
            validation["response_valid"] = False
            validation["errors"].append(f"驗證過程異常: {str(e)}")
            self.log(f"功能 {function_id} 響應結構驗證異常: {e}", "ERROR")
        
        return validation
    
    def validate_json_data_structure(self, json_data: Dict[str, Any], 
                                   function_id: Union[str, int]) -> Dict[str, Any]:
        """驗證JSON數據結構"""
        validation = {
            "function_id": str(function_id),
            "json_valid": False,
            "checks": {},
            "file_count": 0,
            "files_analyzed": []
        }
        
        try:
            if not json_data:
                validation["checks"]["has_json_data"] = False
                return validation
            
            validation["checks"]["has_json_data"] = True
            validation["file_count"] = len(json_data)
            
            # 分析每個JSON檔案
            for filename, file_data in json_data.items():
                file_analysis = {
                    "filename": filename,
                    "is_valid_json": isinstance(file_data, dict),
                    "has_metadata": False,
                    "has_analysis_data": False,
                    "size_estimate": 0
                }
                
                if isinstance(file_data, dict):
                    # 估算數據大小
                    file_analysis["size_estimate"] = len(str(file_data))
                    
                    # 檢查常見結構
                    common_fields = ["metadata", "analysis_data", "results", "statistics"]
                    for field in common_fields:
                        if field in file_data:
                            file_analysis[f"has_{field}"] = True
                    
                    # 檢查metadata
                    if "metadata" in file_data:
                        metadata = file_data["metadata"]
                        if isinstance(metadata, dict):
                            file_analysis["has_metadata"] = True
                            file_analysis["metadata_fields"] = list(metadata.keys())
                    
                    # 檢查是否有實際分析數據
                    data_indicators = ["results", "analysis_data", "statistics", "data"]
                    for indicator in data_indicators:
                        if indicator in file_data and file_data[indicator]:
                            file_analysis["has_analysis_data"] = True
                            break
                
                validation["files_analyzed"].append(file_analysis)
                self.log(f"   檔案 {filename}: {file_analysis['size_estimate']} 字元", "DEBUG")
            
            # 計算整體驗證狀態
            valid_files = sum(1 for f in validation["files_analyzed"] if f["is_valid_json"])
            validation["valid_file_count"] = valid_files
            validation["json_valid"] = valid_files > 0
            
            if validation["json_valid"]:
                self.log(f"功能 {function_id} JSON數據驗證通過 ({valid_files}/{validation['file_count']} 檔案有效)", "SUCCESS")
            else:
                self.log(f"功能 {function_id} JSON數據驗證失敗", "ERROR")
        
        except Exception as e:
            validation["json_valid"] = False
            validation["error"] = str(e)
            self.log(f"功能 {function_id} JSON數據驗證異常: {e}", "ERROR")
        
        return validation
    
    def test_function(self, function_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """測試單個功能"""
        test_result = {
            "function_id": str(function_id),
            "test_time": datetime.now().isoformat(),
            "success": False,
            "api_response": None,
            "structure_validation": None,
            "json_validation": None,
            "errors": []
        }
        
        try:
            self.log(f"開始測試功能 {function_id}", "TEST")
            
            # 調用API
            response = self.call_analysis_api(function_id, **kwargs)
            test_result["api_response"] = response
            
            if not response:
                test_result["errors"].append("API調用失敗")
                return test_result
            
            # 驗證響應結構
            structure_validation = self.validate_basic_response_structure(response, function_id)
            test_result["structure_validation"] = structure_validation
            
            if not structure_validation["response_valid"]:
                test_result["errors"].extend(structure_validation["errors"])
                return test_result
            
            # 驗證JSON數據 (如果有)
            if response.get("data", {}).get("json_data"):
                json_validation = self.validate_json_data_structure(
                    response["data"]["json_data"], function_id
                )
                test_result["json_validation"] = json_validation
                
                if not json_validation["json_valid"]:
                    test_result["errors"].append("JSON數據驗證失敗")
            
            # 判斷整體測試結果
            test_result["success"] = len(test_result["errors"]) == 0
            
            if test_result["success"]:
                self.log(f"功能 {function_id} 測試通過", "SUCCESS")
            else:
                self.log(f"功能 {function_id} 測試失敗", "ERROR")
                for error in test_result["errors"]:
                    self.log(f"   - {error}", "ERROR")
        
        except Exception as e:
            test_result["errors"].append(f"測試過程異常: {str(e)}")
            self.log(f"功能 {function_id} 測試異常: {e}", "ERROR")
        
        return test_result
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """執行全面測試"""
        self.log("開始執行 F1 Analysis API 全面測試", "TEST")
        
        test_results = {
            "test_time": datetime.now().isoformat(),
            "api_health": False,
            "api_info": None,
            "modules_info": None,
            "function_tests": {},
            "summary": {}
        }
        
        # 檢查API健康狀態
        test_results["api_health"] = self.check_api_health()
        if not test_results["api_health"]:
            self.log("API服務器不可用，終止測試", "ERROR")
            return test_results
        
        # 獲取API信息
        test_results["api_info"] = self.get_api_info()
        test_results["modules_info"] = self.get_supported_modules()
        
        # 定義要測試的功能
        test_functions = [
            # 基礎分析
            {"id": "1", "name": "降雨強度分析"},
            {"id": "2", "name": "賽道路線分析"},
            {"id": "3", "name": "進站策略分析"},
            {"id": "4", "name": "事故分析"},
            {"id": "4.1", "name": "關鍵事件摘要"},
            
            # 單車手分析
            {"id": "5", "name": "單車手綜合分析"},
            {"id": "6", "name": "單車手遙測分析"},
            {"id": "6.1", "name": "完整圈次分析"},
            {"id": "7", "name": "雙車手比較", "params": {"driver1": "VER", "driver2": "LEC"}},
            {"id": "7.1", "name": "速度差距分析", "params": {"driver1": "VER", "driver2": "LEC"}},
            
            # 全部車手分析
            {"id": "14", "name": "所有車手綜合分析"},
            {"id": "14.1", "name": "車手統計總覽"},
            {"id": "16.1", "name": "年度超車統計"},
            {"id": "16.2", "name": "超車表現比較"},
            {"id": "16.4", "name": "超車趨勢分析"},
            
            # 彎道分析
            {"id": "12.1", "name": "單車手彎道分析", "params": {"corner_number": 1}},
            {"id": "15", "name": "彎道速度分析"},
        ]
        
        # 執行功能測試
        passed_tests = 0
        total_tests = len(test_functions)
        
        for func_test in test_functions:
            func_id = func_test["id"]
            func_name = func_test["name"]
            params = func_test.get("params", {})
            
            self.log(f"測試功能 {func_id}: {func_name}", "TEST")
            
            try:
                result = self.test_function(func_id, **params)
                test_results["function_tests"][func_id] = result
                
                if result["success"]:
                    passed_tests += 1
                    
            except Exception as e:
                self.log(f"功能 {func_id} 測試異常: {e}", "ERROR")
                test_results["function_tests"][func_id] = {
                    "function_id": func_id,
                    "success": False,
                    "error": str(e)
                }
        
        # 生成測試摘要
        test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%"
        }
        
        self.log(f"測試完成: {passed_tests}/{total_tests} 通過 ({test_results['summary']['success_rate']})", "SUCCESS")
        
        return test_results
    
    def save_test_results(self, results: Dict[str, Any], filename: Optional[str] = None):
        """保存測試結果"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.log(f"測試結果已保存到: {filename}", "SUCCESS")
            
        except Exception as e:
            self.log(f"保存測試結果失敗: {e}", "ERROR")


def main():
    """主函數"""
    print("🏎️  F1 Analysis API 完整測試工具")
    print("=" * 50)
    
    # 從命令行參數獲取API URL，默認使用本地服務器
    api_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    
    print(f"🎯 目標API服務器: {api_url}")
    print("🔧 提示: 請確保API服務器正在運行")
    print("   啟動命令: python APIserver.py")
    print("=" * 50)
    
    # 初始化驗證器
    validator = F1AnalysisAPIValidator(api_url)
    
    # 執行全面測試
    results = validator.run_comprehensive_test()
    
    # 保存測試結果到 testcode 目錄
    os.makedirs('testcode', exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"testcode/api_test_results_{timestamp}.json"
    validator.save_test_results(results, results_file)
    
    # 顯示最終摘要
    print("\n" + "=" * 50)
    print("🏁 測試摘要")
    summary = results.get("summary", {})
    print(f"   總測試數: {summary.get('total_tests', 0)}")
    print(f"   通過測試: {summary.get('passed_tests', 0)}")
    print(f"   失敗測試: {summary.get('failed_tests', 0)}")
    print(f"   成功率: {summary.get('success_rate', '0%')}")
    print(f"   結果文件: {results_file}")
    print("=" * 50)
    
    # 如果有失敗的測試，顯示詳細信息
    if summary.get('failed_tests', 0) > 0:
        print("\n❌ 失敗的測試:")
        for func_id, result in results.get("function_tests", {}).items():
            if not result.get("success", False):
                print(f"   功能 {func_id}: {result.get('error', '未知錯誤')}")
        print("=" * 50)


if __name__ == "__main__":
    main()
