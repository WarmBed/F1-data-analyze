import json

# 載入訓練報告
with open('reports/fp2_race_ml_training_report_v2.json', encoding='utf-8') as f:
    report = json.load(f)

tracks = sorted(report.get('track_results', {}).keys())

print(f'訓練的賽道數量: {len(tracks)}\n')
for i, track in enumerate(tracks, 1):
    result = report['track_results'][track]
    status = '✓' if result.get('success') else '✗'
    print(f'{i}. {status} {track}')

print(f'\n❓ 是否包含 Yas Island: {"Yas Island" in tracks or "Yas_Island" in tracks}')

# 檢查失敗的賽道
failed_tracks = [t for t, r in report['track_results'].items() if not r.get('success')]
if failed_tracks:
    print(f'\n❌ 訓練失敗的賽道 ({len(failed_tracks)} 個):')
    for track in failed_tracks:
        error = report['track_results'][track].get('error', 'Unknown error')
        print(f'  - {track}: {error}')
