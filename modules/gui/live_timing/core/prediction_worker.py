"""
Prediction Worker - 背景執行緒預測器
====================================

將 OT% 和 CC% 的 ML 推理移到背景執行緒, 
避免阻塞主 GUI 執行緒.

Author: F1T Team
Date: 2025-12-10
"""

import queue
import time
from typing import Dict, Any, Optional
from PyQt5.QtCore import QThread, pyqtSignal

from core.logger import get_logger

logger = get_logger("live_timing.prediction_worker", component="gui")


class PredictionWorker(QThread):
    """
    背景預測工作執行緒
    
    ✅ 策略 A:將 ML 模型推理移到背景執行緒
    
    特性:
    - 非阻塞:主執行緒不等待 ML 推理完成
    - 高效:充分利用多核心 CPU
    - 實時:結果延遲僅 1-2 幀(50-100ms)
    - 安全:使用隊列機制避免競爭條件
    
    Signals:
        predictions_ready: 當預測完成時發出
            參數: Dict[str, Dict[str, int]]
            格式: {driver_num: {'ot%': int, 'cc%': int}}
    """
    
    predictions_ready = pyqtSignal(dict)  # {driver_num: {'ot%': ..., 'cc%': ...}}
    
    def __init__(self, overtake_predictor, close_combat_predictor, parent=None):
        """
        初始化背景預測器
        
        Args:
            overtake_predictor: F83 超車預測器實例
            close_combat_predictor: F85 近距離接觸預測器實例
            parent: 父物件
        """
        super().__init__(parent)
        
        self._running = False
        self._queue = queue.Queue(maxsize=2)  # 限制隊列大小, 避免積壓
        
        # 預測器實例(在背景執行緒中使用)
        self._overtake_predictor = overtake_predictor
        self._close_combat_predictor = close_combat_predictor
        
        # 性能監控
        self._total_predictions = 0
        self._total_time = 0.0
        self._last_report_time = 0.0
    
    def queue_prediction(self, snapshot: Dict[str, Any], tyre_state: Dict, 
                        race_progress: float, track_status_green: bool):
        """
        將預測請求加入隊列(主執行緒調用)
        
        Args:
            snapshot: 當前快照
            tyre_state: 輪胎狀態
            race_progress: 比賽進度 (0.0-1.0)
            track_status_green: 是否綠旗
        """
        if not self._running:
            return
        
        try:
            # 非阻塞放入隊列, 如果隊列滿則放棄舊請求
            if self._queue.full():
                try:
                    self._queue.get_nowait()  # 移除舊請求
                except queue.Empty:
                    pass
            
            self._queue.put_nowait({
                'snapshot': snapshot,
                'tyre_state': tyre_state,
                'race_progress': race_progress,
                'track_status_green': track_status_green
            })
        except queue.Full:
            # 隊列滿, 跳過此次預測
            pass
    
    def run(self):
        """Background thread main loop"""
        if self._running:
            logger.warning("[PREDICTION_WORKER] 執行緒已在運行, 避免重複啟動")
            return
        
        self._running = True
        logger.info("[PREDICTION_WORKER] 背景預測執行緒啟動")
        
        while self._running and not self.isInterruptionRequested():
            try:
                # 等待預測請求(最多 100ms)
                request = self._queue.get(timeout=0.1)
                
                start_time = time.perf_counter()
                
                # 執行預測
                results = self._perform_predictions(request)
                
                # 計算耗時
                elapsed = time.perf_counter() - start_time
                self._total_predictions += 1
                self._total_time += elapsed
                
                # 統計非零預測
                nonzero_ot = sum(1 for v in results.values() if v.get('ot%', 0) > 0)
                nonzero_cc = sum(1 for v in results.values() if v.get('cc%', 0) > 0)
                
                # ✅ 中斷檢查:被中斷時不發送信號
                if self.isInterruptionRequested():
                    break
                
                # 發送結果
                self.predictions_ready.emit(results)
                
                # 調試日誌(改為 INFO 級別)
                logger.info(
                    "[PREDICTION_WORKER] 完成 | 車手數=%d | OT>0=%d | CC>0=%d | 耗時=%.1fms",
                    len(results), nonzero_ot, nonzero_cc, elapsed * 1000
                )
                
                # 性能報告(每 5 秒)
                if time.time() - self._last_report_time > 5.0:
                    avg_time = self._total_time / max(1, self._total_predictions)
                    logger.info(
                        "[PREDICTION_WORKER] 性能統計: 總次數=%d, 平均耗時=%.1fms, 總耗時=%.1fs",
                        self._total_predictions,
                        avg_time * 1000,
                        self._total_time
                    )
                    self._last_report_time = time.time()
                
            except queue.Empty:
                # 無新請求, 繼續等待
                continue
            except Exception as e:
                logger.exception("[PREDICTION_WORKER] 預測執行失敗: %s", e)
        
        logger.info("[PREDICTION_WORKER] 背景預測執行緒停止")
    
    def _perform_predictions(self, request: Dict) -> Dict[str, Dict[str, int]]:
        """
        Execute ML inference (in background thread)
        
        Args:
            request: prediction request dict
            
        Returns:
            {driver_num: {'ot%': int, 'cc%': int}}
        """
        snapshot = request['snapshot']
        tyre_state = request['tyre_state']
        race_progress = request['race_progress']
        track_status_green = request['track_status_green']
        
        drivers = snapshot.get('drivers', {})
        results = {}
        
        # 檢查當前圈數(Lap 1-2 不計算)
        current_lap = max((d.get('lap', 0) for d in drivers.values()), default=0)
        if current_lap <= 2:
            # Lap 1-2:所有車手返回 0
            for driver_num in drivers:
                results[driver_num] = {'ot%': 0, 'cc%': 0}
            return results
        
        # 按位置排序
        sorted_drivers = []
        for driver_num, driver_data in drivers.items():
            pos = driver_data.get('position', 99)
            sorted_drivers.append((driver_num, driver_data, pos))
        sorted_drivers.sort(key=lambda x: x[2])
        
        # 為每個車手計算預測
        for i, (driver_num, driver_data, position) in enumerate(sorted_drivers):
            # P1 沒有前車
            if position == 1 or i == 0:
                results[driver_num] = {'ot%': 0, 'cc%': 0}
                continue
            
            # 獲取前車
            ahead_driver_num, ahead_driver_data, _ = sorted_drivers[i - 1]
            
            # 獲取間距
            gap_str = driver_data.get('gap_to_ahead', '') or driver_data.get('gap_to_ahead_display', '')
            gap_seconds = self._parse_gap_seconds(gap_str)
            
            if gap_seconds is None or gap_seconds > 8.0:
                results[driver_num] = {'ot%': 0, 'cc%': 0}
                continue
            
            # 獲取輪胎資訊
            attacker_tyre = 'MEDIUM'
            defender_tyre = 'MEDIUM'
            tyre_age_diff = 0
            
            if tyre_state:
                attacker_tyre_info = tyre_state.get(driver_num, {})
                defender_tyre_info = tyre_state.get(ahead_driver_num, {})
                
                attacker_tyre = attacker_tyre_info.get('compound', 'MEDIUM')
                defender_tyre = defender_tyre_info.get('compound', 'MEDIUM')
                
                attacker_age = attacker_tyre_info.get('age', 0)
                defender_age = defender_tyre_info.get('age', 0)
                tyre_age_diff = defender_age - attacker_age
            
            # DRS 可用性
            drs_available = gap_seconds < 1.0
            
            # 間距趨勢(簡化版)
            gap_trend = driver_data.get('gap_trend', 0.0)
            is_catching = gap_trend < -0.1
            
            # 計算 OT%
            ot_prob = 0
            if self._overtake_predictor:
                try:
                    result = self._overtake_predictor.predict(
                        gap_seconds=gap_seconds,
                        gap_delta=gap_trend if gap_trend != 0 else -0.1,
                        is_catching=is_catching,
                        drs_available=drs_available,
                        attacker_tyre=attacker_tyre,
                        defender_tyre=defender_tyre,
                        tyre_age_diff=tyre_age_diff,
                        track_status_green=track_status_green,
                        attacker_position=position,
                        race_progress=race_progress
                    )
                    ot_prob = int(round(result.probability * 100))
                except Exception as e:
                    logger.debug("[PREDICTION_WORKER] OT% 預測失敗: %s", e)
            
            # 計算 CC%
            cc_prob = 0
            if self._close_combat_predictor:
                try:
                    # CC% 需要額外特徵(簡化版)
                    gap_trend_3lap = gap_trend  # 簡化
                    min_gap_last_5lap = gap_seconds  # 簡化
                    consecutive_catching_laps = 1 if is_catching else 0
                    
                    result = self._close_combat_predictor.predict(
                        gap_seconds=gap_seconds,
                        gap_delta=gap_trend if gap_trend != 0 else -0.1,
                        is_catching=is_catching,
                        drs_available=drs_available,
                        attacker_tyre=attacker_tyre,
                        defender_tyre=defender_tyre,
                        tyre_age_diff=tyre_age_diff,
                        track_status_green=track_status_green,
                        attacker_position=position,
                        race_progress=race_progress,
                        gap_trend_3lap=gap_trend_3lap,
                        min_gap_last_5lap=min_gap_last_5lap,
                        consecutive_catching_laps=consecutive_catching_laps
                    )
                    cc_prob = int(round(result.probability * 100))
                except Exception as e:
                    logger.debug("[PREDICTION_WORKER] CC% 預測失敗: %s", e)
            
            results[driver_num] = {'ot%': ot_prob, 'cc%': cc_prob}
        
        return results
    
    def _parse_gap_seconds(self, gap_str) -> Optional[float]:
        """
        解析間距為秒數
        
        Args:
            gap_str: 可能是字符串('+2.3s')或數字(2.3)
        """
        # 如果已經是數字, 直接返回
        if isinstance(gap_str, (int, float)):
            return float(gap_str)
        
        # 如果不是字符串, 嘗試轉換
        if not isinstance(gap_str, str):
            try:
                return float(gap_str)
            except (ValueError, TypeError, AttributeError):
                return None
        
        # 字符串處理
        if not gap_str or gap_str in ('', '-', 'LAP'):
            return None
        
        try:
            gap_clean = gap_str.replace('+', '').replace('s', '').strip()
            result = float(gap_clean)
            return result
        except (ValueError, AttributeError) as e:
            return None
    
    def stop(self):
        """停止背景執行緒"""
        if not self._running:
            logger.debug("[PREDICTION_WORKER] 執行緒已停止, 忽略重複調用")
            return
        
        logger.info("[PREDICTION_WORKER] 請求停止背景執行緒")
        self._running = False
        
        # 等待執行緒結束(最多 3 秒)
        if self.isRunning():
            logger.info("[PREDICTION_WORKER] 等待執行緒退出...")
            if not self.wait(3000):  # 3 秒超時
                logger.warning("[PREDICTION_WORKER] ⚠️ 執行緒未在 3 秒內退出, 強制終止")
                self.terminate()
                self.wait(1000)  # 再等 1 秒
            else:
                logger.info("[PREDICTION_WORKER] ✅ 執行緒已正常退出")
