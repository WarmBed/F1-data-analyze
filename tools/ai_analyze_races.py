#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 自動分析勝率預測 - 使用 Google Gemini API

此工具會：
1. 讀取所有比賽分析報告
2. 呼叫 Gemini API 分析每場比賽
3. 彙總所有分析結果
4. 生成改進建議總結

使用方法：
    python tools/ai_analyze_races.py

作者: F1T Dev Team
日期: 2025-12-05
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# 添加專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Google Gemini API
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("[WARN] google-generativeai 未安裝，執行: pip install google-generativeai")


@dataclass
class RaceAnalysisResult:
    """單場比賽的 AI 分析結果"""
    year: int
    race_name: str
    prediction_difficulties: List[str]
    key_turning_points: List[str]
    strategy_impact: str
    model_suggestions: List[str]
    weight_adjustments: List[str]


@dataclass
class OverallSummary:
    """所有比賽的彙總分析"""
    total_races: int
    common_prediction_issues: List[str]
    top_suggestions: List[str]
    priority_fixes: List[str]
    validation_methods: List[str]


class AIRaceAnalyzer:
    """使用 AI 分析比賽數據"""
    
    def __init__(self, api_key: str):
        """
        初始化分析器
        
        Args:
            api_key: Google Gemini API Key
        """
        self.api_key = api_key
        self.reports_dir = PROJECT_ROOT / "reports" / "race_analysis_for_llm"
        self.output_dir = PROJECT_ROOT / "reports" / "ai_analysis_results"
        self.race_analyses: List[RaceAnalysisResult] = []
        
        # 初始化 Gemini
        if GEMINI_AVAILABLE:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("[OK] Gemini API 初始化成功")
        else:
            self.model = None
    
    def get_race_reports(self) -> List[Path]:
        """取得所有比賽報告檔案"""
        if not self.reports_dir.exists():
            print(f"[ERROR] 報告目錄不存在: {self.reports_dir}")
            return []
        
        reports = list(self.reports_dir.glob("*.md"))
        # 排除 README
        reports = [r for r in reports if r.name != "README.md"]
        return sorted(reports)
    
    def analyze_single_race(self, report_path: Path) -> Optional[RaceAnalysisResult]:
        """
        分析單場比賽
        
        Args:
            report_path: 比賽報告檔案路徑
            
        Returns:
            分析結果
        """
        if not self.model:
            print("[ERROR] Gemini 模型未初始化")
            return None
        
        # 讀取報告
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # 解析年份和比賽名稱
        filename = report_path.stem  # e.g., "2024_Qatar"
        parts = filename.split("_", 1)
        year = int(parts[0])
        race_name = parts[1] if len(parts) > 1 else "Unknown"
        
        # 構建提示
        prompt = f"""你是 F1 賽車數據分析專家。請分析以下比賽數據，並以 JSON 格式回答。

{report_content}

請以以下 JSON 格式回答（只返回 JSON，不要其他文字）：

{{
    "prediction_difficulties": ["列出 2-3 個最難預測的情況，例如：NOR 從 P2 掉到 P10"],
    "key_turning_points": ["列出 1-2 個關鍵轉折點，例如：第 41 圈 NOR 進站後位置大幅下降"],
    "strategy_impact": "一句話總結進站策略對結果的影響",
    "model_suggestions": ["列出 2-3 個預測模型應該改進的地方"],
    "weight_adjustments": ["列出 1-2 個這場比賽特性需要的權重調整"]
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # 嘗試解析 JSON
            # 移除可能的 markdown 標記
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            
            result_data = json.loads(response_text)
            
            return RaceAnalysisResult(
                year=year,
                race_name=race_name,
                prediction_difficulties=result_data.get("prediction_difficulties", []),
                key_turning_points=result_data.get("key_turning_points", []),
                strategy_impact=result_data.get("strategy_impact", ""),
                model_suggestions=result_data.get("model_suggestions", []),
                weight_adjustments=result_data.get("weight_adjustments", []),
            )
            
        except json.JSONDecodeError as e:
            print(f"    [WARN] JSON 解析失敗: {e}")
            print(f"    回應: {response_text[:200]}...")
            return None
        except Exception as e:
            print(f"    [ERROR] API 呼叫失敗: {e}")
            return None
    
    def analyze_all_races(self, max_races: int = None, delay: float = 1.0):
        """
        分析所有比賽
        
        Args:
            max_races: 最多分析幾場（用於測試）
            delay: API 呼叫間隔（秒）
        """
        reports = self.get_race_reports()
        
        if max_races:
            reports = reports[:max_races]
        
        print(f"\n[分析中] 共 {len(reports)} 場比賽")
        print("=" * 60)
        
        for i, report_path in enumerate(reports, 1):
            print(f"[{i}/{len(reports)}] {report_path.stem}...", end=" ")
            
            result = self.analyze_single_race(report_path)
            
            if result:
                self.race_analyses.append(result)
                print("OK")
            else:
                print("FAILED")
            
            # 避免 API 限流
            if i < len(reports):
                time.sleep(delay)
        
        print("=" * 60)
        print(f"[完成] 成功分析 {len(self.race_analyses)}/{len(reports)} 場")
    
    def generate_summary(self) -> OverallSummary:
        """生成所有分析的彙總"""
        if not self.race_analyses:
            return OverallSummary(
                total_races=0,
                common_prediction_issues=[],
                top_suggestions=[],
                priority_fixes=[],
                validation_methods=[],
            )
        
        # 收集所有建議
        all_suggestions = []
        all_difficulties = []
        all_adjustments = []
        
        for analysis in self.race_analyses:
            all_suggestions.extend(analysis.model_suggestions)
            all_difficulties.extend(analysis.prediction_difficulties)
            all_adjustments.extend(analysis.weight_adjustments)
        
        # 統計出現頻率最高的建議
        from collections import Counter
        
        # 簡單的關鍵詞統計
        suggestion_keywords = Counter()
        for s in all_suggestions:
            # 提取關鍵詞
            keywords = ["DNF", "進站", "輪胎", "策略", "天氣", "SC", "安全車", 
                       "超車", "DRS", "差距", "位置", "排位"]
            for kw in keywords:
                if kw.lower() in s.lower():
                    suggestion_keywords[kw] += 1
        
        # 使用 AI 生成彙總
        summary_prompt = f"""你是 F1 賽車數據分析專家。以下是 {len(self.race_analyses)} 場比賽的分析結果：

