"""
執行 CLI -f13 並將輸出保存到文件
"""
import subprocess
import os

output_file = "cli_f13_output.txt"

print("執行: python f1_analysis_modular_main.py -f 13 -y 2024 -r Japan -s R -d VER -d2 LEC")
print(f"輸出將保存到: {output_file}")
print("=" * 80)

with open(output_file, 'w', encoding='utf-8') as f:
    result = subprocess.run(
        ["python", "f1_analysis_modular_main.py", "-f", "13", "-y", "2024", "-r", "Japan", "-s", "R", "-d", "VER", "-d2", "LEC"],
        stdout=f,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        timeout=120
    )

print(f"CLI 執行完成，返回碼: {result.returncode}")
print("\n正在讀取輸出檔案...")
print("=" * 80)

with open(output_file, 'r', encoding='utf-8') as f:
    content = f.read()
    
# 過濾相關行
relevant_lines = []
for line in content.split('\n'):
    if any(keyword in line for keyword in ['DEBUG', 'time_series', '時間序列', '成功提取', '已添加時間序列', '缺少', 'time_seconds', 'time_reference']):
        relevant_lines.append(line)

if relevant_lines:
    print("\n相關輸出行:")
    for line in relevant_lines:
        print(line)
else:
    print("\n❌ 未找到相關的調試輸出")
    print("\n顯示最後 50 行:")
    lines = content.split('\n')
    for line in lines[-50:]:
        print(line)
