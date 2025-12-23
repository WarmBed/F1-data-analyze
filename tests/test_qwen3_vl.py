"""
測試 Qwen3-VL 視覺語言模型
用於 F1 賽道圖片和遙測數據分析
"""

import subprocess
import json
from pathlib import Path

def test_qwen3_vl_text_only():
    """測試 1: 純文本分析（不需要圖片）"""
    print("\n[測試 1] Qwen3-VL 純文本分析")
    print("=" * 60)
    
    prompt = """
    分析以下 F1 Monaco 預測失敗案例：
    
    問題：
    - v3.5 Spearman 0.524 vs v3.4 0.607 (-13.7%)
    - 街道賽道特性，改進率僅 +1.59%
    - LEC 預測第 3，實際第 6
    - HAM 預測第 4，實際第 9
    
    請建議 3 個新特徵來改善街道賽道預測。
    """
    
    try:
        result = subprocess.run(
            ['ollama', 'run', 'qwen3-vl:8b', prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )
        
        print("[Qwen3-VL 回覆]:")
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"[錯誤] {result.stderr}")
            return False
            
        return True
        
    except subprocess.TimeoutExpired:
        print("[錯誤] 執行逾時")
        return False
    except FileNotFoundError:
        print("[錯誤] Ollama 未安裝或 qwen3-vl:8b 模型未下載")
        print("[提示] 請執行: ollama pull qwen3-vl:8b")
        return False


def test_qwen3_vl_with_image(image_path: str):
    """測試 2: 圖片 + 文本分析"""
    print("\n[測試 2] Qwen3-VL 圖片分析")
    print("=" * 60)
    
    if not Path(image_path).exists():
        print(f"[錯誤] 圖片不存在: {image_path}")
        return False
    
    prompt = """
    請分析這張 F1 賽道圖：
    1. 賽道類型（街道/永久賽道/混合）
    2. 高速彎道 vs 低速彎道比例
    3. 主要超車點
    4. 為什麼這條賽道預測困難？
    """
    
    try:
        # Ollama 視覺模型需要使用 API 或特殊語法
        # 這裡示範 API 調用方式
        result = subprocess.run(
            ['ollama', 'run', 'qwen3-vl:8b', '--image', image_path, prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120
        )
        
        print("[Qwen3-VL 視覺分析]:")
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"[錯誤] {result.stderr}")
            return False
            
        return True
        
    except subprocess.TimeoutExpired:
        print("[錯誤] 執行逾時（圖片分析較慢）")
        return False


def compare_models():
    """測試 3: 比較不同視覺模型"""
    print("\n[測試 3] 視覺模型比較")
    print("=" * 60)
    
    models = [
        ('qwen3-vl:8b', '最新最強（中文優）'),
        ('llava:13b', '完全免費開源'),
        ('moondream:1.8b', '輕量快速'),
        ('llama3.2-vision:11b', 'Meta 官方')
    ]
    
    prompt = "簡單介紹你的視覺分析能力，適合分析 F1 賽道圖嗎？"
    
    results = {}
    
    for model_name, description in models:
        print(f"\n[測試] {model_name} - {description}")
        print("-" * 60)
        
        try:
            result = subprocess.run(
                ['ollama', 'run', model_name, prompt],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"[成功] {model_name}")
                print(result.stdout[:200] + "...")  # 只顯示前 200 字
                results[model_name] = "可用"
            else:
                print(f"[失敗] {model_name} - 模型未安裝")
                results[model_name] = "未安裝"
                
        except subprocess.TimeoutExpired:
            print(f"[逾時] {model_name}")
            results[model_name] = "逾時"
        except FileNotFoundError:
            print(f"[錯誤] Ollama 未安裝")
            break
    
    print("\n[模型可用性總結]:")
    print("=" * 60)
    for model, status in results.items():
        print(f"{model:30s} -> {status}")
    
    return results


def install_recommended_models():
    """推薦安裝腳本"""
    print("\n[推薦安裝] F1 分析最佳組合")
    print("=" * 60)
    
    recommendations = [
        {
            'name': 'Qwen3 14B',
            'command': 'ollama pull qwen3:14b',
            'size': '~14GB',
            'use': '文本推理分析'
        },
        {
            'name': 'Qwen3-VL 8B',
            'command': 'ollama pull qwen3-vl:8b',
            'size': '~6GB',
            'use': '圖片分析（賽道圖/遙測圖）'
        },
        {
            'name': 'DeepSeek-R1 14B',
            'command': 'ollama pull deepseek-r1:14b',
            'size': '~14GB',
            'use': '深度推理（Monaco/Netherlands 診斷）'
        },
        {
            'name': 'LLaVA 13B（免費替代）',
            'command': 'ollama pull llava:13b',
            'size': '~8GB',
            'use': '免費視覺分析'
        }
    ]
    
    print("\n推薦安裝順序：")
    for i, model in enumerate(recommendations, 1):
        print(f"\n{i}. {model['name']} ({model['size']})")
        print(f"   用途: {model['use']}")
        print(f"   指令: {model['command']}")
    
    print("\n總計需要空間: ~42GB（安裝全部）")
    print("最小配置: Qwen3 14B + Qwen3-VL 8B (~20GB)")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  Qwen3-VL 視覺語言模型測試")
    print("=" * 60)
    
    # 測試 1: 純文本分析
    success1 = test_qwen3_vl_text_only()
    
    # 測試 2: 圖片分析（如果有圖片）
    # test_image = "path/to/monaco_track.png"
    # if Path(test_image).exists():
    #     success2 = test_qwen3_vl_with_image(test_image)
    
    # 測試 3: 模型比較
    available_models = compare_models()
    
    # 顯示安裝推薦
    install_recommended_models()
    
    print("\n" + "=" * 60)
    print("  測試完成")
    print("=" * 60)
    
    # 總結
    if success1:
        print("\n[結論] Qwen3-VL 8B 可用於 F1 文本分析")
        print("[下一步] 建議同時安裝 Qwen3 14B（更強的純文本推理）")
    else:
        print("\n[提示] 請先執行: ollama pull qwen3-vl:8b")
