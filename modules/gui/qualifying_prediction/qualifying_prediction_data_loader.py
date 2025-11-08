#!/usr/bin/env python3
"""
排位賽預測資料載入器
Qualifying Prediction Data Loader

負責載入和轉換 CLI Function 74 輸出的排位賽預測資料
遵循 API-ONLY 模式，優先使用 API，備援使用本地 JSON

作者: F1T Team
日期: 2025-11-05
版本: 1.0.0
"""

from modules.gui.base.universal_data_loader_base import UniversalDataLoader
from core.gui_i18n import tr
from typing import Dict, Any, Optional, List


class QualifyingPredictionDataLoader(UniversalDataLoader):
    """
    排位賽預測資料載入器
    
    繼承自 UniversalDataLoader，實作排位賽預測資料的載入、驗證和轉換
    
    資料來源：
    - API: refactored_api.py (function_id=74)
    - 本地 JSON: json/qualifying_prediction_{year}_{race}.json
    
    資料結構：
    {
        "metadata": {
            "track": str,
            "year": int,
            "model_version": "v3.8",
            "model_r2": float,  # 模型整體 R²（所有車手共用）
            "model_mae": float,  # 模型整體 MAE
            "sample_count": int,
            "prediction_time": str
        },
        "predictions": [
            {
                "rank": int,
                "driver": str,
                "team": str,
                "fp3_time": float,
                "predicted_time": float,
                "actual_q_time": float | None,
                "improvement": float  # predicted - fp3
            }
        ]
    }
    """
    
    # CLI 功能編號
    CLI_FUNCTION = 74  # ✅ 修正：F74 = 排位賽預測生成器
    
    # JSON 檔案命名模式
    JSON_PATTERN = "qualifying_prediction_{year}_{race}.json"
    
    # 分析類型標識
    ANALYSIS_TYPE = "qualifying_prediction"
    
    def __init__(self, year: str, race: str, parent=None):
        """
        初始化資料載入器
        
        Args:
            year: 賽季年份 (例如: "2025")
            race: 賽事名稱 (例如: "Japan", "Austria")
            parent: 父元件 (用於信號連接)
        """
        # 調用基類 __init__ (只需要 analysis_type 和 parent)
        super().__init__(analysis_type=self.ANALYSIS_TYPE, parent=parent)
        
        self.year = str(year)
        self.race = race

        # API-ONLY 模式：停用本地 JSON 後備
        self._allow_local_fallback = False
        self._debug("[QUALIFYING_PRED_LOADER] 已停用本地 JSON 後備 (API-ONLY)")
        
        self._debug(f"[QUALIFYING_PRED_LOADER] 初始化完成: {year} {race}")
    
    def _validate_data_format(self, data: Any) -> bool:
        """
        驗證資料格式是否符合預期
        
        檢查項目：
        1. 資料必須是字典
        2. 必須包含 "metadata" 和 "predictions" 鍵
        3. metadata 必須包含必要的模型指標（model_r2, model_mae）
        4. predictions 必須是列表
        
        Args:
            data: 待驗證的資料
            
        Returns:
            bool: 資料格式是否正確
        """
        try:
            # 檢查基本類型
            if not isinstance(data, dict):
                self._debug("[VALIDATE] ❌ 資料不是字典類型")
                return False
            
            # 檢查頂層結構
            if "metadata" not in data:
                self._debug("[VALIDATE] ❌ 缺少 'metadata' 鍵")
                return False
            
            if "predictions" not in data:
                self._debug("[VALIDATE] ❌ 缺少 'predictions' 鍵")
                return False
            
            # 檢查 metadata
            metadata = data["metadata"]
            if not isinstance(metadata, dict):
                self._debug("[VALIDATE] ❌ 'metadata' 不是字典類型")
                return False
            
            # 檢查必要的模型指標（模型級別，不是車手級別）
            required_meta_keys = ["track", "year", "model_r2", "model_mae"]
            missing_meta = [key for key in required_meta_keys if key not in metadata]
            
            if missing_meta:
                self._debug(f"[VALIDATE] ❌ metadata 缺少必要的鍵: {missing_meta}")
                return False
            
            # 驗證 model_r2 和 model_mae 是數值
            if not isinstance(metadata["model_r2"], (int, float)):
                self._debug("[VALIDATE] ❌ model_r2 不是數值類型")
                return False
            
            if not isinstance(metadata["model_mae"], (int, float)):
                self._debug("[VALIDATE] ❌ model_mae 不是數值類型")
                return False
            
            # 檢查 predictions
            predictions = data["predictions"]
            if not isinstance(predictions, list):
                self._debug("[VALIDATE] ❌ 'predictions' 不是列表類型")
                return False
            
            if len(predictions) == 0:
                self._debug("[VALIDATE] ⚠️ 'predictions' 列表為空")
                return False
            
            # 檢查第一個預測資料是否包含必要欄位
            first_pred = predictions[0]
            required_pred_fields = [
                "rank", "driver", "team", 
                "fp3_time", "predicted_time", "improvement"
            ]
            missing_pred_fields = [
                field for field in required_pred_fields 
                if field not in first_pred
            ]
            
            if missing_pred_fields:
                self._debug(f"[VALIDATE] ❌ 預測資料缺少欄位: {missing_pred_fields}")
                return False
            
            # ✅ 驗證通過
            self._debug(f"[VALIDATE] ✅ 資料格式驗證通過")
            self._debug(f"[VALIDATE]   - 賽道: {metadata['track']}")
            self._debug(f"[VALIDATE]   - 模型 R²: {metadata['model_r2']:.4f}")
            self._debug(f"[VALIDATE]   - 模型 MAE: {metadata['model_mae']:.3f}s")
            self._debug(f"[VALIDATE]   - 預測數量: {len(predictions)}")
            return True
            
        except Exception as e:
            self._debug(f"[VALIDATE] ❌ 驗證過程發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        """
        處理數據為標準格式
        
        重寫基類方法，確保調用 _transform_data_for_display() 進行數據轉換
        
        Args:
            raw_data: 原始數據
            
        Returns:
            Dict[str, Any]: 處理並轉換後的數據
        """
        self._debug("[PROCESS_DATA] 開始處理數據...")
        
        # 基本類型檢查
        if isinstance(raw_data, dict):
            # 調用轉換方法添加計算欄位
            transformed_data = self._transform_data_for_display(raw_data)
            self._debug("[PROCESS_DATA] ✅ 數據轉換完成")
            return transformed_data
        
        if raw_data is None:
            self._debug("[PROCESS_DATA] ⚠️  原始數據為 None")
            return {}
        
        self._debug("[PROCESS_DATA] ⚠️  原始數據類型異常，包裝為字典")
        return {"raw_data": raw_data}
    
    def _transform_data_for_display(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        轉換資料為顯示格式
        
        主要工作：
        1. 計算統計摘要（平均預測時間、時間範圍）
        2. 確保資料排序（按 rank 升序）
        3. 計算平均改善幅度
        4. 為每個預測添加額外的顯示欄位
        
        Args:
            data: 原始資料
            
        Returns:
            Dict: 轉換後的資料
        """
        try:
            self._debug("[TRANSFORM] 開始轉換資料...")
            
            metadata = data["metadata"]
            predictions = data["predictions"]
            
            # ========== 1. 確保按 rank 排序 ==========
            predictions.sort(key=lambda x: x.get("rank", 999))
            
            # ========== 2. 計算統計摘要 ==========
            pred_times = [p["predicted_time"] for p in predictions]
            improvements = [p["improvement"] for p in predictions]
            
            # 平均預測時間
            avg_prediction = sum(pred_times) / len(pred_times)
            
            # 預測時間範圍
            min_prediction = min(pred_times)
            max_prediction = max(pred_times)
            prediction_range = max_prediction - min_prediction
            
            # 平均改善幅度
            avg_improvement = sum(improvements) / len(improvements)
            
            # 添加到 metadata
            metadata["avg_prediction_time"] = avg_prediction
            metadata["min_prediction_time"] = min_prediction
            metadata["max_prediction_time"] = max_prediction
            metadata["prediction_range"] = prediction_range
            metadata["avg_improvement"] = avg_improvement
            
            self._debug(f"[TRANSFORM] 統計摘要:")
            self._debug(f"  - 平均預測時間: {avg_prediction:.3f}s")
            self._debug(f"  - 時間範圍: {prediction_range:.3f}s ({min_prediction:.3f} ~ {max_prediction:.3f})")
            self._debug(f"  - 平均改善: {avg_improvement:.3f}s")
            
            # ========== 3. 驗證 FP3 預測名次和 Q 名次 ==========
            # ✅ 修正 (2025-11-05): CLI F74 現在直接在 JSON 中包含這些欄位
            # 前端不再重複計算，只需驗證數據完整性
            
            # 檢查 fp3_predicted_rank 是否存在
            missing_fp3_rank = [p for p in predictions if "fp3_predicted_rank" not in p]
            if missing_fp3_rank:
                self._debug(f"⚠️  警告: {len(missing_fp3_rank)} 位車手缺少 fp3_predicted_rank")
                self._debug("   執行補償計算...")
                # 補償計算（向後兼容舊 JSON）
                fp3_sorted = sorted(predictions, key=lambda x: x["fp3_time"])
                for rank, pred in enumerate(fp3_sorted, start=1):
                    if "fp3_predicted_rank" not in pred:
                        pred["fp3_predicted_rank"] = rank
            else:
                self._debug(f"✅ 所有車手都有 fp3_predicted_rank")
            
            # 檢查 actual_q_rank 是否存在
            drivers_with_q_time = [p for p in predictions if p.get("actual_q_time") is not None]
            missing_q_rank = [p for p in drivers_with_q_time if "actual_q_rank" not in p]
            
            if missing_q_rank:
                self._debug(f"⚠️  警告: {len(missing_q_rank)} 位車手有 Q 時間但缺少 actual_q_rank")
                self._debug("   執行補償計算...")
                # 補償計算（向後兼容舊 JSON）
                q_sorted = sorted(drivers_with_q_time, key=lambda x: x["actual_q_time"])
                for rank, pred in enumerate(q_sorted, start=1):
                    if "actual_q_rank" not in pred:
                        pred["actual_q_rank"] = rank
            else:
                q_rank_count = len([p for p in predictions if p.get("actual_q_rank") is not None])
                self._debug(f"✅ {q_rank_count} 位車手有 actual_q_rank")
            
            # 確保沒有 Q 時間的車手 actual_q_rank 為 None
            for pred in predictions:
                if pred.get("actual_q_time") is None and "actual_q_rank" not in pred:
                    pred["actual_q_rank"] = None
            
            # ========== 4. 為每個預測添加顯示欄位 ==========
            for pred in predictions:
                # 計算與最快預測時間的差距
                pred["gap_to_fastest"] = pred["predicted_time"] - min_prediction
                
                # 確保 actual_q_time 存在（可能為 None）
                if "actual_q_time" not in pred:
                    pred["actual_q_time"] = None
                
                # 如果有實際 Q 結果，計算預測誤差
                if pred["actual_q_time"] is not None:
                    pred["prediction_error"] = pred["predicted_time"] - pred["actual_q_time"]
                else:
                    pred["prediction_error"] = None
            
            # ========== 5. 計算可靠性評估文字 ==========
            r2 = metadata["model_r2"]
            if r2 >= 0.90:
                reliability = tr("r2_excellent", "極佳（90%+）")
                reliability_color = "green"
            elif r2 >= 0.85:
                reliability = tr("r2_good", "優秀（85%+）")
                reliability_color = "darkgreen"
            elif r2 >= 0.75:
                reliability = tr("r2_fair", "良好（75%+）")
                reliability_color = "orange"
            else:
                reliability = tr("r2_moderate", "中等（<75%）")
                reliability_color = "red"
            
            metadata["reliability_text"] = reliability
            metadata["reliability_color"] = reliability_color
            
            self._debug(f"[TRANSFORM] ✅ 資料轉換完成")
            self._debug(f"[TRANSFORM]   - 可靠性: {reliability}")
            
            return data
            
        except Exception as e:
            self._debug(f"[TRANSFORM] ❌ 轉換過程發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            # 即使轉換失敗，也返回原始資料
            return data
    
    def _find_fastest_driver(self, predictions: list, fastest_time: float) -> Optional[str]:
        """
        找出預測最快的車手代碼
        
        Args:
            predictions: 車手預測列表
            fastest_time: 最快預測時間
            
        Returns:
            str: 車手代碼，未找到則返回 None
        """
        for driver in predictions:
            if driver.get("predicted_time") == fastest_time:
                return driver.get("driver")
        return None
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        ⚠️ API-ONLY 模式: 禁止 CLI 調用
        
        根據 API-ONLY 政策，GUI 模組不允許直接調用 CLI 進程
        只能通過以下方式獲取資料：
        1. REST API (refactored_api.py) - function_id=73
        2. 讀取已存在的本地 JSON 檔案
        
        Returns:
            bool: 固定返回 False
        """
        self._debug("⚠️ [API-ONLY] CLI 調用已禁用")
        self._debug("💡 提示: 請使用 API 獲取預測資料，或手動執行 CLI 訓練模型")
        self._debug("💡 CLI 命令範例: python f1_analysis_modular_main.py -f 73 --trials 500 --track Austria")
        return False
    
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """
        驗證載入參數
        
        Args:
            params: 參數字典
            
        Returns:
            bool: 參數是否有效
        """
        # 基本參數檢查（排位賽預測只需要 year 和 race）
        required = ["year", "race"]
        for key in required:
            if key not in params:
                self._debug(f"❌ 缺少必要參數: {key}")
                return False
        return True
    
    def _build_filename_patterns(self, **params) -> List[str]:
        """
        建立檔案搜尋模式
        
        Args:
            **params: 載入參數 (year, race)
            
        Returns:
            List[str]: 檔案搜尋模式列表
        """
        year = params.get("year", self.year)
        race = params.get("race", self.race)
        
        # 排位賽預測的檔案命名模式
        patterns = [
            f"qualifying_prediction_{year}_{race}.json",
            f"qual_pred_{year}_{race}.json",
            f"*qualifying*prediction*{year}*{race}*.json"
        ]
        
        return patterns


# ========== 測試代碼 ==========
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    print("=" * 60)
    print("排位賽預測資料載入器 - 獨立測試")
    print("=" * 60)
    
    # 創建 Qt 應用程式（需要 QTimer）
    app = QApplication(sys.argv)
    
    # 創建測試實例
    loader = QualifyingPredictionDataLoader(
        year="2025",
        race="Austria"
    )
    
    print(f"\n📋 載入器配置:")
    print(f"  CLI Function: {loader.CLI_FUNCTION}")
    print(f"  JSON Pattern: {loader.JSON_PATTERN}")
    print(f"  參數: {loader.year} {loader.race}")
    
    # 測試檔案搜尋模式
    print(f"\n🔍 檔案搜尋模式:")
    patterns = loader._build_filename_patterns(
        year=loader.year,
        race=loader.race
    )
    for i, pattern in enumerate(patterns, 1):
        print(f"  {i}. {pattern}")
    
    # 設置信號處理
    def on_data_loaded(data):
        print(f"\n✅ 數據載入成功!")
        
        if "metadata" in data and "predictions" in data:
            metadata = data["metadata"]
            predictions = data["predictions"]
            
            print(f"\n📊 資料摘要:")
            print(f"  賽道: {metadata.get('track', 'N/A')}")
            print(f"  年份: {metadata.get('year', 'N/A')}")
            print(f"  模型 R²: {metadata.get('model_r2', 0):.4f}")
            print(f"  模型 MAE: {metadata.get('model_mae', 0):.3f}s")
            print(f"  預測數量: {len(predictions)}")
            print(f"  平均預測時間: {metadata.get('avg_prediction_time', 0):.3f}s")
            print(f"  平均改善: {metadata.get('avg_improvement', 0):.3f}s")
            print(f"  可靠性: {metadata.get('reliability_text', 'N/A')}")
            
            # 顯示前 3 名預測
            print(f"\n🏆 前 3 名預測:")
            for i, pred in enumerate(predictions[:3]):
                print(
                    f"  {i+1}. {pred['driver']} ({pred['team']}) - "
                    f"預測: {pred['predicted_time']:.3f}s "
                    f"(FP3: {pred['fp3_time']:.3f}s, 改善: {pred['improvement']:.3f}s)"
                )
        
        app.quit()
    
    def on_load_error(error_msg):
        print(f"\n❌ 載入錯誤: {error_msg}")
        app.quit()
    
    loader.data_loaded.connect(on_data_loaded)
    loader.load_error.connect(on_load_error)
    
    # 啟動載入
    print(f"\n🚀 啟動數據載入...")
    success = loader.load_data(
        year=loader.year,
        race=loader.race
    )
    
    if not success:
        print("❌ 載入啟動失敗")
        sys.exit(1)
    
    # 進入事件循環
    sys.exit(app.exec_())
