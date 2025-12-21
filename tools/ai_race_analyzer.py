#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
勝率預測 AI 自動分析工具

使用 Google Gemini 2.0 Flash 分析所有比賽報告，
並生成改進建議總結。

使用方法：
    python tools/ai_race_analyzer.py

作者: F1T Dev Team
日期: 2025-12-05
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# 添加專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Google AI
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("[WARN] google-generativeai 未安裝，執行: pip install google-generativeai")


class AIRaceAnalyzer:
    """AI 比賽分析器"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-lite"):
        """
        初始化分析器
        
        Args:
            api_key: Google AI API Key
            model_name: 模型名稱 (預設使用 lite 版本配額較寬鬆)
        """
        if not GENAI_AVAILABLE:
            raise ImportError("請安裝 google-generativeai: pip install google-generativeai")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.reports_dir = PROJECT_ROOT / "reports" / "race_analysis_for_llm"
        self.output_dir = PROJECT_ROOT / "reports" / "ai_analysis_results"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 分析結果
        self.race_analyses: List[Dict[str, Any]] = []
        
    def get_race_reports(self) -> List[Path]:
        """取得所有比賽報告"""
        reports = list(self.reports_dir.glob("20*.md"))
        return sorted(reports)
    
    def analyze_single_race(self, report_path: Path, max_retries: int = 3) -> Dict[str, Any]:
        """
        分析單場比賽
        
        Args:
            report_path: 報告檔案路徑
            max_retries: 最大重試次數
            
        Returns:
            分析結果字典
        """
        race_name = report_path.stem
        print(f"  分析中: {race_name}...", end="", flush=True)
        
        # 讀取報告
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # 建立分析提示
        prompt = f"""你是一位 F1 賽車數據分析專家。請分析以下比賽數據，並回答問題。

{report_content}

請用 JSON 格式回答以下問題（直接輸出 JSON，不要加 markdown 標記）：

