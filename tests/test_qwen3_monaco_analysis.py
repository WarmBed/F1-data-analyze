"""
測試 Qwen3 8B 對 Monaco 預測問題的分析能力
使用本地 Ollama 模型進行特徵工程建議
"""

import subprocess
import json
import time
from pathlib import Path

def run_ollama_model(model_name: str, prompt: str, timeout: int = 120) -> dict:
    """
    執行 Ollama 模型推理
    
    Args:
        model_name: 模型名稱（qwen3:8b 或 qwen3-vl:8b）
        prompt: 輸入 prompt
        timeout: 執行逾時秒數
    
    Returns:
        dict: {'success': bool, 'output': str, 'time': float}
    """
    print(f"\n[啟動] {model_name}")
    print(f"[Prompt] {prompt[:100]}...")
    
    ollama_path = Path.home() / "AppData/Local/Programs/Ollama/ollama.exe"
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [str(ollama_path), 'run', model_name, prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=timeout
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"[成功] 執行時間: {elapsed_time:.1f}秒")
            return {
                'success': True,
                'output': result.stdout.strip(),
                'time': elapsed_time
            }
        else:
            print(f"[錯誤] {result.stderr}")
            return {
                'success': False,
                'output': result.stderr,
                'time': elapsed_time
            }
            
    except subprocess.TimeoutExpired:
        print(f"[逾時] 超過 {timeout} 秒")
        return {
            'success': False,
            'output': f"執行逾時（>{timeout}秒）",
            'time': timeout
        }
    except Exception as e:
        print(f"[異常] {str(e)}")
        return {
            'success': False,
            'output': str(e),
            'time': 0
        }


def test_monaco_feature_engineering():
    """測試 1: Monaco 特徵工程建議"""
    
    print("\n" + "="*80)
    print("  測試 1: Monaco 街道賽道特徵工程分析")
    print("="*80)
    
    prompt = """你是 F1 機器學習專家。請分析以下 Monaco 預測問題並建議新特徵：

## 問題描述
- 賽道: Monaco（街道賽道）
- v3.5 Spearman: 0.524 vs v3.4: 0.607（退化 -13.7%）
- Top5 準確率: 60%（3/5 正確）
- 改進率: +1.59%（非常低）
- 錯誤案例: LEC 預測第 3，實際第 6；HAM 預測第 4，實際第 9

## 現有 20 個特徵
基礎 14 特徵: max_speed, avg_speed, min_speed, sector_1/2/3_time, throttle_pct, brake_pct, gear_changes, drs_usage, tire_type_encoded, compound_encoded, track_temp, air_temp

改進率 6 特徵: improvement_rate_max_speed, improvement_rate_avg_speed, improvement_rate_throttle, improvement_rate_brake, improvement_rate_gear_changes, improvement_rate_drs

## 你的任務
建議 3-5 個新特徵來改善 Monaco 街道賽道預測。格式如下：

1. **特徵名稱**: corner_density
   - 計算方式: 單圈彎道數量 / 賽道長度
   - 預期效果: 捕捉街道賽道高彎道密度特性
   - Monaco 預期值: 19 彎 / 3.337 km = 5.69

請提供具體、可實現的特徵建議。"""

    result = run_ollama_model('qwen3:8b', prompt, timeout=120)
    
    if result['success']:
        print("\n[Qwen3 回覆]:")
        print("-" * 80)
        print(result['output'])
        print("-" * 80)
        
        # 儲存結果
        output_file = Path("monaco_feature_engineering_result.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"執行時間: {result['time']:.1f}秒\n")
            f.write(f"Prompt:\n{prompt}\n\n")
            f.write(f"回覆:\n{result['output']}\n")
        
        print(f"\n[已儲存] {output_file}")
        
    return result


def test_netherlands_extreme_improvement():
    """測試 2: Netherlands 極端改進率分析"""
    
    print("\n" + "="*80)
    print("  測試 2: Netherlands 極端改進率診斷")
    print("="*80)
    
    prompt = """你是 F1 數據科學家。請診斷 Netherlands 預測不穩定的原因並建議解決方案：

## 問題描述
- 賽道: Netherlands（Zandvoort）
- 2024 極端改進率: +11.579s (+13.99%）
- v3.5 MAE: 2.149s（較高）
- Top5 準確率: 60%（僅中等）
- 改進率特徵權重: 未能完全處理極端值

## 數據特徵
- 2022-2023: 正常改進 +1~3%
- 2024: 異常改進 +13.99%（極端值）
- 2025 預測: 模型無法適應極端變化

## 你的任務
1. 解釋為何會出現 +13.99% 極端改進率
2. 建議 2-3 個處理極端值的方法
3. 推薦新特徵來建模這種極端變化

請提供技術性的解決方案。"""

    result = run_ollama_model('qwen3:8b', prompt, timeout=90)
    
    if result['success']:
        print("\n[Qwen3 回覆]:")
        print("-" * 80)
        print(result['output'])
        print("-" * 80)
        
        # 儲存結果
        output_file = Path("netherlands_extreme_analysis_result.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"執行時間: {result['time']:.1f}秒\n")
            f.write(f"Prompt:\n{prompt}\n\n")
            f.write(f"回覆:\n{result['output']}\n")
        
        print(f"\n[已儲存] {output_file}")
        
    return result


def test_quick_introduction():
    """測試 3: 快速自我介紹（驗證模型功能）"""
    
    print("\n" + "="*80)
    print("  測試 3: 模型快速驗證")
    print("="*80)
    
    prompt = "你好，請用 3 句話介紹你自己，並說明你能如何協助 F1 數據分析。"
    
    result = run_ollama_model('qwen3:8b', prompt, timeout=30)
    
    if result['success']:
        print("\n[Qwen3 回覆]:")
        print("-" * 80)
        print(result['output'])
        print("-" * 80)
        
    return result


if __name__ == '__main__':
    print("\n" + "="*80)
    print("  Qwen3 8B Monaco/Netherlands 分析測試")
    print("="*80)
    
    # 測試 3: 快速驗證（先確認模型能運行）
    result_intro = test_quick_introduction()
    
    if not result_intro['success']:
        print("\n[錯誤] 模型無法啟動，測試終止")
        exit(1)
    
    # 測試 1: Monaco 特徵工程
    result_monaco = test_monaco_feature_engineering()
    
    # 測試 2: Netherlands 極端值
    result_netherlands = test_netherlands_extreme_improvement()
    
    # 總結
    print("\n" + "="*80)
    print("  測試總結")
    print("="*80)
    
    results = {
        '快速驗證': result_intro,
        'Monaco 特徵工程': result_monaco,
        'Netherlands 極端值': result_netherlands
    }
    
    for test_name, result in results.items():
        status = "✅ 成功" if result['success'] else "❌ 失敗"
        time_str = f"{result['time']:.1f}秒" if result['success'] else "N/A"
        print(f"{test_name:20s} {status:10s} 執行時間: {time_str}")
    
    total_time = sum(r['time'] for r in results.values() if r['success'])
    print(f"\n總執行時間: {total_time:.1f}秒")
    
    if all(r['success'] for r in results.values()):
        print("\n[完成] 所有測試通過！Qwen3 8B 可用於 F1 分析")
    else:
        print("\n[警告] 部分測試失敗，請檢查模型狀態")
