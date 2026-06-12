"""
F1T GUI EXE 建構工具 - Tkinter 版本
========================================

使用 tkinter 避免 PyQt5 檔案鎖定問題
支援虛擬環境和系統 Python 雙模式

作者：F1T 開發團隊
日期：2025-12-15
"""

import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path

# 導入版本資訊
try:
    from config.version import APP_VERSION, APP_NAME
    import webbrowser
except ImportError:
    APP_VERSION = "V0.16.0"
    APP_NAME = "PIT WALL"


class EXEBuilderGUI:
    def __init__(self, root):
        self.root = root
        self.project_root = Path(__file__).parent.parent.absolute()
        self.venv_path = self.project_root / "venv_build"
        self.building = False
        
        self.init_ui()
        self.check_environment()
        
    def init_ui(self):
        """初始化界面"""
        self.root.title("F1T GUI EXE 建構工具")
        self.root.geometry("900x700")
        
        # 標題
        title_frame = tk.Frame(self.root)
        title_frame.pack(pady=10)
        
        title_label = tk.Label(
            title_frame,
            text="🏎️ F1T GUI EXE 建構工具",
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        # 狀態組
        status_frame = tk.LabelFrame(self.root, text="環境狀態", padx=10, pady=10)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_text = tk.Text(status_frame, height=8, width=80, wrap="word")
        self.status_text.pack()
        self.status_text.config(state="disabled")
        
        # 選項組
        options_frame = tk.LabelFrame(self.root, text="建構選項", padx=10, pady=10)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        self.use_venv_var = tk.BooleanVar(value=False)
        self.clean_build_var = tk.BooleanVar(value=True)
        self.show_console_var = tk.BooleanVar(value=False)
        self.onedir_mode_var = tk.BooleanVar(value=False)  # 預設使用單檔案模式（加密保護）
        self.disable_logs_var = tk.BooleanVar(value=False)  # 禁止 EXE 輸出日誌檔案
        
        tk.Checkbutton(
            options_frame,
            text="使用虛擬環境 (venv_build)",
            variable=self.use_venv_var,
            command=self.on_venv_toggle
        ).pack(anchor="w")
        
        tk.Checkbutton(
            options_frame,
            text="清理舊的建構檔案",
            variable=self.clean_build_var
        ).pack(anchor="w")
        
        tk.Checkbutton(
            options_frame,
            text="目錄模式 (開發用: 啟動快但無加密)",
            variable=self.onedir_mode_var
        ).pack(anchor="w")
        
        # 版本號設定
        version_frame = tk.Frame(options_frame)
        version_frame.pack(fill="x", pady=5)
        
        tk.Label(version_frame, text="版本號命名:").pack(side="left")
        
        self.version_var = tk.StringVar(value=APP_VERSION)
        version_entry = tk.Entry(version_frame, textvariable=self.version_var, width=15)
        version_entry.pack(side="left", padx=5)
        
        tk.Label(
            version_frame,
            text=f"(單檔案: .exe | 目錄模式: 資料夾)",
            fg="gray"
        ).pack(side="left")
        
        tk.Checkbutton(
            options_frame,
            text="EXE 顯示控制台視窗（除錯用）",
            variable=self.show_console_var
        ).pack(anchor="w")
        
        tk.Checkbutton(
            options_frame,
            text="禁止輸出 LOGS（正式發布用，節省效能）",
            variable=self.disable_logs_var
        ).pack(anchor="w")
        
        # 模式說明
        info_frame = tk.Frame(options_frame)
        info_frame.pack(fill="x", pady=5)
        
        tk.Label(
            info_frame,
            text="💡 預設: 單檔案模式（加密保護、易分發、專業）",
            fg="green",
            font=("Arial", 9)
        ).pack(anchor="w")
        
        # 按鈕組
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.auto_btn = tk.Button(
            button_frame,
            text="⚡ 一鍵建構 EXE",
            command=self.auto_build,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10
        )
        self.auto_btn.pack(side="left", padx=5)
        
        # 進度條
        self.progress = ttk.Progressbar(
            self.root,
            mode='indeterminate',
            length=300
        )
        self.progress.pack(pady=5)
        
        # 日誌輸出
        log_label = tk.Label(self.root, text="建構日誌：", font=("Arial", 10, "bold"))
        log_label.pack(anchor="w", padx=10)
        
        self.log_text = scrolledtext.ScrolledText(
            self.root,
            height=20,
            width=100,
            wrap="word",
            font=("Consolas", 9)
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 底部按鈕
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(
            bottom_frame,
            text="Help",
            command=self.open_help_link,
            fg="#1a73e8",
            cursor="hand2"
        ).pack(side="right", padx=5)

        self.open_dist_btn = tk.Button(
            bottom_frame,
            text="Open dist folder",
            command=self.open_dist_folder,
            state="disabled"
        )
        self.open_dist_btn.pack(side="left", padx=5)
        
        tk.Button(
            bottom_frame,
            text="Clear log",
            command=lambda: self.log_text.delete(1.0, tk.END)
        ).pack(side="left", padx=5)
        
        tk.Button(
            bottom_frame,
            text="Close",
            command=self.root.quit
        ).pack(side="right", padx=5)
    
    def open_help_link(self):
        """開啟官方說明連結"""
        webbrowser.open("https://www.pitwall.info/")
        
    def on_venv_toggle(self):
        """虛擬環境選項切換時更新狀態"""
        self.check_environment()
    
    def get_python_executable(self):
        """取得 Python 執行檔路徑"""
        if self.use_venv_var.get():
            venv_python = self.venv_path / "Scripts" / "python.exe"
            if venv_python.exists():
                return str(venv_python)
            else:
                return None
        else:
            return sys.executable
    
    def check_environment(self):
        """檢查環境"""
        status_parts = []
        
        # 檢查 Python
        python_exe = self.get_python_executable()
        
        if self.use_venv_var.get():
            if python_exe is None:
                status_parts.append(f"❌ 虛擬環境不存在: {self.venv_path}")
                status_parts.append("   點擊建構時將自動建立")
            else:
                status_parts.append(f"✅ 虛擬環境: {self.venv_path}")
                result = subprocess.run(
                    [python_exe, "--version"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    status_parts.append(f"   Python: {version}")
        else:
            result = subprocess.run(
                [python_exe, "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                status_parts.append(f"✅ 系統 Python: {version}")
            else:
                status_parts.append("❌ Python 未找到")
        
        # 檢查已安裝套件
        if python_exe:
            result = subprocess.run(
                [python_exe, "-m", "pip", "list"],
                capture_output=True,
                text=True
            )
        else:
            result = None
        
        if result and result.returncode == 0:
            installed = result.stdout.lower()
            
            packages = {
                'PyInstaller': 'pyinstaller' in installed,
                'PyQt5': 'pyqt5' in installed,
                'Pandas': 'pandas' in installed,
                'Matplotlib': 'matplotlib' in installed,
                'ReportLab': 'reportlab' in installed,
            }
            
            for name, exists in packages.items():
                status_parts.append(f"{'✅' if exists else '❌'} {name}")
        
        # 檢查 spec 檔案
        if (self.project_root / "build_tools" / "F1T_GUI_clean.spec").exists():
            status_parts.append("✅ Spec 檔案存在")
        else:
            status_parts.append("⚠️ Spec 檔案不存在")
        
        self.update_status("\n".join(status_parts))
        
    def update_status(self, text):
        """更新狀態文字"""
        self.status_text.config(state="normal")
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(1.0, text)
        self.status_text.config(state="disabled")
        
    def append_log(self, text):
        """添加日誌"""
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def _convert_to_onedir_spec(self, content: str) -> str:
        """
        將 spec 檔案轉換為目錄模式 (--onedir)
        
        Args:
            content: spec 檔案內容
            
        Returns:
            轉換後的 spec 檔案內容
        """
        import re
        
        # 步驟 1: 修改 EXE() 配置
        # 尋找 EXE(...) 區塊並替換
        exe_pattern = r'exe = EXE\((.*?)\n\)'
        
        def replace_exe(match):
            exe_content = match.group(1)
            
            # 移除 a.binaries, a.zipfiles, a.datas（這些應該在 COLLECT 中）
            exe_content = re.sub(r'\s*a\.binaries,?\s*\n', '', exe_content)
            exe_content = re.sub(r'\s*a\.zipfiles,?\s*\n', '', exe_content)
            exe_content = re.sub(r'\s*a\.datas,?\s*\n', '', exe_content)
            
            # 確保有 exclude_binaries=True 和空的 binaries 列表
            if 'exclude_binaries' not in exe_content:
                # 在 a.scripts 後插入
                exe_content = exe_content.replace(
                    'a.scripts,',
                    'a.scripts,\n    [],  # 不包含 binaries (目錄模式)\n    exclude_binaries=True,  # ✅ 啟用目錄模式'
                )
            else:
                # 更新 exclude_binaries 為 True
                exe_content = re.sub(r'exclude_binaries=\w+', 'exclude_binaries=True', exe_content)
            
            return f'exe = EXE({exe_content}\n)'
        
        content = re.sub(exe_pattern, replace_exe, content, flags=re.DOTALL)
        
        # 步驟 2: 確保有 COLLECT 區塊
        if 'coll = COLLECT' not in content and 'COLLECT(' not in content:
            # 在檔案末尾添加 COLLECT
            collect_block = '''
# COLLECT - 收集所有檔案到目錄
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='F1T_GUI',
)
'''
            content += collect_block
        
        return content
    
    def _convert_to_onefile_spec(self, content: str) -> str:
        """
        將 spec 檔案轉換為單檔案模式 (--onefile)
        
        Args:
            content: spec 檔案內容
            
        Returns:
            轉換後的 spec 檔案內容
        """
        import re
        
        # 步驟 1: 修改 EXE() 配置
        exe_pattern = r'exe = EXE\((.*?)\n\)'
        
        def replace_exe(match):
            exe_content = match.group(1)
            
            # 移除 exclude_binaries 參數（單檔案模式不需要）
            exe_content = re.sub(r'\s*exclude_binaries=True,?\s*#.*?\n', '', exe_content)
            exe_content = re.sub(r'\s*exclude_binaries=False,?\s*#.*?\n', '', exe_content)
            exe_content = re.sub(r'\s*exclude_binaries=\w+,?\s*', '', exe_content)
            
            # 移除空的 [] 參數（目錄模式的標記）
            exe_content = re.sub(r'\s*\[\],?\s*#.*?binaries.*?\n', '', exe_content)
            
            # 確保包含 a.binaries, a.zipfiles, a.datas
            if 'a.binaries' not in exe_content:
                # 在 a.scripts 後插入
                exe_content = exe_content.replace(
                    'a.scripts,',
                    'a.scripts,\n    a.binaries,\n    a.zipfiles,\n    a.datas,'
                )
            
            return f'exe = EXE({exe_content}\n)'
        
        content = re.sub(exe_pattern, replace_exe, content, flags=re.DOTALL)
        
        # 步驟 2: 移除 COLLECT 區塊
        # 尋找並刪除整個 COLLECT 區塊
        collect_pattern = r'\n# COLLECT.*?\ncoll = COLLECT\([^)]+\)\s*'
        content = re.sub(collect_pattern, '', content, flags=re.DOTALL)
        
        # 也處理沒有註解的 COLLECT
        collect_pattern2 = r'\ncoll = COLLECT\([^)]+\)\s*'
        content = re.sub(collect_pattern2, '', content, flags=re.DOTALL)
        
        return content
        
    def auto_build(self):
        """一鍵建構"""
        if self.building:
            messagebox.showwarning("警告", "已有建構任務在執行中...")
            return
        
        self.building = True
        self.auto_btn.config(state="disabled")
        self.progress.start()
        
        thread = threading.Thread(target=self._auto_build, daemon=True)
        thread.start()
        
    def _auto_build(self):
        """建構執行緒"""
        try:
            self.append_log("=" * 60)
            self.append_log("⚡ 開始一鍵建構...")
            self.append_log("=" * 60)
            
            # 取得 Python 執行檔
            python_exe = self.get_python_executable()
            
            # 建立虛擬環境（如果需要）
            if self.use_venv_var.get():
                if python_exe is None:
                    self.append_log(f"\n📦 建立虛擬環境: {self.venv_path}")
                    result = subprocess.run(
                        [sys.executable, "-m", "venv", str(self.venv_path)],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        self.append_log("✅ 虛擬環境建立成功")
                        python_exe = str(self.venv_path / "Scripts" / "python.exe")
                    else:
                        self.append_log(f"❌ 虛擬環境建立失敗: {result.stderr[:200]}")
                        self.on_build_finished(False)
                        return
                else:
                    self.append_log(f"\n✅ 使用虛擬環境: {self.venv_path}")
            else:
                self.append_log(f"\n✅ 使用系統 Python: {python_exe}")
            
            # 檢查 PyInstaller
            self.append_log("\n📦 檢查 PyInstaller...")
            result = subprocess.run(
                [python_exe, "-m", "pip", "show", "pyinstaller"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.append_log("⚠️ PyInstaller 未安裝，正在安裝...")
                
                # 安裝核心套件
                packages = [
                    "pyinstaller",
                    "pyinstaller-hooks-contrib",
                    "packaging",
                    "pefile",
                    "pywin32-ctypes"
                ]
                
                if self.use_venv_var.get():
                    # 虛擬環境需要安裝所有依賴
                    # ⚠️ PyQt5 必須指定版本，避免 PyInstaller 無法讀取版本 metadata
                    packages.extend([
                        "PyQt5==5.15.10",  # 指定版本確保兼容性
                        "fastf1",
                        "pandas",
                        "matplotlib",
                        "scipy",
                        "Pillow",
                        "requests",
                        "numpy",
                        "prettytable",
                        "tabulate",
                        "openpyxl",
                        "seaborn",
                        "scikit-learn",
                        "reportlab",  # PDF 報告生成
                        "certifi",    # SSL 證書 (spec 文件需要)
                    ])
                
                for pkg in packages:
                    self.append_log(f"   正在安裝 {pkg}...")
                    result = subprocess.run(
                        [python_exe, "-m", "pip", "install", pkg],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        self.append_log(f"   ✅ {pkg} 安裝成功")
                    else:
                        self.append_log(f"   ❌ {pkg} 安裝失敗: {result.stderr[:200]}")
                        if pkg == "pyinstaller":
                            self.on_build_finished(False)
                            return
            else:
                self.append_log("✅ PyInstaller 已安裝")
            
            # 清理舊檔案
            if self.clean_build_var.get():
                self.append_log("\n🧹 清理舊的建構檔案...")
                import shutil
                
                build_dir = self.project_root / "build"
                dist_dir = self.project_root / "dist"
                
                if build_dir.exists():
                    try:
                        shutil.rmtree(build_dir, ignore_errors=True)
                        self.append_log("   ✅ 已清理 build 資料夾")
                    except Exception as e:
                        self.append_log(f"   ⚠️ 清理 build 時發生警告: {e}")
                
                if dist_dir.exists():
                    for item in dist_dir.glob("F1T_GUI*"):
                        try:
                            if item.is_file():
                                item.unlink()
                            elif item.is_dir():
                                shutil.rmtree(item, ignore_errors=True)
                            self.append_log(f"   ✅ 已清理 {item.name}")
                        except Exception as e:
                            self.append_log(f"   ⚠️ 清理 {item.name} 時發生警告: {e}")
            
            # 執行 PyInstaller
            self.append_log("\n🔧 執行 PyInstaller...")
            self.append_log("⏳ 這可能需要 3-5 分鐘，請耐心等待...\n")
            
            spec_file = self.project_root / "build_tools" / "F1T_GUI_clean.spec"
            
            if not spec_file.exists():
                self.append_log("❌ 找不到 F1T_GUI_clean.spec 檔案")
                self.on_build_finished(False)
                return
            
            # 讀取 spec 檔案內容
            content = spec_file.read_text(encoding='utf-8')
            modified = False
            
            # 修改 console 選項
            if self.show_console_var.get():
                if 'console=False' in content:
                    content = content.replace('console=False', 'console=True')
                    modified = True
                    self.append_log("✅ 已啟用控制台模式")
            else:
                if 'console=True' in content:
                    content = content.replace('console=True', 'console=False')
                    modified = True
            
            # 修改打包模式（目錄模式 vs 單檔案模式）
            onedir_mode = self.onedir_mode_var.get()
            
            if onedir_mode:
                # 目錄模式：需要有 COLLECT
                if 'exclude_binaries=False' in content or ('exclude_binaries' not in content and 'a.binaries' in content):
                    self.append_log("🔄 切換到目錄模式 (--onedir)...")
                    # 替換為目錄模式配置
                    content = self._convert_to_onedir_spec(content)
                    modified = True
                    self.append_log("✅ 已設定為目錄模式")
            else:
                # 單檔案模式：不需要 COLLECT
                if 'exclude_binaries=True' in content:
                    self.append_log("🔄 切換到單檔案模式 (--onefile)...")
                    content = self._convert_to_onefile_spec(content)
                    modified = True
                    self.append_log("✅ 已設定為單檔案模式")
            
            # 如果有修改，寫回檔案
            if modified:
                spec_file.write_text(content, encoding='utf-8')
            
            # 🔒 修改 runtime_hook 來控制 EXE 日誌輸出
            runtime_hook_file = self.project_root / "hooks" / "runtime_hook_disable_logger.py"
            if runtime_hook_file.exists():
                hook_content = runtime_hook_file.read_text(encoding='utf-8')
                
                if self.disable_logs_var.get():
                    # 禁用日誌
                    if "F1T_EXE_DISABLE_LOG'] = '0'" in hook_content:
                        hook_content = hook_content.replace(
                            "F1T_EXE_DISABLE_LOG'] = '0'",
                            "F1T_EXE_DISABLE_LOG'] = '1'"
                        )
                        hook_content = hook_content.replace(
                            'Logging ENABLED for debugging',
                            'Logging DISABLED for production'
                        )
                        runtime_hook_file.write_text(hook_content, encoding='utf-8')
                        self.append_log("🔒 已禁用 EXE 日誌輸出（正式發布模式）")
                else:
                    # 啟用日誌
                    if "F1T_EXE_DISABLE_LOG'] = '1'" in hook_content:
                        hook_content = hook_content.replace(
                            "F1T_EXE_DISABLE_LOG'] = '1'",
                            "F1T_EXE_DISABLE_LOG'] = '0'"
                        )
                        hook_content = hook_content.replace(
                            'Logging DISABLED for production',
                            'Logging ENABLED for debugging'
                        )
                        runtime_hook_file.write_text(hook_content, encoding='utf-8')
                        self.append_log("📝 EXE 日誌輸出已啟用（除錯模式）")
            
            cmd = [python_exe, "-m", "PyInstaller", str(spec_file), "--noconfirm"]
            
            self.append_log(f"🔧 執行命令: {' '.join(cmd)}\n")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # 實時輸出日誌
            for line in process.stdout:
                self.append_log(line.rstrip())
            
            process.wait()
            
            if process.returncode == 0:
                # 獲取版本號用於命名
                version = self.version_var.get().strip()
                version_suffix = f"-{version}" if version else ""
                
                # 🔧 修正：spec 文件生成的 EXE 名稱是 PitWall_{version}
                # 例如：PitWall_V0.14.0.exe
                pitwall_name = f"PitWall_{version}" if version else "PitWall"
                
                # 檢查輸出檔案（目錄模式或單檔案模式）
                if self.onedir_mode_var.get():
                    # 目錄模式：先找 PitWall_{version}，再找 F1T_GUI
                    exe_path = self.project_root / "dist" / pitwall_name / f"{pitwall_name}.exe"
                    if not exe_path.exists():
                        exe_path = self.project_root / "dist" / "F1T_GUI" / "F1T_GUI.exe"
                    output_desc = f"dist/{exe_path.parent.name}/ (目錄模式)"
                else:
                    # 單檔案模式：先找 PitWall_{version}.exe，再找 F1T_GUI.exe
                    exe_path = self.project_root / "dist" / f"{pitwall_name}.exe"
                    if not exe_path.exists():
                        exe_path = self.project_root / "dist" / "F1T_GUI.exe"
                    output_desc = f"dist/{exe_path.name} (單檔案模式)"
                
                if exe_path.exists():
                    size_mb = exe_path.stat().st_size / (1024 * 1024)
                    
                    # 🔧 簡化邏輯：spec 文件已經包含版本號，不需要重新命名
                    # PitWall_V0.14.0.exe 已經是正確的名稱
                    
                    self.append_log("\n" + "=" * 60)
                    self.append_log("✅ EXE 建構成功！")
                    self.append_log(f"📍 位置: {output_desc}")
                    self.append_log(f"📦 EXE 大小: {size_mb:.2f} MB")
                    
                    # 如果是目錄模式，顯示 _internal 資料夾資訊
                    if self.onedir_mode_var.get():
                        internal_dir = exe_path.parent / "_internal"
                        if internal_dir.exists():
                            total_size = sum(f.stat().st_size for f in internal_dir.rglob('*') if f.is_file())
                            internal_mb = total_size / (1024 * 1024)
                            self.append_log(f"📁 _internal 大小: {internal_mb:.2f} MB")
                    
                    self.append_log("=" * 60)
                    self.on_build_finished(True)
                else:
                    # 🔧 額外嘗試：列出 dist 資料夾中的所有 EXE 檔案
                    dist_dir = self.project_root / "dist"
                    self.append_log(f"\n⚠️ 預期的 EXE 路徑不存在: {exe_path}")
                    if dist_dir.exists():
                        exe_files = list(dist_dir.glob("*.exe")) + list(dist_dir.glob("*/*.exe"))
                        if exe_files:
                            self.append_log(f"📂 dist 資料夾中找到的 EXE 檔案:")
                            for ef in exe_files:
                                self.append_log(f"   - {ef.relative_to(dist_dir)}")
                            # 使用第一個找到的 EXE
                            exe_path = exe_files[0]
                            size_mb = exe_path.stat().st_size / (1024 * 1024)
                            self.append_log("\n" + "=" * 60)
                            self.append_log("✅ EXE 建構成功！")
                            self.append_log(f"📍 位置: dist/{exe_path.relative_to(dist_dir)}")
                            self.append_log(f"📦 EXE 大小: {size_mb:.2f} MB")
                            self.append_log("=" * 60)
                            self.on_build_finished(True)
                        else:
                            self.append_log("\n❌ EXE 檔案未找到")
                            self.on_build_finished(False)
                    else:
                        self.append_log("\n❌ dist 資料夾不存在")
                        self.on_build_finished(False)
            else:
                self.append_log("\n❌ 建構失敗")
                self.on_build_finished(False)
                
        except Exception as e:
            self.append_log(f"\n❌ 建構過程發生錯誤: {e}")
            import traceback
            self.append_log(traceback.format_exc())
            self.on_build_finished(False)
            
    def on_build_finished(self, success):
        """建構完成"""
        self.building = False
        self.progress.stop()
        self.auto_btn.config(state="normal")
        
        if success:
            self.open_dist_btn.config(state="normal")
            messagebox.showinfo("成功", "EXE 建構成功！")
        else:
            messagebox.showerror("失敗", "EXE 建構失敗，請檢查日誌")
        
        # 重新檢查環境
        self.check_environment()
        
    def open_dist_folder(self):
        """打開 dist 資料夾"""
        dist_path = self.project_root / "dist"
        if dist_path.exists():
            import os
            # 使用 os.startfile 在 Windows 上更可靠
            try:
                os.startfile(str(dist_path))
            except Exception as e:
                # 備用方案：使用 explorer
                try:
                    subprocess.run(["explorer", str(dist_path)], shell=True)
                except Exception as e2:
                    messagebox.showerror("錯誤", f"無法開啟資料夾: {e2}")
        else:
            messagebox.showerror("錯誤", "dist 資料夾不存在")


def main():
    root = tk.Tk()
    app = EXEBuilderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
