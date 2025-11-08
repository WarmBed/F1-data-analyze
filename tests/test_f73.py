"""測試 Function 73 賽道分類"""
from CLI_modules.cli.analyzer.track_classification_analyzer import run_track_classification_analysis

print("=" * 60)
print("開始執行 Function 73 - 賽道分類分析")
print("=" * 60)

result = run_track_classification_analysis()

print("\n" + "=" * 60)
print("執行結果")
print("=" * 60)
print(f"Success: {result.get('success')}")
print(f"Message: {result.get('message')}")

metadata = result.get('metadata', {})
print(f"\nTotal Tracks: {metadata.get('total_tracks')}")
print(f"N Clusters: {metadata.get('n_clusters')}")
print(f"Session: {metadata.get('session')}")

if result.get('success'):
    print(f"\n輸出檔案:")
    output_files = result.get('output_files', {})
    for key, path in output_files.items():
        print(f"  {key}: {path}")