## 預測困難案例
{chr(10).join(['- ' + d for d in all_difficulties[:20]])}

## 模型改進建議
{chr(10).join(['- ' + s for s in all_suggestions[:20]])}

## 權重調整建議
{chr(10).join(['- ' + a for a in all_adjustments[:20]])}

請以 JSON 格式給出彙總分析（只返回 JSON）：

{{
    "common_prediction_issues": ["列出 3-5 個最常見的預測問題"],
    "top_suggestions": ["列出最重要的 5 個改進建議，按優先級排序"],
    "priority_fixes": ["列出應該優先修復的 3 個問題"],
    "validation_methods": ["列出 2-3 個驗證改進效果的方法"]
}}
"""
        
        try:
            response = self.model.generate_content(summary_prompt)
            response_text = response.text.strip()
            
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            
            summary_data = json.loads(response_text)
            
            return OverallSummary(
                total_races=len(self.race_analyses),
                common_prediction_issues=summary_data.get("common_prediction_issues", []),
                top_suggestions=summary_data.get("top_suggestions", []),
                priority_fixes=summary_data.get("priority_fixes", []),
                validation_methods=summary_data.get("validation_methods", []),
            )
            
        except Exception as e:
            print(f"[ERROR] 彙總分析失敗: {e}")
            return OverallSummary(
                total_races=len(self.race_analyses),
                common_prediction_issues=list(suggestion_keywords.keys())[:5],
                top_suggestions=all_suggestions[:5],
                priority_fixes=["DNF 預測", "進站策略", "賽道特性"],
                validation_methods=["回測驗證", "交叉驗證"],
            )
    
    def save_results(self):
        """儲存所有分析結果"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 儲存每場比賽的分析
        races_data = [asdict(r) for r in self.race_analyses]
        races_path = self.output_dir / "individual_race_analyses.json"
        with open(races_path, 'w', encoding='utf-8') as f:
            json.dump(races_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] 個別分析: {races_path}")
        
        # 2. 生成並儲存彙總
        summary = self.generate_summary()
        summary_path = self.output_dir / "overall_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(summary), f, indent=2, ensure_ascii=False)
        print(f"[OK] 彙總分析: {summary_path}")
        
        # 3. 生成 Markdown 報告
        report = self._generate_markdown_report(summary)
        report_path = self.output_dir / "AI_ANALYSIS_REPORT.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"[OK] 完整報告: {report_path}")
        
        return report_path
    
    def _generate_markdown_report(self, summary: OverallSummary) -> str:
        """生成 Markdown 格式的完整報告"""
        report = f"""# F1 勝率預測模型 - AI 分析報告

**生成時間**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**分析比賽數**: {summary.total_races}

---

## 執行摘要

本報告使用 AI 分析了 {summary.total_races} 場 F1 比賽的預測數據，識別出預測模型的主要問題和改進方向。

---

## 一、常見預測問題

"""
        for i, issue in enumerate(summary.common_prediction_issues, 1):
            report += f"{i}. {issue}\n"
        
        report += f"""

---

## 二、改進建議（按優先級排序）

"""
        for i, suggestion in enumerate(summary.top_suggestions, 1):
            report += f"### {i}. {suggestion}\n\n"
        
        report += f"""

---

## 三、優先修復項目

| 優先級 | 問題 | 預期影響 |
|--------|------|----------|
"""
        for i, fix in enumerate(summary.priority_fixes, 1):
            report += f"| P{i} | {fix} | 高 |\n"
        
        report += f"""

---

## 四、驗證方法

"""
        for method in summary.validation_methods:
            report += f"- {method}\n"
        
        report += f"""

---

## 五、個別比賽分析摘要

| 年份 | 比賽 | 主要困難 | 建議 |
|------|------|----------|------|
"""
        for analysis in self.race_analyses[:20]:  # 只顯示前 20 場
            difficulty = analysis.prediction_difficulties[0] if analysis.prediction_difficulties else "-"
            suggestion = analysis.model_suggestions[0] if analysis.model_suggestions else "-"
            report += f"| {analysis.year} | {analysis.race_name} | {difficulty[:30]}... | {suggestion[:30]}... |\n"
        
        report += f"""

---

## 六、下一步行動

1. **立即修復**: 根據「優先修復項目」開始實施
2. **驗證效果**: 使用建議的驗證方法測試改進
3. **迭代優化**: 重新運行分析，確認改進效果

---

*此報告由 AI 自動生成，建議人工審核後再實施*
"""
        
        return report


