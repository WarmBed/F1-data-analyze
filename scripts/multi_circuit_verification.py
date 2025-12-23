"""
多賽道彎道一致性驗證 - 擴展測試腳本

在美國站驗證成功後，此腳本可測試算法在其他賽道的表現。
支援批次測試多個賽道，生成綜合對比報告。
"""

from corner_consistency_verification import CornerConsistencyVerifier
import json
from pathlib import Path
from datetime import datetime

# 測試賽道清單
TEST_CIRCUITS = [
    {
        'name': 'United States',
        'years': [2022, 2023, 2024, 2025],
        'expected_corners': 6,  # 預期識別的主要彎道數
        'circuit_type': 'Mixed'  # 賽道類型
    },
    {
        'name': 'Japan',
        'years': [2022, 2023, 2024, 2025],
        'expected_corners': 18,  # 鈴鹿的彎道數
        'circuit_type': 'Technical'
    },
    {
        'name': 'Italy',  # Monza
        'years': [2022, 2023, 2024, 2025],
        'expected_corners': 11,
        'circuit_type': 'High-Speed'
    },
    {
        'name': 'Monaco',
        'years': [2022, 2023, 2024, 2025],
        'expected_corners': 19,
        'circuit_type': 'Street Circuit'
    },
    {
        'name': 'Singapore',
        'years': [2022, 2023, 2024],  # 2025 尚未舉辦
        'expected_corners': 23,
        'circuit_type': 'Street Circuit'
    }
]


def run_multi_circuit_verification():
    """執行多賽道驗證"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║     多賽道彎道識別一致性驗證                                   ║
    ║     Multi-Circuit Corner Detection Verification               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    verifier = CornerConsistencyVerifier()
    all_results = {}
    
    for circuit in TEST_CIRCUITS:
        print(f"\n{'='*70}")
        print(f"🏁 測試賽道: {circuit['name']}")
        print(f"   類型: {circuit['circuit_type']}")
        print(f"   預期彎道數: {circuit['expected_corners']}")
        print(f"{'='*70}")
        
        try:
            # 執行驗證
            report = verifier.compare_multi_year(
                years=circuit['years'],
                race_name=circuit['name']
            )
            
            if report:
                # 儲存報告
                verifier.save_report(report)
                verifier.generate_visualization(report)
                
                # 收集結果統計
                analysis = report['consistency_analysis']
                all_results[circuit['name']] = {
                    'circuit_type': circuit['circuit_type'],
                    'expected_corners': circuit['expected_corners'],
                    'detected_corners': list(analysis['corner_counts'].values()),
                    'consistency_score': analysis['consistency_score'],
                    'matching_rate': analysis['matching_rate'],
                    'success': True
                }
                
                print(f"\n✅ {circuit['name']} 驗證完成")
            else:
                all_results[circuit['name']] = {
                    'circuit_type': circuit['circuit_type'],
                    'success': False,
                    'error': 'No data available'
                }
                print(f"\n❌ {circuit['name']} 驗證失敗")
                
        except Exception as e:
            print(f"\n❌ {circuit['name']} 驗證錯誤: {e}")
            all_results[circuit['name']] = {
                'circuit_type': circuit['circuit_type'],
                'success': False,
                'error': str(e)
            }
    
    # 生成綜合報告
    generate_comprehensive_report(all_results)


def generate_comprehensive_report(all_results):
    """生成綜合對比報告"""
    print(f"\n{'='*70}")
    print(f"📊 綜合驗證結果")
    print(f"{'='*70}\n")
    
    # 統計表格
    print(f"{'賽道':<20} {'類型':<15} {'一致性':<10} {'匹配率':<10} {'狀態'}")
    print(f"{'-'*70}")
    
    successful = 0
    total = len(all_results)
    
    for circuit_name, result in all_results.items():
        if result['success']:
            consistency = f"{result['consistency_score']:.1f}%"
            matching = f"{result['matching_rate']:.1f}%"
            status = "✅"
            successful += 1
        else:
            consistency = "N/A"
            matching = "N/A"
            status = f"❌ {result.get('error', 'Unknown')}"
        
        circuit_type = result.get('circuit_type', 'Unknown')
        print(f"{circuit_name:<20} {circuit_type:<15} {consistency:<10} {matching:<10} {status}")
    
    print(f"{'-'*70}")
    print(f"\n總結: {successful}/{total} 賽道驗證成功 ({successful/total*100:.1f}%)")
    
    # 儲存 JSON 摘要
    output_dir = Path('json/corner_consistency')
    summary_file = output_dir / f"multi_circuit_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'verification_date': datetime.now().isoformat(),
            'total_circuits': total,
            'successful_circuits': successful,
            'success_rate': successful / total * 100,
            'results': all_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 綜合報告已儲存: {summary_file}")


def quick_single_circuit_test(circuit_name: str, years: list):
    """快速單一賽道測試"""
    verifier = CornerConsistencyVerifier()
    report = verifier.compare_multi_year(years, circuit_name)
    
    if report:
        verifier.save_report(report)
        verifier.generate_visualization(report)
        return True
    return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 命令列模式：指定單一賽道
        # 用法: python multi_circuit_verification.py Japan
        circuit_name = sys.argv[1]
        years = [2022, 2023, 2024, 2025]
        
        print(f"執行單一賽道測試: {circuit_name}")
        success = quick_single_circuit_test(circuit_name, years)
        
        if success:
            print(f"✅ {circuit_name} 測試完成")
        else:
            print(f"❌ {circuit_name} 測試失敗")
    else:
        # 執行完整多賽道驗證
        run_multi_circuit_verification()
