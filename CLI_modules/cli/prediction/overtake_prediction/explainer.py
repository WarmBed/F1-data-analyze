#!/usr/bin/env python3
"""
F84: 超車預測 LLM 解說器
Overtake Prediction LLM Explainer

使用規則引擎或 LLM 生成超車預測的自然語言解說。
預設使用規則引擎，可選擇使用 OpenAI/Anthropic/Ollama。
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import os


@dataclass
class OvertakeExplanation:
    """超車預測解說結果"""
    explanation: str  # 主要解說文字
    key_points: List[str]  # 關鍵要點
    recommendation: str  # 建議
    confidence_note: str  # 信心度說明
    language: str = "zh-TW"  # 輸出語言


class RuleBasedExplainer:
    """規則引擎解說器（不需要 LLM API）"""
    
    def __init__(self, language: str = "zh-TW"):
        self.language = language
        
    def explain_prediction(self, 
                          prediction: Dict[str, Any],
                          attacker: str = None,
                          defender: str = None,
                          context: Dict[str, Any] = None) -> OvertakeExplanation:
        """
        生成超車預測的自然語言解說
        
        Args:
            prediction: F83 預測結果 (包含 probability, confidence, key_factors)
            attacker: 進攻者車手代碼
            defender: 防守者車手代碼
            context: 額外上下文 (gap, tyre_diff, etc.)
            
        Returns:
            OvertakeExplanation: 解說結果
        """
        probability = prediction.get('probability', 0.5)
        confidence = prediction.get('confidence', 'MEDIUM')
        key_factors = prediction.get('key_factors', [])
        
        context = context or {}
        gap = context.get('gap_seconds', 1.0)
        tyre_diff = context.get('tyre_age_diff', 0)
        race_progress = context.get('race_progress', 0.5)
        drs_available = gap < 1.0
        
        # 生成主要解說
        explanation = self._generate_explanation(
            probability, confidence, key_factors,
            attacker, defender, gap, tyre_diff, drs_available, race_progress
        )
        
        # 生成關鍵要點
        key_points = self._generate_key_points(
            probability, drs_available, tyre_diff, gap
        )
        
        # 生成建議
        recommendation = self._generate_recommendation(
            probability, confidence, drs_available, tyre_diff
        )
        
        # 生成信心度說明
        confidence_note = self._generate_confidence_note(confidence, probability)
        
        return OvertakeExplanation(
            explanation=explanation,
            key_points=key_points,
            recommendation=recommendation,
            confidence_note=confidence_note,
            language=self.language
        )
    
    def _generate_explanation(self, prob: float, conf: str, factors: List[str],
                             attacker: str, defender: str, gap: float,
                             tyre_diff: int, drs: bool, progress: float) -> str:
        """生成主要解說文字"""
        attacker = attacker or "進攻者"
        defender = defender or "防守者"
        
        # 機率區間判斷
        if prob >= 0.7:
            prob_desc = "很高"
            outcome = "很可能成功超車"
        elif prob >= 0.5:
            prob_desc = "中等偏高"
            outcome = "有機會完成超車"
        elif prob >= 0.3:
            prob_desc = "中等"
            outcome = "超車難度較大，但仍有可能"
        else:
            prob_desc = "較低"
            outcome = "超車難度很大，成功機率有限"
        
        # DRS 描述
        drs_desc = "在 DRS 區域內" if drs else "不在 DRS 區域"
        
        # 輪胎優勢描述
        if tyre_diff > 5:
            tyre_desc = f"擁有明顯的輪胎優勢 (對手輪胎老 {tyre_diff} 圈)"
        elif tyre_diff > 0:
            tyre_desc = f"擁有輕微輪胎優勢 (對手輪胎老 {tyre_diff} 圈)"
        elif tyre_diff < -5:
            tyre_desc = f"處於輪胎劣勢 (自己輪胎較老)"
        else:
            tyre_desc = "輪胎狀況相近"
        
        # 比賽階段描述
        if progress >= 0.8:
            stage_desc = "比賽已進入尾聲，時間緊迫"
        elif progress >= 0.5:
            stage_desc = "比賽進入後半段"
        else:
            stage_desc = "比賽尚在前半段"
        
        explanation = (
            f"分析 {attacker} 對 {defender} 的超車機會：\n"
            f"預測機率為 {prob:.1%}（{prob_desc}），{outcome}。\n"
            f"目前間距為 {gap:.2f} 秒，{drs_desc}。\n"
            f"{tyre_desc}。{stage_desc}。"
        )
        
        if factors:
            factors_str = "、".join(factors[:3])
            explanation += f"\n主要影響因素：{factors_str}。"
        
        return explanation
    
    def _generate_key_points(self, prob: float, drs: bool, 
                            tyre_diff: int, gap: float) -> List[str]:
        """生成關鍵要點列表"""
        points = []
        
        # 機率評估
        if prob >= 0.6:
            points.append(f"超車機率達 {prob:.1%}，屬於高機率情況")
        elif prob >= 0.4:
            points.append(f"超車機率為 {prob:.1%}，屬於中等風險")
        else:
            points.append(f"超車機率僅 {prob:.1%}，風險較高")
        
        # DRS 評估
        if drs:
            points.append("DRS 可用，提供重要速度優勢")
        else:
            if gap < 1.5:
                points.append("接近 DRS 區間，需要縮小差距")
            else:
                points.append("距離 DRS 區間較遠")
        
        # 輪胎評估
        if tyre_diff > 3:
            points.append(f"輪胎優勢明顯 (+{tyre_diff} 圈)")
        elif tyre_diff < -3:
            points.append(f"輪胎劣勢明顯 ({tyre_diff} 圈)")
        
        # 間距評估
        if gap < 0.5:
            points.append("間距極小，已進入攻擊範圍")
        elif gap < 1.0:
            points.append("間距適中，可發動攻擊")
        else:
            points.append("間距較大，需先縮小差距")
        
        return points
    
    def _generate_recommendation(self, prob: float, conf: str,
                                 drs: bool, tyre_diff: int) -> str:
        """生成策略建議"""
        if prob >= 0.7 and conf == "HIGH":
            if drs:
                return "建議積極進攻，利用 DRS 優勢在直線末端發動攻擊"
            else:
                return "建議找機會進入 DRS 區間後發動攻擊"
        elif prob >= 0.5:
            if tyre_diff > 3:
                return "建議利用輪胎優勢持續施壓，等待對手失誤"
            else:
                return "建議謹慎評估時機，避免輕率嘗試"
        elif prob >= 0.3:
            return "建議保持壓力但避免冒險，等待更好的機會"
        else:
            return "建議保守策略，專注於保護位置或等待進站換胎"
    
    def _generate_confidence_note(self, conf: str, prob: float) -> str:
        """生成信心度說明"""
        if conf == "HIGH":
            return f"模型對此預測有高度信心（機率 {prob:.1%}），可作為重要參考依據"
        elif conf == "MEDIUM":
            return f"模型對此預測有中等信心（機率 {prob:.1%}），建議結合現場情況判斷"
        else:
            return f"模型對此預測信心度較低（機率 {prob:.1%}），結果僅供參考"


class LLMExplainer:
    """LLM 解說器（支援 Ollama 本地端）"""
    
    SUPPORTED_PROVIDERS = ["ollama", "openai", "anthropic"]
    
    def __init__(self, provider: str = "ollama", model: str = None):
        self.provider = provider.lower()
        if self.provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"不支援的 LLM 提供者: {provider}")
        
        self.model = model or self._default_model()
        self.client = None
        self._init_client()
    
    def _default_model(self) -> str:
        """取得預設模型"""
        defaults = {
            "ollama": "qwen3:8b",  # 本地 Ollama 預設使用 qwen3
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-haiku-20240307"
        }
        return defaults.get(self.provider, "qwen3:8b")
    
    def _init_client(self):
        """初始化 LLM 客戶端"""
        try:
            if self.provider == "openai":
                from openai import OpenAI
                self.client = OpenAI()
            elif self.provider == "anthropic":
                from anthropic import Anthropic
                self.client = Anthropic()
            elif self.provider == "ollama":
                import ollama
                self.client = ollama
        except ImportError as e:
            print(f"[WARNING] 無法載入 {self.provider} 客戶端: {e}")
            self.client = None
    
    def explain_prediction(self, 
                          prediction: Dict[str, Any],
                          attacker: str = None,
                          defender: str = None,
                          context: Dict[str, Any] = None) -> OvertakeExplanation:
        """使用 LLM 生成解說"""
        if self.client is None:
            # 回退到規則引擎
            fallback = RuleBasedExplainer()
            return fallback.explain_prediction(prediction, attacker, defender, context)
        
        prompt = self._build_prompt(prediction, attacker, defender, context)
        response = self._call_llm(prompt)
        
        return OvertakeExplanation(
            explanation=response,
            key_points=[],  # LLM 回應中可能包含
            recommendation="",  # LLM 回應中可能包含
            confidence_note="",
            language="zh-TW"
        )
    
    def _build_prompt(self, prediction: Dict, attacker: str, 
                     defender: str, context: Dict) -> str:
        """建構 LLM 提示"""
        context = context or {}
        return f"""你是一位專業的 F1 賽車分析師。請分析以下超車預測並提供簡潔的中文解說：