def main():
    """主函數"""
    print("=" * 60)
    print("F1 勝率預測 - AI 自動分析工具")
    print("=" * 60)
    
    if not GEMINI_AVAILABLE:
        print("[ERROR] 請先安裝 google-generativeai:")
        print("        pip install google-generativeai")
        return
    
    # API Key
    API_KEY = "AIzaSyCqL57ei4-CxJ6jY_rddPh262mkSqMBy90"
    
    analyzer = AIRaceAnalyzer(api_key=API_KEY)
    
    # 檢查報告是否存在
    reports = analyzer.get_race_reports()
    if not reports:
        print("[ERROR] 找不到比賽報告，請先執行:")
        print("        python tools/generate_race_analysis_for_llm.py")
        return
    
    print(f"[INFO] 找到 {len(reports)} 場比賽報告")
    
    # 分析所有比賽
    analyzer.analyze_all_races(delay=1.5)  # 1.5 秒間隔避免限流
    
    # 儲存結果
    if analyzer.race_analyses:
        report_path = analyzer.save_results()
        
        print("\n" + "=" * 60)
        print("分析完成！")
        print("=" * 60)
        print(f"完整報告: {report_path}")
    else:
        print("[ERROR] 沒有成功分析任何比賽")


if __name__ == "__main__":
    main()
