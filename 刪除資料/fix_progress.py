#!/usr/bin/env python
"""
手動修復 update_all_lap_analysis 的進度更新部分
"""

def fix_progress_updates():
    with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到需要修改的行
    for i in range(len(lines)):
        # 第一個修改點：添加進度更新（around line 6362）
        if '更新視窗 {i}/{len(self.lap_analysis_windows)}:' in lines[i]:
            # 在這行之前插入進度更新
            indent = '                '
            new_lines = [
                f'{indent}# 更新進度對話框\n',
                f'{indent}progress_text = f"正在更新 {{analysis_type}} ({{i}}/{{len(modules_to_update)}})...\\n{{window_title}}"\n',
                f'{indent}progress.setLabelText(progress_text)\n',
                f'{indent}progress.setValue(i)\n',
                f'{indent}QApplication.processEvents()  # 確保UI響應\n',
                f'{indent}\n',
            ]
            
            # 替換當前行
            lines[i] = f'{indent}print(f"[LAP_CONTROL] 📋 [{{i}}/{{len(modules_to_update)}}] 更新視窗: {{window_title}}")\n'
            
            # 插入新行
            lines[i:i] = new_lines
            
            # 修改下一行
            if i + len(new_lines) + 1 < len(lines):
                lines[i + len(new_lines) + 1] = f'{indent}print(f"[LAP_CONTROL]   ├─ 類型: {{analysis_type}}")\n'
                
            # 修改接下來的一行
            for j in range(i + len(new_lines) + 2, min(i + len(new_lines) + 10, len(lines))):
                if '模組類型' in lines[j]:
                    lines[j] = f'{indent}print(f"[LAP_CONTROL]   ├─ 模組: {{type(analysis_module).__name__}}")\n'
                    break
            
            print(f"✅ 修改行 {i+1}: 添加進度更新")
            break
    
    # 第二個修改點：修改 has_method 檢查日誌
    for i in range(len(lines)):
        if 'hasattr檢查 update_lap_parameters:' in lines[i]:
            indent = '                '
            lines[i] = f"{indent}print(f\"[LAP_CONTROL]   ├─ 方法檢查: {{'✅' if has_method else '❌'}} update_lap_parameters\")\n"
            print(f"✅ 修改行 {i+1}: 更新 hasattr 檢查日誌")
            break
    
    # 第三個修改點：更新成功/失敗日誌
    for i in range(len(lines)):
        if '找到 update_lap_parameters 方法，開始調用...' in lines[i]:
            # 跳過這行，查找成功/失敗日誌
            for j in range(i+1, min(i+20, len(lines))):
                if '視窗更新成功' in lines[j]:
                    indent = '                        '
                    lines[j] = f'{indent}print(f"[LAP_CONTROL]   └─ ✅ 更新成功")\n'
                    print(f"✅ 修改行 {j+1}: 更新成功日誌")
                elif '視窗更新失敗' in lines[j]:
                    indent = '                        '
                    lines[j] = f'{indent}print(f"[LAP_CONTROL]   └─ ⚠️ 更新返回 False")\n'
                    print(f"✅ 修改行 {j+1}: 更新失敗日誌")
                elif '模組沒有 update_lap_parameters 方法' in lines[j]:
                    indent = '                    '
                    lines[j] = f'{indent}print(f"[LAP_CONTROL]   └─ ❌ 模組沒有 update_lap_parameters 方法")\n'
                    print(f"✅ 修改行 {j+1}: 無方法日誌")
                    break
            break
    
    # 第四個修改點：添加延遲機制
    for i in range(len(lines)):
        if '模組沒有 update_lap_parameters 方法' in lines[i]:
            # 在這行後面添加延遲
            for j in range(i+1, min(i+10, len(lines))):
                if 'except Exception as e:' in lines[j]:
                    indent = '                '
                    new_lines = [
                        '\n',
                        f'{indent}# 短暫延遲確保載入完成（防止並發衝突）\n',
                        f'{indent}QApplication.processEvents()\n',
                        f'{indent}time.sleep(0.25)  # 250ms 延遲\n',
                    ]
                    lines[j:j] = new_lines
                    print(f"✅ 在行 {j+1} 之前添加延遲機制")
                    break
            break
    
    # 第五個修改點：更新錯誤日誌
    for i in range(len(lines)):
        if '更新視窗時發生錯誤:' in lines[i]:
            indent = '                '
            lines[i] = f'{indent}print(f"[LAP_CONTROL]   └─ ❌ 更新時發生錯誤: {{e}}")\n'
            
            # 刪除接下來的 "錯誤詳情" 行
            if i+1 < len(lines) and 'traceback.format_exc()' in lines[i+1]:
                del lines[i+1]
            
            # 添加 traceback.print_exc()
            lines.insert(i+1, f'{indent}traceback.print_exc()\n')
            print(f"✅ 修改行 {i+1}: 更新錯誤日誌")
            break
    
    # 寫回文件
    with open('f1t_gui_main.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("\n🎉 所有修改完成！")

if __name__ == "__main__":
    fix_progress_updates()
