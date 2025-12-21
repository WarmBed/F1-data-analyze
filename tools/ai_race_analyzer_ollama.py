#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
勝率預測 AI 自動分析工具 - Ollama 本地版

使用本地 Ollama (qwen3:8b) 分析所有比賽報告，
完全免費、無限制、無需網路。

使用方法：
    python tools/ai_race_analyzer_ollama.py

作者: F1T Dev Team
日期: 2025-12-05
"""

import os
import sys
import io
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Any

# 修復 Windows 終端編碼問題
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class OllamaRaceAnalyzer:
    """使用 Ollama 的比賽分析器"""
    
    def __init__(self, model_name: str = "qwen3:8b", base_url: str = "http://localhost:11434"):
        """
        初始化分析器
        
        Args:
            model_name: Ollama 模型名稱
            base_url: Ollama API 地址
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.reports_dir = PROJECT_ROOT / "reports" / "race_analysis_for_llm"
        self.output_dir = PROJECT_ROOT / "reports" / "ai_analysis_results"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 分析結果
        self.race_analyses: List[Dict[str, Any]] = []
        
    def check_ollama(self) -> bool:
        """檢查 Ollama 是否運行"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_race_reports(self) -> List[Path]:
        """取得所有比賽報告"""
        reports = list(self.reports_dir.glob("20*.md"))
        return sorted(reports)
    
    def analyze_single_race(self, report_path: Path) -> Dict[str, Any]:
        """
        分析單場比賽
        
        Args:
            report_path: 報告檔案路徑
            
        Returns:
            分析結果字典
        """
        race_name = report_path.stem
        
        # 讀取報告
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # 建立分析提示 - 簡化版本以適應本地模型
        prompt = f"""/no_think
你是 F1 賽車數據分析專家。請分析以下比賽數據。

{report_content}

請用 JSON 格式回答（只輸出 JSON，不要其他文字）：

{{
    "race": "{race_name}",
    "prediction_difficulty": "easy/medium/hard",
    "hardest_to_predict": ["車手1", "車手2"],
    "dnf_drivers": ["車手代碼"],
    "big_position_changes": [
        {{"driver": "XXX", "change": "+5 或 -3", "reason": "簡短原因"}}
    ],
    "key_observations": "一句話總結這場比賽的特點",
    "model_suggestions": ["改進建議1", "改進建議2"]
}}
"""
        
        # 重試機制
        max_retries = 3
        response = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 1000,
                        }
                    },
                    timeout=300  # 增加到 5 分鐘，模型載入需要時間
                )
                break  # 成功就跳出重試
            except requests.exceptions.Timeout:
                last_error = f"超時 (嘗試 {attempt + 1}/{max_retries})"
                print(f"      重試中... ({attempt + 1}/{max_retries})")
                time.sleep(5)
                continue
            except requests.exceptions.ConnectionError as e:
                last_error = f"連線失敗: {str(e)[:50]}"
                print(f"      連線失敗，重試中... ({attempt + 1}/{max_retries})")
                time.sleep(10)
                continue
        
        # 如果所有重試都失敗
        if response is None:
            return {
                "race": race_name,
                "success": False,
                "error": last_error or "所有重試都失敗"
            }
        
        try:
            if response.status_code != 200:
                return {
                    "race": race_name,
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
            
            result_text = response.json().get("response", "").strip()
            
            # 嘗試提取 JSON
            # 找到第一個 { 和最後一個 }
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_text = result_text[start:end]
                result = json.loads(json_text)
                result["success"] = True
                return result
            else:
                return {
                    "race": race_name,
                    "success": False,
                    "error": "無法找到 JSON",
                    "raw_response": result_text[:500]
                }
                
        except json.JSONDecodeError as e:
            return {
                "race": race_name,
                "success": False,
                "error": f"JSON 解析失敗: {str(e)}",
                "raw_response": result_text[:500] if result_text else ""
            }
        except Exception as e:
            return {
                "race": race_name,
                "success": False,
                "error": str(e)
            }
    
    def warmup_model(self) -> bool:
        """預熱模型，確保已載入到記憶體"""
        print("[暖機] 載入模型中...", end=" ", flush=True)
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": "Say 'ready' in one word.",
                    "stream": False,
                    "options": {
                        "num_predict": 10,
                    }
                },
                timeout=600  # 10 分鐘超時
            )
            if response.status_code == 200:
                print("✓ 模型已就緒")
                return True
            else:
                print(f"✗ HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ {str(e)[:50]}")
            return False
    
    def analyze_all_races(self, max_races: int = None) -> List[Dict]:
        """
        分析所有比賽
        
        Args:
            max_races: 最多分析幾場（None = 全部）
            
        Returns:
            所有分析結果
        """
        reports = self.get_race_reports()
        if max_races:
            reports = reports[:max_races]
        
        print(f"\n[開始分析] 共 {len(reports)} 場比賽")
        print(f"使用模型: {self.model_name}")
        print("=" * 60)
        
        # 預熱模型
        if not self.warmup_model():
            print("警告: 模型預熱失敗，但將繼續嘗試分析")
        print("=" * 60)
        
        for i, report_path in enumerate(reports, 1):
            race_name = report_path.stem
            print(f"[{i}/{len(reports)}] {race_name}...", end=" ", flush=True)
            
            start_time = time.time()
            result = self.analyze_single_race(report_path)
            elapsed = time.time() - start_time
            
            self.race_analyses.append(result)
            
            if result.get("success"):
                print(f"✓ ({elapsed:.1f}s)")
            else:
                print(f"✗ {result.get('error', 'Unknown')[:40]}")
        
        print("=" * 60)
        success_count = sum(1 for r in self.race_analyses if r.get('success'))
        print(f"[完成] 成功: {success_count}/{len(reports)}")
        
        return self.race_analyses
    
    def generate_summary(self) -> str:
        """生成總結報告"""
        
        successful = [r for r in self.race_analyses if r.get("success")]
        
        if not successful:
            return "沒有成功的分析結果"
        
        # 收集統計
        all_suggestions = []
        all_dnf = []
        all_changes = []
        difficulty_counts = {"easy": 0, "medium": 0, "hard": 0}
        
        for result in successful:
            suggestions = result.get("model_suggestions", [])
            all_suggestions.extend(suggestions)
            
            dnf = result.get("dnf_drivers", [])
            all_dnf.extend(dnf)
            
            changes = result.get("big_position_changes", [])
            all_changes.extend(changes)
            
            diff = result.get("prediction_difficulty", "medium")
            if diff in difficulty_counts:
                difficulty_counts[diff] += 1
        
        # 統計 DNF 車手
        dnf_counts = {}
        for d in all_dnf:
            dnf_counts[d] = dnf_counts.get(d, 0) + 1
        
        # 統計建議
        suggestion_counts = {}
        for s in all_suggestions:
            key = s[:60] if len(s) > 60 else s
            suggestion_counts[key] = suggestion_counts.get(key, 0) + 1
        
        # 生成總結
        summary = f"""# F1 勝率預測模型 - AI 分析總結報告

