#!/usr/bin/env python3
"""
降雨分析圖表工具類
Rain Analysis Chart Utilities
專門處理雙Y軸天氣數據視覺化
"""

import numpy as np
import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.figure import Figure

class WeatherChartFormatter:
    """天氣圖表格式化工具"""
    
    @staticmethod
    def setup_dual_axis_chart(figure, title="天氣狀況分析"):
        """設置雙Y軸圖表基本結構"""
        figure.clear()
        figure.patch.set_facecolor('black')
        
        # 創建主軸 (溫度)
        ax_temp = figure.add_subplot(111)
        ax_temp.set_facecolor('black')
        
        # 創建次軸 (風速)
        ax_wind = ax_temp.twinx()
        
        # 設置標籤
        ax_temp.set_xlabel('時間 (分鐘)', color='white', fontsize=12)
        ax_temp.set_ylabel('溫度 (°C)', color='#FF6B6B', fontsize=12)
        ax_wind.set_ylabel('風速 (km/h)', color='#4ECDC4', fontsize=12)
        
        # 設置標題
        ax_temp.set_title(title, color='white', fontsize=14, pad=20)
        
        # 設置軸顏色
        ax_temp.tick_params(axis='x', colors='white')
        ax_temp.tick_params(axis='y', colors='#FF6B6B')
        ax_wind.tick_params(axis='y', colors='#4ECDC4')
        
        # 設置網格
        ax_temp.grid(True, alpha=0.3, color='white')
        
        # 設置邊框顏色
        for spine in ax_temp.spines.values():
            spine.set_color('white')
        for spine in ax_wind.spines.values():
            spine.set_color('white')
        
        return ax_temp, ax_wind
    
    @staticmethod
    def prepare_time_data(weather_data):
        """準備時間數據"""
        if 'Time' in weather_data.columns:
            time_data = []
            for i, time_val in enumerate(weather_data['Time']):
                if isinstance(time_val, timedelta):
                    time_data.append(time_val.total_seconds() / 60)  # 轉換為分鐘
                elif pd.isna(time_val):
                    time_data.append(i * 1)  # 假設每分鐘一個數據點
                else:
                    try:
                        # 嘗試轉換其他時間格式
                        if hasattr(time_val, 'total_seconds'):
                            time_data.append(time_val.total_seconds() / 60)
                        else:
                            time_data.append(i * 1)
                    except:
                        time_data.append(i * 1)
        else:
            # 如果沒有時間欄位，使用索引作為時間
            time_data = list(range(len(weather_data)))
        
        return time_data
    
    @staticmethod
    def plot_temperature_line(ax_temp, time_data, temp_data):
        """繪製溫度曲線"""
        if len(temp_data) > 0 and not temp_data.dropna().empty:
            valid_indices = ~temp_data.isna()
            valid_time = [time_data[i] for i, valid in enumerate(valid_indices) if valid and i < len(time_data)]
            valid_temp = temp_data.dropna().values
            
            if len(valid_time) > 0 and len(valid_temp) > 0:
                # 確保時間和溫度數據長度一致
                min_len = min(len(valid_time), len(valid_temp))
                valid_time = valid_time[:min_len]
                valid_temp = valid_temp[:min_len]
                
                ax_temp.plot(valid_time, valid_temp, 
                           color='#FF6B6B', linewidth=2.5, 
                           label='氣溫', marker='o', markersize=4,
                           markeredgecolor='white', markeredgewidth=0.5)
                return True
        return False
    
    @staticmethod
    def plot_wind_speed_line(ax_wind, time_data, wind_data):
        """繪製風速曲線"""
        if len(wind_data) > 0 and not wind_data.dropna().empty:
            valid_indices = ~wind_data.isna()
            valid_time = [time_data[i] for i, valid in enumerate(valid_indices) if valid and i < len(time_data)]
            valid_wind = wind_data.dropna().values
            
            if len(valid_time) > 0 and len(valid_wind) > 0:
                # 確保時間和風速數據長度一致
                min_len = min(len(valid_time), len(valid_wind))
                valid_time = valid_time[:min_len]
                valid_wind = valid_wind[:min_len]
                
                ax_wind.plot(valid_time, valid_wind, 
                           color='#4ECDC4', linewidth=2.5, 
                           label='風速', marker='s', markersize=4,
                           markeredgecolor='white', markeredgewidth=0.5)
                return True
        return False
    
    @staticmethod
    def mark_rain_periods(ax_temp, time_data, rainfall_data):
        """標記降雨時段"""
        rain_periods = []
        rain_markers = []
        
        try:
            # 識別降雨時段
            in_rain = False
            start_time = None
            
            for i, (time_val, rain_val) in enumerate(zip(time_data, rainfall_data)):
                if pd.notna(rain_val) and rain_val > 0:  # 有降雨
                    if not in_rain:
                        start_time = time_val
                        in_rain = True
                    # 記錄降雨標記點
                    rain_markers.append(time_val)
                else:  # 無降雨
                    if in_rain and start_time is not None:
                        rain_periods.append((start_time, time_val))
                        in_rain = False
            
            # 處理最後一個降雨期間
            if in_rain and start_time is not None:
                rain_periods.append((start_time, time_data[-1]))
            
            # 在圖表上標記降雨時段
            for i, (start, end) in enumerate(rain_periods):
                # 添加半透明藍色背景
                ax_temp.axvspan(start, end, alpha=0.2, color='lightblue', 
                               label='降雨時段' if i == 0 else "")
            
            # 在降雨點添加標記
            if rain_markers:
                y_lim = ax_temp.get_ylim()
                y_pos = y_lim[1] - (y_lim[1] - y_lim[0]) * 0.05  # 圖表頂部5%位置
                
                for time_val in rain_markers[::max(1, len(rain_markers)//20)]:  # 最多顯示20個標記避免擁擠
                    ax_temp.text(time_val, y_pos, '🌧️', 
                               fontsize=12, ha='center', va='top', 
                               color='blue', alpha=0.8)
            
            return len(rain_periods)
            
        except Exception as e:
            print(f"標記降雨時段時發生錯誤: {e}")
            return 0
    
    @staticmethod
    def add_legend(ax_temp, ax_wind):
        """添加圖例"""
        lines1, labels1 = ax_temp.get_legend_handles_labels()
        lines2, labels2 = ax_wind.get_legend_handles_labels()
        
        if lines1 or lines2:
            ax_temp.legend(lines1 + lines2, labels1 + labels2, 
                         loc='upper left', facecolor='black', 
                         edgecolor='white', labelcolor='white',
                         framealpha=0.8)
    
    @staticmethod
    def format_axes(ax_temp, ax_wind, time_data):
        """格式化軸顯示"""
        # 設置X軸範圍
        if time_data:
            ax_temp.set_xlim(min(time_data), max(time_data))
        
        # 設置Y軸範圍 (給一些餘量)
        temp_lim = ax_temp.get_ylim()
        wind_lim = ax_wind.get_ylim()
        
        if temp_lim[1] > temp_lim[0]:
            margin = (temp_lim[1] - temp_lim[0]) * 0.1
            ax_temp.set_ylim(temp_lim[0] - margin, temp_lim[1] + margin)
        
        if wind_lim[1] > wind_lim[0]:
            margin = (wind_lim[1] - wind_lim[0]) * 0.1
            ax_wind.set_ylim(wind_lim[0] - margin, wind_lim[1] + margin)

class RainAnalysisPlotter:
    """降雨分析專用繪圖器"""
    
    def __init__(self, figure):
        self.figure = figure
        self.formatter = WeatherChartFormatter()
    
    def plot_complete_weather_analysis(self, weather_data, title="天氣狀況分析"):
        """繪製完整的天氣分析圖表"""
        if weather_data is None or weather_data.empty:
            return self.plot_no_data_message()
        
        try:
            # 設置雙Y軸圖表
            ax_temp, ax_wind = self.formatter.setup_dual_axis_chart(self.figure, title)
            
            # 準備時間數據
            time_data = self.formatter.prepare_time_data(weather_data)
            
            # 繪製資料線條
            temp_plotted = False
            wind_plotted = False
            
            # 溫度數據
            if 'AirTemp' in weather_data.columns:
                temp_plotted = self.formatter.plot_temperature_line(
                    ax_temp, time_data, weather_data['AirTemp'])
            
            # 風速數據  
            if 'WindSpeed' in weather_data.columns:
                wind_plotted = self.formatter.plot_wind_speed_line(
                    ax_wind, time_data, weather_data['WindSpeed'])
            
            # 標記降雨時段
            rain_periods_count = 0
            if 'Rainfall' in weather_data.columns:
                rain_periods_count = self.formatter.mark_rain_periods(
                    ax_temp, time_data, weather_data['Rainfall'])
            
            # 格式化軸顯示
            self.formatter.format_axes(ax_temp, ax_wind, time_data)
            
            # 添加圖例
            self.formatter.add_legend(ax_temp, ax_wind)
            
            # 添加數據摘要文本
            self.add_data_summary(ax_temp, weather_data, rain_periods_count)
            
            return {
                "success": True,
                "temp_plotted": temp_plotted,
                "wind_plotted": wind_plotted,
                "rain_periods": rain_periods_count,
                "data_points": len(weather_data)
            }
            
        except Exception as e:
            print(f"繪製天氣分析時發生錯誤: {e}")
            return self.plot_error_message(f"繪製錯誤: {str(e)}")
    
    def add_data_summary(self, ax, weather_data, rain_periods_count):
        """添加數據摘要"""
        summary_text = []
        
        if 'AirTemp' in weather_data.columns:
            temp_data = weather_data['AirTemp'].dropna()
            if not temp_data.empty:
                avg_temp = temp_data.mean()
                min_temp = temp_data.min()
                max_temp = temp_data.max()
                summary_text.append(f"溫度: {avg_temp:.1f}°C (範圍: {min_temp:.1f}°C - {max_temp:.1f}°C)")
        
        if 'WindSpeed' in weather_data.columns:
            wind_data = weather_data['WindSpeed'].dropna()
            if not wind_data.empty:
                avg_wind = wind_data.mean()
                max_wind = wind_data.max()
                summary_text.append(f"風速: 平均 {avg_wind:.1f} km/h (最大 {max_wind:.1f} km/h)")
        
        if rain_periods_count > 0:
            summary_text.append(f"降雨時段: {rain_periods_count} 個")
        else:
            summary_text.append("降雨時段: 無")
        
        if summary_text:
            summary = "\n".join(summary_text)
            ax.text(0.02, 0.98, summary, transform=ax.transAxes,
                   verticalalignment='top', horizontalalignment='left',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='black', 
                            edgecolor='white', alpha=0.8),
                   fontsize=10, color='white')
    
    def plot_no_data_message(self):
        """顯示無數據消息"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('black')
        
        ax.text(0.5, 0.5, '暫無天氣數據\n請先載入比賽數據', 
               transform=ax.transAxes,
               horizontalalignment='center', verticalalignment='center',
               fontsize=16, color='white',
               bbox=dict(boxstyle='round,pad=1', facecolor='#333333', 
                        edgecolor='white', alpha=0.8))
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        return {"success": False, "message": "無數據"}
    
    def plot_error_message(self, error_text):
        """顯示錯誤消息"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('black')
        
        ax.text(0.5, 0.5, f'❌ 錯誤\n{error_text}', 
               transform=ax.transAxes,
               horizontalalignment='center', verticalalignment='center',
               fontsize=14, color='red',
               bbox=dict(boxstyle='round,pad=1', facecolor='#333333', 
                        edgecolor='red', alpha=0.8))
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        return {"success": False, "message": error_text}

# 使用範例
"""
# 在你的圖表組件中使用:
from modules.gui.rain_chart_utils import RainAnalysisPlotter

# 初始化
plotter = RainAnalysisPlotter(your_matplotlib_figure)

# 繪製圖表
result = plotter.plot_complete_weather_analysis(weather_data, "2025 Japan GP - 天氣分析")

if result["success"]:
    print(f"成功繪製圖表: 溫度={result['temp_plotted']}, 風速={result['wind_plotted']}, 降雨時段={result['rain_periods']}")
else:
    print(f"繪製失敗: {result['message']}")
"""
