"""
API Worker 異步載入功能測試
測試目標：驗證 Worker 能在背景執行緒運行，不阻塞主執行緒

執行命令：
    pytest tests/test_api_worker_async.py -v --tb=short
    pytest tests/test_api_worker_async.py::TestApiWorkerAsync::test_worker_runs_in_background_thread -v
"""
import pytest
import time
import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, QEventLoop, QTimer, QThread, pyqtSignal
import requests


class MockApiDataLoadWorker(QThread):
    """
    模擬 API Worker（測試版本）
    用於測試異步行為，不依賴真實 API
    """
    # 信號定義
    progress_updated = pyqtSignal(int, str)  # (進度%, 狀態訊息)
    data_loaded = pyqtSignal(dict)           # 載入成功
    error_occurred = pyqtSignal(str)         # 載入失敗
    
    def __init__(self, url: str, params: dict, timeout: int = 30, mock_delay: float = 2.0):
        """
        Args:
            url: API 端點 URL
            params: 請求參數字典
            timeout: 超時時間（秒）
            mock_delay: 模擬延遲時間（秒）
        """
        super().__init__()
        self.url = url
        self.params = params
        self.timeout = timeout
        self.mock_delay = mock_delay
        self._is_cancelled = False
    
    def run(self):
        """執行緒主邏輯（在背景執行緒執行）"""
        try:
            # 階段 1: 連接 API (10%)
            self.progress_updated.emit(10, "正在連接 API...")
            time.sleep(self.mock_delay * 0.2)
            if self._is_cancelled:
                return
            
            # 階段 2: 發送請求 (30%)
            self.progress_updated.emit(30, "正在請求數據...")
            time.sleep(self.mock_delay * 0.3)
            if self._is_cancelled:
                return
            
            # 階段 3: 接收數據 (60%)
            self.progress_updated.emit(60, "正在接收數據...")
            time.sleep(self.mock_delay * 0.3)
            if self._is_cancelled:
                return
            
            # 階段 4: 解析 JSON (80%)
            self.progress_updated.emit(80, "正在解析數據...")
            time.sleep(self.mock_delay * 0.1)
            if self._is_cancelled:
                return
            
            # 階段 5: 完成 (100%)
            self.progress_updated.emit(100, "載入完成")
            mock_data = {
                'success': True,
                'data': {'test': 'data'},
                'url': self.url,
                'params': self.params
            }
            self.data_loaded.emit(mock_data)
            
        except Exception as e:
            self.error_occurred.emit(f"測試錯誤: {str(e)}")
    
    def cancel(self):
        """取消載入操作"""
        self._is_cancelled = True
        self.quit()