## 分析概覽
- 分析比賽數: {len(successful)} / {len(self.race_analyses)}
- 分析日期: 2025-12-05
- 使用模型: {self.model_name} (Ollama 本地)

## 預測難度分佈

| 難度 | 比賽數 | 比例 |
|------|--------|------|
| Easy | {difficulty_counts['easy']} | {difficulty_counts['easy']/max(len(successful),1)*100:.1f}% |
| Medium | {difficulty_counts['medium']} | {difficulty_counts['medium']/max(len(successful),1)*100:.1f}% |
| Hard | {difficulty_counts['hard']} | {difficulty_counts['hard']/max(len(successful),1)*100:.1f}% |

## DNF 高風險車手 (需加入 DNF 預測因子)

| 車手 | DNF 次數 |
|------|----------|
"""
        for driver, count in sorted(dnf_counts.items(), key=lambda x: -x[1])[:10]:
            summary += f"| {driver} | {count} |\n"
        
        summary += f"""

## AI 建議彙總 (按出現頻率)

"""
        for i, (suggestion, count) in enumerate(sorted(suggestion_counts.items(), key=lambda x: -x[1])[:15], 1):
            summary += f"{i}. **[{count}次]** {suggestion}\n"
        
        summary += f"""

## 每場比賽摘要

"""
        for result in successful:
            race = result.get("race", "Unknown")
            difficulty = result.get("prediction_difficulty", "?")
            obs = result.get("key_observations", "")
            summary += f"### {race}\n"
            summary += f"- 難度: {difficulty}\n"
            summary += f"- 觀察: {obs}\n"
            
            dnf = result.get("dnf_drivers", [])
            if dnf:
                summary += f"- DNF: {', '.join(dnf)}\n"
            
            summary += "\n"
        
        summary += """
---

## 總結建議

根據 AI 分析所有比賽，預測模型的主要改進方向：

1. **加入 DNF 預測因子** - 根據車隊可靠性和車手歷史
2. **調整賽道權重** - 不同賽道的超車難度需要更精確
3. **考慮比賽混亂度** - SC、雨戰等因素的影響
4. **車手特性建模** - 某些車手擅長逆轉，某些容易掉位
"""
        
        return summary
    
    def save_results(self):
        """儲存分析結果"""
        # 儲存原始 JSON
        json_path = self.output_dir / "all_races_analysis_ollama.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.race_analyses, f, indent=2, ensure_ascii=False)
        print(f"[OK] JSON 結果: {json_path}")
        
        # 儲存總結報告
        summary = self.generate_summary()
        summary_path = self.output_dir / "analysis_summary_ollama.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"[OK] 總結報告: {summary_path}")
        
        return json_path, summary_path


def main():
    print("=" * 60)
    print("F1 勝率預測 - AI 自動分析工具 (Ollama 本地版)")
    print("=" * 60)
    
    # 初始化分析器
    analyzer = OllamaRaceAnalyzer(model_name="qwen3:8b")
    
    # 檢查 Ollama
    print("\n檢查 Ollama 服務...", end=" ")
    if not analyzer.check_ollama():
        print("✗")
        print("[ERROR] Ollama 未運行！請先啟動 Ollama:")
        print("  ollama serve")
        return
    print("✓")
    
    # 檢查報告
    reports = analyzer.get_race_reports()
    print(f"找到 {len(reports)} 場比賽報告")
    
    if not reports:
        print("[ERROR] 沒有找到比賽報告")
        return
    
    # 分析所有比賽
    print("\n開始 AI 分析（本地運行，無需等待）...")
    analyzer.analyze_all_races()
    
    # 儲存結果
    print("\n儲存分析結果...")
    json_path, summary_path = analyzer.save_results()
    
    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)
    print(f"1. 詳細 JSON: {json_path}")
    print(f"2. 總結報告: {summary_path}")


if __name__ == "__main__":
    main()