{{
    "race": "{race_name}",
    "prediction_difficulty": "easy/medium/hard",
    "hardest_to_predict_drivers": [
        {{"driver": "XXX", "reason": "為什麼難預測"}}
    ],
    "key_turning_points": [
        {{"lap": 數字, "event": "發生了什麼", "impact": "對結果的影響"}}
    ],
    "dnf_drivers": ["車手代碼"],
    "big_gainers": [
        {{"driver": "XXX", "positions_gained": 數字, "likely_reason": "原因"}}
    ],
    "big_losers": [
        {{"driver": "XXX", "positions_lost": 數字, "likely_reason": "原因"}}
    ],
    "strategy_observations": "進站/輪胎策略觀察",
    "model_suggestions": [
        "針對這場比賽，預測模型應該改進的具體建議"
    ]
}}
"""
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                result_text = response.text.strip()
                
                # 清理 JSON（移除可能的 markdown 標記）
                if result_text.startswith("```"):
                    lines = result_text.split("\n")
                    result_text = "\n".join(lines[1:-1])
                
                # 解析 JSON
                result = json.loads(result_text)
                result["success"] = True
                return result
                
            except json.JSONDecodeError as e:
                print(f" [JSON錯誤]", end="")
                return {
                    "race": race_name,
                    "success": False,
                    "error": f"JSON 解析失敗: {str(e)}",
                    "raw_response": response.text if 'response' in dir() else ""
                }
            except Exception as e:
                error_str = str(e)
                if "429" in error_str and attempt < max_retries - 1:
                    # 從錯誤訊息中提取等待時間
                    wait_time = 60  # 預設等待 60 秒
                    if "retry_delay" in error_str:
                        try:
                            import re
                            match = re.search(r'retry in (\d+)', error_str)
                            if match:
                                wait_time = int(match.group(1)) + 5
                        except:
                            pass
                    print(f" [等待{wait_time}秒重試]", end="", flush=True)
                    time.sleep(wait_time)
                    continue
                else:
                    return {
                        "race": race_name,
                        "success": False,
                        "error": str(e)[:100]
                    }
        
        return {
            "race": race_name,
            "success": False,
            "error": "達到最大重試次數"
        }
    
    def analyze_all_races(self, delay: float = 2.0) -> List[Dict]:
        """
        分析所有比賽
        
        Args:
            delay: 每次 API 呼叫之間的延遲（秒）
            
        Returns:
            所有分析結果
        """
        reports = self.get_race_reports()
        print(f"\n[開始分析] 共 {len(reports)} 場比賽")
        print("=" * 60)
        
        for i, report_path in enumerate(reports, 1):
            print(f"[{i}/{len(reports)}]", end="")
            result = self.analyze_single_race(report_path)
            self.race_analyses.append(result)
            
            if result.get("success"):
                print(f" ✓")
            else:
                print(f" ✗ {result.get('error', 'Unknown error')[:50]}")
            
            # 延遲避免 API 限制
            if i < len(reports):
                time.sleep(delay)
        
        print("=" * 60)
        print(f"[完成] 成功: {sum(1 for r in self.race_analyses if r.get('success'))}/{len(reports)}")
        
        return self.race_analyses
    
    def generate_summary(self) -> str:
        """生成總結報告"""
        
        successful = [r for r in self.race_analyses if r.get("success")]
        
        if not successful:
            return "沒有成功的分析結果"
        
        # 統計
        all_suggestions = []
        all_dnf_drivers = []
        all_gainers = []
        all_losers = []
        difficulty_counts = {"easy": 0, "medium": 0, "hard": 0}
        
        for result in successful:
            # 收集建議
            suggestions = result.get("model_suggestions", [])
            all_suggestions.extend(suggestions)
            
            # 收集 DNF
            dnf = result.get("dnf_drivers", [])
            all_dnf_drivers.extend(dnf)
            
            # 收集大進步/大退步
            gainers = result.get("big_gainers", [])
            all_gainers.extend(gainers)
            
            losers = result.get("big_losers", [])
            all_losers.extend(losers)
            
            # 難度統計
            diff = result.get("prediction_difficulty", "medium")
            if diff in difficulty_counts:
                difficulty_counts[diff] += 1
        
        # 統計最常出現的建議
        suggestion_counts = {}
        for s in all_suggestions:
            # 簡化建議文字
            key = s[:50] if len(s) > 50 else s
            suggestion_counts[key] = suggestion_counts.get(key, 0) + 1
        
        # 統計 DNF 車手
        dnf_counts = {}
        for d in all_dnf_drivers:
            dnf_counts[d] = dnf_counts.get(d, 0) + 1
        
        # 統計大進步車手
        gainer_counts = {}
        for g in all_gainers:
            driver = g.get("driver", "?")
            gainer_counts[driver] = gainer_counts.get(driver, 0) + 1
        
        # 統計大退步車手
        loser_counts = {}
        for l in all_losers:
            driver = l.get("driver", "?")
            loser_counts[driver] = loser_counts.get(driver, 0) + 1
        
        # 生成總結
        summary = f"""# F1 勝率預測模型 - AI 分析總結報告

## 分析概覽
- 分析比賽數: {len(successful)} / {len(self.race_analyses)}
- 分析日期: 2025-12-05
- 使用模型: Gemini 2.0 Flash

## 預測難度分佈

| 難度 | 比賽數 | 比例 |
|------|--------|------|
| Easy | {difficulty_counts['easy']} | {difficulty_counts['easy']/len(successful)*100:.1f}% |
| Medium | {difficulty_counts['medium']} | {difficulty_counts['medium']/len(successful)*100:.1f}% |
| Hard | {difficulty_counts['hard']} | {difficulty_counts['hard']/len(successful)*100:.1f}% |

## DNF 高風險車手

以下車手在分析期間 DNF 次數最多，模型應該加入 DNF 風險因子：

| 車手 | DNF 次數 |
|------|----------|
"""
        for driver, count in sorted(dnf_counts.items(), key=lambda x: -x[1])[:10]:
            summary += f"| {driver} | {count} |\n"
        
        summary += f"""

## 經常大幅進步的車手

這些車手經常從後面追上來，可能需要特別的預測調整：

