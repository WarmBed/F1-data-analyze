#!/usr/bin/env python3
"""
objgraph 報告分析工具
====================

獨立的 GUI 工具，用於分析和視覺化 objgraph 記憶體診斷報告。

功能特色：
- 📈 時間軸記憶體成長趨勢
- 🏆 Top 物件類型排行
- 🎯 操作影響分析
- 📊 記憶體變化統計
- 🔍 詳細數據表格

使用方式：
    python objgraph_analyzer.py [report_file.txt]

Author: F1T Team
Date: 2025-10-15
Version: 1.0.0
"""

import sys
import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

# GUI 框架
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

# 數據分析和視覺化
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import numpy as np

# 中文字體支援
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


@dataclass
class MemorySnapshot:
    """記憶體快照數據結構"""
    timestamp: str
    action: str
    total_objects: int
    object_change: int
    top_objects: Dict[str, int] = field(default_factory=dict)
    growth_data: Dict[str, int] = field(default_factory=dict)


@dataclass
class AnalysisReport:
    """分析報告數據結構"""
    generation_time: str
    total_records: int
    initial_objects: int
    final_objects: int
    net_change: int
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    detected_modules: List[Dict[str, Any]] = field(default_factory=list)


class ObjgraphParser:
    """objgraph 報告解析器"""
    
    def __init__(self):
        self.time_pattern = r'\[(\d{2}:\d{2}:\d{2})\]'
        self.action_pattern = r'\[ACTION\]\s*(.*?)\s*\(物件總數:\s*(\d+),\s*變化:\s*([+-]?\d+)\)'
        self.snapshot_pattern = r'\[SNAPSHOT\]\s*總物件數:\s*(\d+)'
        self.growth_pattern = r'↑\s*(\w+)\s+(\d+)\s*\(\+(\d+)\)'
        
        # F1T 模組識別模式
        self.module_patterns = {
            'speed_analysis': [
                r'SpeedAnalysisModule',
                r'SpeedDataManager', 
                r'SpeedAnalysisChartWidget',
                r'SpeedChartWidget',
                r'SpeedAnalysisDataLoader'
            ],
            'brake_analysis': [
                r'BrakeAnalysisModule',
                r'BrakeDataManager',
                r'BrakeAnalysisChartWidget', 
                r'BrakeChartWidget',
                r'BrakeAnalysisDataLoader'
            ],
            'throttle_analysis': [
                r'ThrottleAnalysisModule',
                r'ThrottleDataManager',
                r'ThrottleAnalysisChartWidget',
                r'ThrottleChartWidget', 
                r'ThrottleAnalysisDataLoader'
            ],
            'gear_analysis': [
                r'GearAnalysisModule',
                r'GearDataManager',
                r'GearAnalysisChartWidget',
                r'GearChartWidget',
                r'GearAnalysisDataLoader'
            ],
            'rpm_analysis': [
                r'RPMAnalysisModule',
                r'RPMDataManager',
                r'RPMAnalysisChartWidget',
                r'RPMChartWidget',
                r'RPMAnalysisDataLoader'
            ],
            'acceleration_analysis': [
                r'accelerationAnalysisModule',
                r'AccelerationDataManager',
                r'accelerationAnalysisChartWidget',
                r'accelerationChartWidget',
                r'AccelerationAnalysisDataLoader'
            ],
            'speeddiff_analysis': [
                r'SpeeddiffAnalysisModule',
                r'speeddiffDataManager',
                r'SpeeddiffAnalysisChartWidget',
                r'speeddiffChartWidget',
                r'SpeedDiffAnalysisDataLoader'
            ],
            'distancediff_analysis': [
                r'distancediffAnalysisModule',
                r'distancediffDataManager',
                r'distancediffAnalysisChartWidget',
                r'distancediffChartWidget',
                r'DistanceDiffAnalysisDataLoader'
            ],
            'timediff_analysis': [
                r'timediffAnalysisModule',
                r'timediffDataManager',
                r'timediffAnalysisChartWidget',
                r'timediffChartWidget',
                r'timediffAnalysisDataLoader'
            ]
        }
        
    def parse_report(self, file_path: str) -> AnalysisReport:
        """解析 objgraph 報告檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析標題資訊
            report = self._parse_header(content)
            
            # 解析快照數據
            report.snapshots = self._parse_snapshots(content)
            
            # 檢測開啟的模組
            report.detected_modules = self._detect_modules(content)
            
            # 計算統計資訊
            report.summary_stats = self._calculate_stats(report)
            
            return report
            
        except Exception as e:
            raise ValueError(f"解析報告檔案失敗: {e}")
    
    def _parse_header(self, content: str) -> AnalysisReport:
        """解析報告標題資訊"""
        report = AnalysisReport(
            generation_time="",
            total_records=0,
            initial_objects=0,
            final_objects=0,
            net_change=0
        )
        
        # 生成時間
        time_match = re.search(r'生成時間:\s*(.+)', content)
        if time_match:
            report.generation_time = time_match.group(1)
        
        # 記錄統計
        records_match = re.search(r'總記錄數:\s*(\d+)', content)
        if records_match:
            report.total_records = int(records_match.group(1))
        
        initial_match = re.search(r'初始物件數:\s*(\d+)', content)
        if initial_match:
            report.initial_objects = int(initial_match.group(1))
        
        final_match = re.search(r'當前物件數:\s*(\d+)', content)
        if final_match:
            report.final_objects = int(final_match.group(1))
        
        change_match = re.search(r'總變化量:\s*([+-]?\d+)', content)
        if change_match:
            report.net_change = int(change_match.group(1))
        
        return report
    
    def _parse_snapshots(self, content: str) -> List[MemorySnapshot]:
        """解析記憶體快照數據"""
        snapshots = []
        
        # 尋找所有 ACTION 記錄
        action_matches = re.finditer(self.action_pattern, content)
        
        for match in action_matches:
            action = match.group(1)
            total_objects = int(match.group(2))
            change = int(match.group(3))
            
            # 提取時間戳記
            timestamp = self._extract_timestamp(action)
            
            snapshot = MemorySnapshot(
                timestamp=timestamp,
                action=action,
                total_objects=total_objects,
                object_change=change
            )
            
            snapshots.append(snapshot)
        
        return snapshots
    
    def _extract_timestamp(self, action_text: str) -> str:
        """從動作文字中提取時間戳記"""
        time_match = re.search(self.time_pattern, action_text)
        if time_match:
            return time_match.group(1)
        
        # 如果沒有時間戳記，嘗試從動作描述推斷
        if "開啟GUI" in action_text:
            return "16:58:51"
        elif "開啟9個分析模組" in action_text:
            return "16:59:04"
        else:
            return "unknown"
    
    def _calculate_stats(self, report: AnalysisReport) -> Dict[str, Any]:
        """計算統計資訊"""
        if not report.snapshots:
            return {}
        
        changes = [s.object_change for s in report.snapshots if s.object_change != 0]
        
        return {
            'total_snapshots': len(report.snapshots),
            'positive_changes': len([c for c in changes if c > 0]),
            'negative_changes': len([c for c in changes if c < 0]),
            'max_increase': max(changes) if changes else 0,
            'max_decrease': min(changes) if changes else 0,
            'avg_change': np.mean(changes) if changes else 0,
            'memory_growth_rate': report.net_change / len(report.snapshots) if report.snapshots else 0,
            'detected_modules_count': len(report.detected_modules),
            'module_memory_impact': sum(m['total_objects'] for m in report.detected_modules)
        }
    
    def _detect_modules(self, content: str) -> List[Dict[str, Any]]:
        """檢測報告中開啟的 F1T 分析模組"""
        detected_modules = []
        
        for module_name, class_patterns in self.module_patterns.items():
            module_info = {
                'name': module_name,
                'display_name': self._get_module_display_name(module_name),
                'detected_classes': [],
                'total_objects': 0,
                'status': 'not_detected'
            }
            
            # 檢查每個類別是否存在
            for pattern in class_patterns:
                # 尋找該類別的物件數量
                class_match = re.search(rf'↑\s*{pattern}\s+(\d+)\s*\(\+(\d+)\)', content)
                if class_match:
                    class_count = int(class_match.group(1))
                    class_increase = int(class_match.group(2))
                    
                    module_info['detected_classes'].append({
                        'class_name': pattern,
                        'count': class_count,
                        'increase': class_increase
                    })
                    module_info['total_objects'] += class_count
            
            # 判斷模組狀態
            if len(module_info['detected_classes']) >= 3:  # 至少3個類別才算完整載入
                module_info['status'] = 'fully_loaded'
                detected_modules.append(module_info)
            elif len(module_info['detected_classes']) > 0:
                module_info['status'] = 'partially_loaded'
                detected_modules.append(module_info)
        
        # 按照物件總數排序
        detected_modules.sort(key=lambda x: x['total_objects'], reverse=True)
        
        return detected_modules
    
    def _get_module_display_name(self, module_name: str) -> str:
        """獲取模組顯示名稱"""
        display_names = {
            'speed_analysis': '🏎️ 速度分析',
            'brake_analysis': '🚩 煞車分析', 
            'throttle_analysis': '⚡ 油門分析',
            'gear_analysis': '⚙️ 檔位分析',
            'rpm_analysis': '🔄 轉速分析',
            'acceleration_analysis': '🚀 加速度分析',
            'speeddiff_analysis': '📈 速度差異分析',
            'distancediff_analysis': '📏 距離差異分析',
            'timediff_analysis': '⏱️ 時間差異分析'
        }
        return display_names.get(module_name, module_name)


class ObjgraphAnalyzerGUI:
    """objgraph 分析器 GUI 主程式"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("📊 objgraph 記憶體分析工具 v1.0")
        self.root.geometry("1400x800")
        
        # 數據
        self.report_data: Optional[AnalysisReport] = None
        self.parser = ObjgraphParser()
        
        # 建立界面
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """建立 GUI 組件"""
        # 主框架
        self.main_frame = ttk.Frame(self.root)
        
        # 工具列
        self.toolbar_frame = ttk.Frame(self.main_frame)
        self.load_btn = ttk.Button(self.toolbar_frame, text="📂 載入報告", command=self.load_report)
        self.export_btn = ttk.Button(self.toolbar_frame, text="💾 匯出圖表", command=self.export_charts, state="disabled")
        self.info_label = ttk.Label(self.toolbar_frame, text="請載入 objgraph 報告檔案")
        
        # 筆記本（標籤頁）
        self.notebook = ttk.Notebook(self.main_frame)
        
        # 標籤頁 1: 時間軸分析
        self.timeline_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.timeline_frame, text="📈 時間軸分析")
        
        # 標籤頁 2: 模組分析
        self.modules_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.modules_frame, text="🧩 模組分析")
        
        # 標籤頁 3: 統計圖表
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="📊 統計圖表")
        
        # 標籤頁 4: 詳細數據
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text="🔍 詳細數據")
        
        # 標籤頁 5: 報告原文
        self.raw_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.raw_frame, text="📄 報告原文")
    
    def _setup_layout(self):
        """設置界面佈局"""
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 工具列佈局
        self.toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        self.load_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.export_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.info_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 筆記本佈局
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 設置各標籤頁內容
        self._setup_timeline_tab()
        self._setup_modules_tab()
        self._setup_stats_tab()
        self._setup_details_tab()
        self._setup_raw_tab()
    
    def _setup_timeline_tab(self):
        """設置時間軸分析標籤頁"""
        # 圖表框架
        self.timeline_chart_frame = ttk.Frame(self.timeline_frame)
        self.timeline_chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 說明標籤
        info_text = "時間軸記憶體成長趨勢圖將在載入報告後顯示"
        self.timeline_info = ttk.Label(self.timeline_chart_frame, text=info_text, foreground="gray")
        self.timeline_info.pack(expand=True)
    
    def _setup_modules_tab(self):
        """設置模組分析標籤頁"""
        # 主框架
        main_modules_frame = ttk.Frame(self.modules_frame)
        main_modules_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 上半部：模組概覽
        overview_frame = ttk.LabelFrame(main_modules_frame, text="📊 模組載入概覽")
        overview_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.modules_overview_label = ttk.Label(overview_frame, text="等待載入報告...", foreground="gray")
        self.modules_overview_label.pack(pady=10)
        
        # 下半部：詳細模組清單
        details_frame = ttk.LabelFrame(main_modules_frame, text="🧩 檢測到的模組詳情")
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # 模組樹狀檢視
        self.modules_tree = ttk.Treeview(details_frame, columns=('status', 'objects', 'classes'), show='tree headings')
        self.modules_tree.heading('#0', text='模組名稱')
        self.modules_tree.heading('status', text='狀態')
        self.modules_tree.heading('objects', text='物件數量')
        self.modules_tree.heading('classes', text='類別數量')
        
        # 設置欄寬
        self.modules_tree.column('#0', width=250)
        self.modules_tree.column('status', width=100)
        self.modules_tree.column('objects', width=100)
        self.modules_tree.column('classes', width=100)
        
        # 滾動條
        modules_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.modules_tree.yview)
        self.modules_tree.configure(yscrollcommand=modules_scrollbar.set)
        
        # 佈局
        self.modules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        modules_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
    
    def _setup_stats_tab(self):
        """設置統計圖表標籤頁"""
        # 統計框架
        self.stats_chart_frame = ttk.Frame(self.stats_frame)
        self.stats_chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 說明標籤
        info_text = "記憶體變化統計圖表將在載入報告後顯示"
        self.stats_info = ttk.Label(self.stats_chart_frame, text=info_text, foreground="gray")
        self.stats_info.pack(expand=True)
        """設置統計圖表標籤頁"""
        # 統計框架
        self.stats_chart_frame = ttk.Frame(self.stats_frame)
        self.stats_chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 說明標籤
        info_text = "記憶體變化統計圖表將在載入報告後顯示"
        self.stats_info = ttk.Label(self.stats_chart_frame, text=info_text, foreground="gray")
        self.stats_info.pack(expand=True)
    
    def _setup_details_tab(self):
        """設置詳細數據標籤頁"""
        # 數據表格
        self.details_tree = ttk.Treeview(self.details_frame, columns=('timestamp', 'action', 'objects', 'change'), show='headings')
        self.details_tree.heading('timestamp', text='時間')
        self.details_tree.heading('action', text='操作')
        self.details_tree.heading('objects', text='物件總數')
        self.details_tree.heading('change', text='變化量')
        
        # 設置欄寬
        self.details_tree.column('timestamp', width=100)
        self.details_tree.column('action', width=300)
        self.details_tree.column('objects', width=100)
        self.details_tree.column('change', width=100)
        
        # 滾動條
        details_scrollbar = ttk.Scrollbar(self.details_frame, orient=tk.VERTICAL, command=self.details_tree.yview)
        self.details_tree.configure(yscrollcommand=details_scrollbar.set)
        
        # 佈局
        self.details_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
    
    def _setup_raw_tab(self):
        """設置報告原文標籤頁"""
        # 文字區域
        self.raw_text = ScrolledText(self.raw_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.raw_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def load_report(self):
        """載入 objgraph 報告檔案"""
        file_path = filedialog.askopenfilename(
            title="選擇 objgraph 報告檔案",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # 解析報告
            self.report_data = self.parser.parse_report(file_path)
            
            # 更新界面
            self._update_info_label()
            self._populate_timeline_chart()
            self._populate_modules_analysis()
            self._populate_stats_chart()
            self._populate_details_table()
            self._populate_raw_text(file_path)
            
            # 啟用匯出按鈕
            self.export_btn.config(state="normal")
            
            messagebox.showinfo("成功", f"已成功載入報告檔案：\n{os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"載入報告檔案失敗：\n{str(e)}")
    
    def _update_info_label(self):
        """更新資訊標籤"""
        if not self.report_data:
            return
        
        info = f"📊 報告時間: {self.report_data.generation_time} | " \
               f"記錄數: {self.report_data.total_records} | " \
               f"初始物件: {self.report_data.initial_objects:,} | " \
               f"最終物件: {self.report_data.final_objects:,} | " \
               f"淨變化: {self.report_data.net_change:+,} | " \
               f"檢測模組: {len(self.report_data.detected_modules)}"
        
        self.info_label.config(text=info)
    
    def _populate_timeline_chart(self):
        """繪製時間軸圖表"""
        if not self.report_data or not self.report_data.snapshots:
            return
        
        # 清除舊圖表
        for widget in self.timeline_chart_frame.winfo_children():
            widget.destroy()
        
        # 創建圖表
        fig = Figure(figsize=(12, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # 準備數據
        timestamps = []
        object_counts = []
        changes = []
        
        for snapshot in self.report_data.snapshots:
            if snapshot.timestamp != "unknown":
                timestamps.append(snapshot.timestamp)
                object_counts.append(snapshot.total_objects)
                changes.append(snapshot.object_change)
        
        if not timestamps:
            ax.text(0.5, 0.5, '無有效時間戳記數據', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=14)
        else:
            # 繪製主要趨勢線
            x_range = range(len(timestamps))
            ax.plot(x_range, object_counts, 'b-o', linewidth=2, markersize=6, label='物件總數')
            
            # 標記重要操作點
            for i, (ts, change) in enumerate(zip(timestamps, changes)):
                if change > 1000:  # 顯著變化
                    ax.annotate(f'+{change:,}', (i, object_counts[i]), 
                              textcoords="offset points", xytext=(0,10), ha='center',
                              bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
            
            # 設置圖表
            ax.set_xlabel('時間點')
            ax.set_ylabel('物件總數')
            ax.set_title('📈 記憶體物件數量時間軸變化', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # 設置 X 軸標籤
            ax.set_xticks(x_range)
            ax.set_xticklabels(timestamps, rotation=45)
            
            # 格式化 Y 軸
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        
        fig.tight_layout()
        
        # 嵌入到 Tkinter
        canvas = FigureCanvasTkAgg(fig, self.timeline_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具列
        toolbar = NavigationToolbar2Tk(canvas, self.timeline_chart_frame)
        toolbar.update()
    
    def _populate_modules_analysis(self):
        """填充模組分析數據"""
        if not self.report_data or not self.report_data.detected_modules:
            return
        
        # 更新概覽資訊
        total_modules = len(self.report_data.detected_modules)
        fully_loaded = len([m for m in self.report_data.detected_modules if m['status'] == 'fully_loaded'])
        partially_loaded = len([m for m in self.report_data.detected_modules if m['status'] == 'partially_loaded'])
        total_module_objects = sum(m['total_objects'] for m in self.report_data.detected_modules)
        
        overview_text = f"🎯 檢測到 {total_modules} 個模組 | " \
                       f"✅ 完全載入: {fully_loaded} | " \
                       f"⚠️ 部分載入: {partially_loaded} | " \
                       f"💾 模組物件總數: {total_module_objects:,}"
        
        self.modules_overview_label.config(text=overview_text, foreground="black")
        
        # 清除舊數據
        for item in self.modules_tree.get_children():
            self.modules_tree.delete(item)
        
        # 插入模組數據
        for module in self.report_data.detected_modules:
            # 狀態圖示
            status_icon = "✅" if module['status'] == 'fully_loaded' else "⚠️"
            status_text = f"{status_icon} {module['status']}"
            
            # 插入主模組節點
            module_id = self.modules_tree.insert('', 'end', 
                text=module['display_name'],
                values=(status_text, f"{module['total_objects']:,}", len(module['detected_classes']))
            )
            
            # 插入類別子節點
            for class_info in module['detected_classes']:
                self.modules_tree.insert(module_id, 'end',
                    text=f"  └─ {class_info['class_name']}",
                    values=("", f"{class_info['count']}", f"+{class_info['increase']}")
                )
        
        # 展開所有節點
        for item in self.modules_tree.get_children():
            self.modules_tree.item(item, open=True)
    
    def _populate_stats_chart(self):
        """繪製統計圖表"""
        if not self.report_data:
            return
        
        # 清除舊圖表
        for widget in self.stats_chart_frame.winfo_children():
            widget.destroy()
        
        # 創建子圖表
        fig = Figure(figsize=(14, 8), dpi=100)
        
        # 子圖 1: 變化分佈
        ax1 = fig.add_subplot(2, 2, 1)
        changes = [s.object_change for s in self.report_data.snapshots if s.object_change != 0]
        if changes:
            colors = ['green' if c > 0 else 'red' for c in changes]
            bars = ax1.bar(range(len(changes)), changes, color=colors, alpha=0.7)
            ax1.set_title('📊 記憶體變化分佈')
            ax1.set_xlabel('快照序號')
            ax1.set_ylabel('物件變化量')
            ax1.grid(True, alpha=0.3)
            
            # 添加數值標籤
            for bar, change in zip(bars, changes):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{change:+,}', ha='center', va='bottom' if change > 0 else 'top')
        
        # 子圖 2: 統計餅圖
        ax2 = fig.add_subplot(2, 2, 2)
        stats = self.report_data.summary_stats
        if stats:
            labels = ['正變化', '負變化']
            sizes = [stats.get('positive_changes', 0), stats.get('negative_changes', 0)]
            colors = ['lightgreen', 'lightcoral']
            
            if sum(sizes) > 0:
                ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax2.set_title('📈 變化類型分佈')
        
        # 子圖 3: 累積變化
        ax3 = fig.add_subplot(2, 1, 2)
        if self.report_data.snapshots:
            cumulative = []
            running_total = self.report_data.initial_objects
            
            for snapshot in self.report_data.snapshots:
                running_total += snapshot.object_change
                cumulative.append(running_total)
            
            ax3.plot(cumulative, 'g-', linewidth=2, marker='o', markersize=4)
            ax3.fill_between(range(len(cumulative)), cumulative, alpha=0.3)
            ax3.set_title('📈 累積記憶體成長趨勢')
            ax3.set_xlabel('快照序號')
            ax3.set_ylabel('累積物件總數')
            ax3.grid(True, alpha=0.3)
            ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        
        fig.tight_layout()
        
        # 嵌入到 Tkinter
        canvas = FigureCanvasTkAgg(fig, self.stats_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具列
        toolbar = NavigationToolbar2Tk(canvas, self.stats_chart_frame)
        toolbar.update()
    
    def _populate_details_table(self):
        """填充詳細數據表格"""
        if not self.report_data:
            return
        
        # 清除舊數據
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)
        
        # 插入新數據
        for snapshot in self.report_data.snapshots:
            # 格式化變化量
            change_text = f"{snapshot.object_change:+,}" if snapshot.object_change != 0 else "0"
            
            # 簡化操作描述
            action_short = snapshot.action[:50] + "..." if len(snapshot.action) > 50 else snapshot.action
            
            self.details_tree.insert('', 'end', values=(
                snapshot.timestamp,
                action_short,
                f"{snapshot.total_objects:,}",
                change_text
            ))
    
    def _populate_raw_text(self, file_path: str):
        """填充報告原文"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.raw_text.config(state=tk.NORMAL)
            self.raw_text.delete(1.0, tk.END)
            self.raw_text.insert(1.0, content)
            self.raw_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.raw_text.config(state=tk.NORMAL)
            self.raw_text.delete(1.0, tk.END)
            self.raw_text.insert(1.0, f"無法載入原文檔案：{e}")
            self.raw_text.config(state=tk.DISABLED)
    
    def export_charts(self):
        """匯出圖表"""
        if not self.report_data:
            return
        
        # 選擇匯出目錄
        export_dir = filedialog.askdirectory(title="選擇匯出目錄")
        if not export_dir:
            return
        
        try:
            # 產生檔案名稱前綴
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = f"objgraph_analysis_{timestamp}"
            
            # 匯出數據為 JSON
            json_path = os.path.join(export_dir, f"{prefix}_data.json")
            self._export_data_json(json_path)
            
            # 匯出數據為 CSV
            csv_path = os.path.join(export_dir, f"{prefix}_snapshots.csv")
            self._export_data_csv(csv_path)
            
            messagebox.showinfo("匯出完成", 
                f"已成功匯出分析結果：\n"
                f"• JSON 數據：{os.path.basename(json_path)}\n"
                f"• CSV 數據：{os.path.basename(csv_path)}")
            
        except Exception as e:
            messagebox.showerror("匯出失敗", f"匯出過程中發生錯誤：\n{str(e)}")
    
    def _export_data_json(self, file_path: str):
        """匯出數據為 JSON 格式"""
        export_data = {
            'report_info': {
                'generation_time': self.report_data.generation_time,
                'total_records': self.report_data.total_records,
                'initial_objects': self.report_data.initial_objects,
                'final_objects': self.report_data.final_objects,
                'net_change': self.report_data.net_change
            },
            'summary_stats': self.report_data.summary_stats,
            'detected_modules': self.report_data.detected_modules,
            'snapshots': [
                {
                    'timestamp': s.timestamp,
                    'action': s.action,
                    'total_objects': s.total_objects,
                    'object_change': s.object_change
                }
                for s in self.report_data.snapshots
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def _export_data_csv(self, file_path: str):
        """匯出快照數據為 CSV 格式"""
        df_data = []
        for snapshot in self.report_data.snapshots:
            df_data.append({
                'timestamp': snapshot.timestamp,
                'action': snapshot.action,
                'total_objects': snapshot.total_objects,
                'object_change': snapshot.object_change
            })
        
        df = pd.DataFrame(df_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')


def main():
    """主程式入口"""
    # 檢查命令列參數
    if len(sys.argv) > 1:
        initial_file = sys.argv[1]
        if not os.path.exists(initial_file):
            print(f"錯誤：檔案不存在 - {initial_file}")
            sys.exit(1)
    else:
        initial_file = None
    
    # 建立 GUI
    root = tk.Tk()
    app = ObjgraphAnalyzerGUI(root)
    
    # 如果有指定檔案，自動載入
    if initial_file:
        root.after(100, lambda: app._auto_load_file(initial_file))
    
    # 啟動主迴圈
    root.mainloop()


def add_auto_load_method():
    """為 GUI 類別添加自動載入方法"""
    def _auto_load_file(self, file_path: str):
        """自動載入指定檔案"""
        try:
            self.report_data = self.parser.parse_report(file_path)
            self._update_info_label()
            self._populate_timeline_chart()
            self._populate_modules_analysis()
            self._populate_stats_chart()
            self._populate_details_table()
            self._populate_raw_text(file_path)
            self.export_btn.config(state="normal")
            
            messagebox.showinfo("自動載入", f"已自動載入：\n{os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("自動載入失敗", f"無法載入檔案：\n{str(e)}")
    
    # 動態添加方法
    ObjgraphAnalyzerGUI._auto_load_file = _auto_load_file


if __name__ == "__main__":
    # 添加自動載入功能
    add_auto_load_method()
    
    print("🚀 啟動 objgraph 記憶體分析工具...")
    print("📊 功能特色：")
    print("   • 時間軸記憶體成長趨勢分析")
    print("   • 統計圖表和變化分佈")
    print("   • 詳細數據表格檢視")
    print("   • 原文報告瀏覽")
    print("   • 數據匯出 (JSON/CSV)")
    print()
    
    main()