車手對決：{attacker or '進攻者'} vs {defender or '防守者'}

預測數據：
- 超車機率：{prediction.get('probability', 0.5):.1%}
- 信心等級：{prediction.get('confidence', 'MEDIUM')}
- 關鍵因素：{', '.join(prediction.get('key_factors', []))}

情境參數：
- 間距：{context.get('gap_seconds', 1.0):.2f} 秒
- 輪胎差異：{context.get('tyre_age_diff', 0)} 圈
- 比賽進度：{context.get('race_progress', 0.5):.0%}

請提供：
1. 情勢分析（2-3句）
2. 關鍵優劣勢
3. 策略建議

回答請簡潔專業，使用繁體中文。"""
    
    def _call_llm(self, prompt: str) -> str:
        """調用 LLM API"""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif self.provider == "ollama":
                print(f"[INFO] 正在調用 Ollama ({self.model})，請稍候...")
                response = self.client.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    options={
                        'num_predict': 500,  # 限制輸出 token 數
                        'temperature': 0.7
                    }
                )
                return response['message']['content']
            
        except Exception as e:
            print(f"[ERROR] LLM 調用失敗: {e}")
            print("[INFO] 回退到規則引擎...")
            # 回退到規則引擎
            fallback = RuleBasedExplainer()
            return fallback.explain_prediction({}, None, None, {}).explanation


def run_f84_explanation(prediction: Dict[str, Any] = None,
                        attacker: str = None,
                        defender: str = None,
                        gap: float = 1.0,
                        tyre_diff: int = 0,
                        race_progress: float = 0.5,
                        use_llm: bool = True,  # 預設使用 LLM（Ollama）
                        llm_provider: str = "ollama",  # 預設使用本地 Ollama
                        llm_model: str = None,  # 可指定模型
                        verbose: bool = True) -> Dict[str, Any]:
    """
    執行 F84 超車預測解說
    
    Args:
        prediction: F83 的預測結果，如果未提供則使用預設值
        attacker: 進攻者車手代碼
        defender: 防守者車手代碼
        gap: 間距（秒）
        tyre_diff: 輪胎年齡差
        race_progress: 比賽進度 (0-1)
        use_llm: 是否使用 LLM（預設使用規則引擎）
        llm_provider: LLM 提供者 (openai/anthropic/ollama)
        verbose: 詳細輸出
        
    Returns:
        Dict: 解說結果
    """
    print("=" * 70)
    print("F84: 超車預測 LLM 解說器")
    print("=" * 70)
    
    # 如果沒有提供預測結果，先執行 F83
    if prediction is None:
        print("[INFO] 未提供預測結果，先執行 F83 預測...")
        from CLI_modules.cli.prediction.overtake_prediction.predictor import run_f83_prediction
        result = run_f83_prediction(
            attacker=attacker,
            defender=defender,
            gap=gap,
            tyre_diff=tyre_diff,
            race_progress=race_progress,
            verbose=False
        )
        if result.get('success'):
            prediction = result.get('prediction', {})
        else:
            return {
                'success': False,
                'message': 'F83 預測失敗，無法生成解說'
            }
    
    # 建構上下文
    context = {
        'gap_seconds': gap,
        'tyre_age_diff': tyre_diff,
        'race_progress': race_progress
    }
    
    # 選擇解說器
    if use_llm:
        model_info = f" (model: {llm_model})" if llm_model else ""
        print(f"[INFO] 使用 LLM 解說器 ({llm_provider}{model_info})")
        try:
            explainer = LLMExplainer(provider=llm_provider, model=llm_model)
            if explainer.client is None:
                print(f"[WARNING] {llm_provider} 客戶端初始化失敗，回退到規則引擎")
                explainer = RuleBasedExplainer()
        except Exception as e:
            print(f"[WARNING] LLM 初始化失敗: {e}，回退到規則引擎")
            explainer = RuleBasedExplainer()
    else:
        print("[INFO] 使用規則引擎解說器")
        explainer = RuleBasedExplainer()
    
    # 生成解說
    explanation = explainer.explain_prediction(prediction, attacker, defender, context)
    
    if verbose:
        print("\n" + "=" * 50)
        print("解說結果")
        print("=" * 50)
        print(explanation.explanation)
        print("\n關鍵要點:")
        for point in explanation.key_points:
            print(f"  - {point}")
        print(f"\n策略建議: {explanation.recommendation}")
        print(f"\n信心度說明: {explanation.confidence_note}")
    
    return {
        'success': True,
        'message': '解說生成完成',
        'explanation': {
            'text': explanation.explanation,
            'key_points': explanation.key_points,
            'recommendation': explanation.recommendation,
            'confidence_note': explanation.confidence_note,
            'language': explanation.language
        },
        'prediction_used': prediction,
        'use_llm': use_llm,
        'llm_provider': llm_provider if use_llm else None
    }


if __name__ == "__main__":
    import sys
    
    # 測試解說器
    test_prediction = {
        'probability': 0.558,
        'confidence': 'MEDIUM',
        'key_factors': ['DRS zone available', 'DRS range']
    }
    
    # 檢查是否使用 LLM (預設使用 Ollama)
    use_llm = "--no-llm" not in sys.argv
    
    result = run_f84_explanation(
        prediction=test_prediction,
        attacker="VER",
        defender="HAM",
        gap=0.8,
        tyre_diff=5,
        race_progress=0.6,
        use_llm=use_llm,
        llm_provider="ollama",
        llm_model="qwen3:8b",
        verbose=True
    )
    
    print("\n" + "=" * 50)
    print("JSON 結果:")
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