| 車手 | 大進步次數 |
|------|------------|
"""
        for driver, count in sorted(gainer_counts.items(), key=lambda x: -x[1])[:10]:
            summary += f"| {driver} | {count} |\n"
        
        summary += f"""

## 經常大幅退步的車手

這些車手經常從前面掉下來：

| 車手 | 大退步次數 |
|------|------------|
"""
        for driver, count in sorted(loser_counts.items(), key=lambda x: -x[1])[:10]:
            summary += f"| {driver} | {count} |\n"
        
        summary += f"""

## AI 建議彙總

以下是 AI 分析所有比賽後提出的改進建議（按出現頻率排序）：

"""
        for i, (suggestion, count) in enumerate(sorted(suggestion_counts.items(), key=lambda x: -x[1])[:20], 1):
            summary += f"{i}. **[出現 {count} 次]** {suggestion}\n"
        
        summary += f"""

## 詳細改進建議

基於以上分析，以下是具體的模型改進方向：

### 1. DNF 預測
- 需要加入車隊可靠性因子
- 高 DNF 風險車手: {', '.join(list(dnf_counts.keys())[:5])}

### 2. 位置變動預測
- 某些車手（如 {', '.join(list(gainer_counts.keys())[:3])}）經常大幅進步
- 可能與輪胎管理、比賽節奏有關

### 3. 難預測比賽特徵
- 高難度比賽通常有：多次 SC、雨戰、街道賽事故
- 建議加入「比賽混亂度」因子

### 4. 賽道特定調整
- 不同賽道的超車難度需要更精確的校準
- 街道賽和高速賽道的預測邏輯應該不同

---

## 每場比賽詳細分析

"""
        for result in successful:
            race = result.get("race", "Unknown")
            difficulty = result.get("prediction_difficulty", "?")
            summary += f"### {race}\n"
            summary += f"- 難度: {difficulty}\n"
            
            hardest = result.get("hardest_to_predict_drivers", [])
            if hardest:
                summary += f"- 最難預測: "
                summary += ", ".join([f"{h['driver']}({h['reason'][:30]})" for h in hardest[:3]])
                summary += "\n"
            
            suggestions = result.get("model_suggestions", [])
            if suggestions:
                summary += f"- 建議: {suggestions[0][:80]}...\n" if len(suggestions[0]) > 80 else f"- 建議: {suggestions[0]}\n"
            
            summary += "\n"
        
        return summary
    
    def save_results(self):
        """儲存分析結果"""
        # 儲存原始 JSON
        json_path = self.output_dir / "all_races_analysis.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.race_analyses, f, indent=2, ensure_ascii=False)
        print(f"[OK] JSON 結果: {json_path}")
        
        # 儲存總結報告
        summary = self.generate_summary()
        summary_path = self.output_dir / "analysis_summary.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"[OK] 總結報告: {summary_path}")
        
        return json_path, summary_path


def main():
    print("=" * 60)
    print("F1 勝率預測 - AI 自動分析工具")
    print("使用 Gemini 2.0 Flash")
    print("=" * 60)
    
    # API Key
    API_KEY = "AIzaSyCqL57ei4-CxJ6jY_rddPh262mkSqMBy90"
    
    # 初始化分析器
    try:
        analyzer = AIRaceAnalyzer(api_key=API_KEY, model_name="gemini-2.0-flash-exp")
    except Exception as e:
        print(f"[ERROR] 初始化失敗: {e}")
        return
    
    # 檢查報告數量
    reports = analyzer.get_race_reports()
    print(f"\n找到 {len(reports)} 場比賽報告")
    
    if not reports:
        print("[ERROR] 沒有找到比賽報告，請先執行 generate_race_analysis_for_llm.py")
        return
    
    # 分析所有比賽
    print("\n開始 AI 分析（每場比賽間隔 2 秒避免 API 限制）...")
    analyzer.analyze_all_races(delay=2.0)
    
    # 儲存結果
    print("\n儲存分析結果...")
    json_path, summary_path = analyzer.save_results()
    
    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)
    print(f"1. 詳細 JSON: {json_path}")
    print(f"2. 總結報告: {summary_path}")
    print("\n請查看總結報告獲取改進建議。")


if __name__ == "__main__":
    main()