@pytest.fixture(scope='session')
def qapp():
    """提供 QApplication 實例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestApiWorkerAsync:
    """API Worker 異步行為測試"""
    
    def test_worker_runs_in_background_thread(self, qapp, qtbot):
        """
        測試 1: Worker 在背景執行緒運行
        驗證：主執行緒不被阻塞
        
        成功標準：Worker 啟動耗時 < 100ms
        """
        print("\n" + "="*70)
        print("🧪 測試 1: Worker 在背景執行緒運行")
        print("="*70)
        
        # 創建 Worker
        worker = MockApiDataLoadWorker(
            url="http://test.api/analyze",
            params={'year': 2025, 'race': 'Japan'},
            mock_delay=2.0  # 模擬 2 秒延遲
        )
        
        # 追蹤信號
        progress_signals = []
        data_loaded = []
        
        worker.progress_updated.connect(lambda p, m: progress_signals.append((p, m)))
        worker.data_loaded.connect(lambda d: data_loaded.append(d))
        
        # 啟動 Worker
        print("📊 啟動 Worker...")
        start_time = time.time()
        worker.start()
        
        # ✅ 關鍵測試：主執行緒應立即返回（不阻塞）
        immediate_return_time = time.time() - start_time
        print(f"⏱️  Worker 啟動耗時: {immediate_return_time*1000:.1f}ms")
        
        assert immediate_return_time < 0.1, \
            f"❌ 失敗：Worker 啟動阻塞主執行緒 {immediate_return_time*1000:.1f}ms (應 < 100ms)"
        
        print(f"✅ 通過：Worker 立即啟動，未阻塞主執行緒")
        
        # 等待 Worker 完成（使用事件循環，不阻塞）
        print("⏳ 等待 Worker 完成...")
        loop = QEventLoop()
        worker.finished.connect(loop.quit)
        QTimer.singleShot(5000, loop.quit)  # 5 秒超時
        loop.exec_()
        
        # 驗證信號接收
        print(f"📨 接收到 {len(progress_signals)} 個進度信號")
        print(f"📦 接收到 {len(data_loaded)} 個數據包")
        
        assert len(progress_signals) > 0, "❌ 失敗：未接收到進度信號"
        assert len(data_loaded) > 0, "❌ 失敗：未接收到數據"
        
        print("✅ 測試通過：Worker 在背景執行緒正常運行")
        print("="*70 + "\n")
    
    def test_progress_updates_received(self, qapp, qtbot):
        """
        測試 2: 進度更新信號正常接收
        驗證：至少接收到 5 個階段的進度更新
        
        成功標準：接收到 10%, 30%, 60%, 80%, 100% 五個階段
        """
        print("\n" + "="*70)
        print("🧪 測試 2: 進度更新信號")
        print("="*70)
        
        worker = MockApiDataLoadWorker(
            url="http://test.api/analyze",
            params={'function_id': 1, 'year': 2025, 'race': 'Japan'},
            mock_delay=1.0  # 1 秒總延遲
        )
        
        progress_updates = []
        worker.progress_updated.connect(
            lambda p, m: progress_updates.append((p, m))
        )
        
        # 啟動並等待
        print("📊 啟動 Worker...")
        worker.start()
        worker.wait(5000)
        
        # 顯示接收到的進度
        print(f"\n📨 接收到 {len(progress_updates)} 個進度更新:")
        for progress, message in progress_updates:
            print(f"   {progress:3d}% - {message}")
        
        # 驗證進度階段
        progress_values = [p for p, m in progress_updates]
        
        expected_stages = [10, 30, 60, 80, 100]
        for stage in expected_stages:
            assert stage in progress_values, \
                f"❌ 失敗：缺少階段 {stage}%"
            print(f"✅ 階段 {stage:3d}% 已接收")
        
        print(f"\n✅ 測試通過：所有 5 個進度階段已接收")
        print("="*70 + "\n")
    
    def test_worker_cancellation(self, qapp, qtbot):
        """
        測試 3: Worker 可正常取消
        驗證：取消操作後 Worker 立即停止
        
        成功標準：取消後 Worker 在 2 秒內停止
        """
        print("\n" + "="*70)
        print("🧪 測試 3: Worker 取消功能")
        print("="*70)
        
        worker = MockApiDataLoadWorker(
            url="http://test.api/slow",
            params={},
            mock_delay=10.0  # 模擬 10 秒的長時間操作
        )
        
        print("📊 啟動 Worker (10秒延遲)...")
        worker.start()
        time.sleep(0.5)  # 讓 Worker 開始執行
        
        # 取消 Worker
        print("🛑 取消 Worker...")
        cancel_time = time.time()
        worker.cancel()
        worker.wait(2000)  # 最多等待 2 秒
        stop_time = time.time()
        
        # 驗證停止時間
        stop_duration = stop_time - cancel_time
        print(f"⏱️  Worker 停止耗時: {stop_duration*1000:.1f}ms")
        
        assert stop_duration < 2, \
            f"❌ 失敗：Worker 取消耗時過長: {stop_duration:.3f}s (應 < 2s)"
        assert not worker.isRunning(), "❌ 失敗：Worker 未正確停止"
        
        print(f"✅ 測試通過：Worker 在 {stop_duration*1000:.0f}ms 內停止")
        print("="*70 + "\n")
    
    def test_error_handling(self, qapp, qtbot):
        """
        測試 4: 錯誤處理機制
        驗證：發生錯誤時正確發出 error_occurred 信號
        
        成功標準：接收到錯誤信號
        """
        print("\n" + "="*70)
        print("🧪 測試 4: 錯誤處理機制")
        print("="*70)
        
        # 創建會出錯的 Worker
        class ErrorWorker(MockApiDataLoadWorker):
            def run(self):
                try:
                    self.progress_updated.emit(10, "開始處理...")
                    time.sleep(0.2)
                    raise ValueError("模擬錯誤")
                except Exception as e:
                    self.error_occurred.emit(str(e))
        
        worker = ErrorWorker(url="http://test.api/error", params={})
        
        errors = []
        worker.error_occurred.connect(lambda e: errors.append(e))
        
        print("📊 啟動會出錯的 Worker...")
        worker.start()
        worker.wait(2000)
        
        # 驗證錯誤信號
        print(f"📨 接收到 {len(errors)} 個錯誤信號")
        if errors:
            print(f"❌ 錯誤訊息: {errors[0]}")
        
        assert len(errors) > 0, "❌ 失敗：未接收到錯誤信號"
        assert "模擬錯誤" in errors[0], \
            f"❌ 失敗：錯誤訊息不正確: {errors[0]}"
        
        print(f"✅ 測試通過：錯誤正確捕獲和傳遞")
        print("="*70 + "\n")


class TestMultipleWorkersParallel:
    """多 Worker 並發測試"""
    
    def test_multiple_workers_do_not_block_each_other(self, qapp, qtbot):
        """
        測試 5: 多個 Worker 並發執行不互相阻塞
        驗證：5 個 Worker 同時運行，總時間接近單個時間
        
        成功標準：5 個 Worker 總時間 < 4 秒（單個 2 秒）
        """
        print("\n" + "="*70)
        print("🧪 測試 5: 多 Worker 並發執行")
        print("="*70)
        
        workers = []
        results = []
        
        # 創建 5 個 Worker（每個 2 秒）
        print("📊 創建 5 個 Worker (每個 2 秒延遲)...")
        for i in range(5):
            worker = MockApiDataLoadWorker(
                url=f"http://test.api/worker{i}",
                params={'id': i},
                mock_delay=2.0
            )
            worker.data_loaded.connect(
                lambda d, i=i: results.append((i, time.time()))
            )
            workers.append(worker)
        
        # 同時啟動所有 Worker
        print("🚀 同時啟動所有 Worker...")
        start_time = time.time()
        for worker in workers:
            worker.start()
        
        # 等待所有完成
        print("⏳ 等待所有 Worker 完成...")
        for worker in workers:
            worker.wait(5000)
        
        total_time = time.time() - start_time
        print(f"\n⏱️  總耗時: {total_time:.2f}s")
        print(f"📦 完成數量: {len(results)}/5")
        
        # 驗證並發執行（總時間應接近 2 秒，而非 10 秒）
        assert total_time < 4, \
            f"❌ 失敗：Workers 未並發執行，總時間 {total_time:.1f}s (應 < 4s)"
        assert len(results) == 5, \
            f"❌ 失敗：部分 Worker 未完成：{len(results)}/5"
        
        print(f"✅ 測試通過：5 個 Worker 並發完成，總時間 {total_time:.1f}s")
        print("="*70 + "\n")


if __name__ == '__main__':
    """
    直接執行測試
    使用方式：python tests/test_api_worker_async.py
    """
    print("\n" + "🚀 " + "="*66 + " 🚀")
    print("🚀   API Worker 異步載入功能測試                                     🚀")
    print("🚀 " + "="*66 + " 🚀\n")
    
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes',
        '-p', 'no:warnings'
    ])
