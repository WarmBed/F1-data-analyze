#!/usr/bin/env python3
"""顯示訓練結果摘要"""
import json

d = json.load(open('config/tire_degradation_database.json', encoding='utf-8'))

print('=' * 70)
print('Cappello & Hoegh 2025 輪胎衰退模型訓練結果')
print('=' * 70)
print()
print(f"{'賽道':<15} {'SOFT':>10} {'MEDIUM':>10} {'HARD':>10}  備註")
print('-' * 70)

for circuit_name, data in sorted(d['circuits'].items()):
    if not data.get('trained_from_data'):
        continue
    
    opt = data.get('optimal_stint_length', {})
    deg = data.get('base_degradation', {})
    
    soft = opt.get('SOFT', '-')
    med = opt.get('MEDIUM', '-')
    hard = opt.get('HARD', '-')
    
    # 檢查 SOFT < MEDIUM < HARD 邏輯
    note = ''
    if isinstance(soft, int) and isinstance(med, int) and soft > med:
        note = 'SOFT > MEDIUM !'
    if isinstance(med, int) and isinstance(hard, int) and med > hard:
        note = 'MEDIUM > HARD !'
    
    print(f'{circuit_name:<15} {str(soft):>10} {str(med):>10} {str(hard):>10}  {note}')

print()
print('說明: 最佳換胎圈數 = sqrt(2 × pit_loss / degradation_rate)')
