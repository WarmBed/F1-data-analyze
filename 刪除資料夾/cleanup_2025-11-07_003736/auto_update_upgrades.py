#!/usr/bin/env python3
"""
自動化 F1 主要部件升級分析器
功能:
1. 掃描 fiadoc/ 資料夾中的所有 Parc Fermé PDF
2. 檢測新增的 PDF 文件
3. 自動分析並更新數據
4. 重新生成完整的組織化 JSON
"""
import json
from pathlib import Path
from datetime import datetime
import hashlib
import sys

# 導入現有的分析模組
sys.path.insert(0, str(Path(__file__).parent))
from analyze_2025_parts_changes_v2 import F1UpgradeAnalyzerV2
from extract_major_upgrades_2025 import MajorUpgradeExtractor
from reorganize_major_upgrades import MajorUpgradeReorganizer


class AutoUpdateUpgradeAnalyzer:
    """自動更新升級分析器"""
    
    def __init__(self, 
                 fiadoc_dir="fiadoc",
                 cache_file=".pdf_cache.json",
                 output_complete="2025_f1_parts_changes_complete.json",
                 output_major="2025_f1_major_upgrades.json",
                 output_organized="2025_f1_major_upgrades_organized.json"):
        self.fiadoc_dir = Path(fiadoc_dir)
        self.cache_file = Path(cache_file)
        self.output_complete = output_complete
        self.output_major = output_major
        self.output_organized = output_organized
        
        self.cache_data = self._load_cache()
    
    def _load_cache(self):
        """載入 PDF 緩存記錄"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "last_update": None,
            "processed_files": {},
            "total_pdfs": 0
        }
    
    def _save_cache(self):
        """儲存 PDF 緩存記錄"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
    
    def _get_file_hash(self, file_path):
        """計算文件 MD5 雜湊值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def scan_pdfs(self):
        """掃描 fiadoc/ 資料夾中的所有 Parc Fermé PDF"""
        if not self.fiadoc_dir.exists():
            print(f"❌ 找不到資料夾: {self.fiadoc_dir}")
            return []
        
        parc_ferme_files = list(self.fiadoc_dir.glob("*Parts and parameters*.pdf"))
        
        print("\n" + "="*100)
        print(f"📂 掃描 Parc Fermé 文件")
        print("="*100)
        print(f"資料夾: {self.fiadoc_dir.absolute()}")
        print(f"找到 PDF: {len(parc_ferme_files)} 個")
        
        return parc_ferme_files
    
    def detect_changes(self, pdf_files):
        """檢測新增或修改的 PDF 文件"""
        new_files = []
        modified_files = []
        unchanged_files = []
        
        current_files = {pdf.name: pdf for pdf in pdf_files}
        
        print("\n🔍 檢測文件變化...")
        
        for filename, filepath in current_files.items():
            file_hash = self._get_file_hash(filepath)
            
            if filename not in self.cache_data["processed_files"]:
                # 新文件
                new_files.append(filepath)
                self.cache_data["processed_files"][filename] = {
                    "hash": file_hash,
                    "first_seen": datetime.now().isoformat(),
                    "last_processed": datetime.now().isoformat()
                }
            elif self.cache_data["processed_files"][filename]["hash"] != file_hash:
                # 文件已修改
                modified_files.append(filepath)
                self.cache_data["processed_files"][filename]["hash"] = file_hash
                self.cache_data["processed_files"][filename]["last_processed"] = datetime.now().isoformat()
            else:
                # 未變化
                unchanged_files.append(filepath)
        
        # 檢測已刪除的文件
        deleted_files = set(self.cache_data["processed_files"].keys()) - set(current_files.keys())
        
        print(f"\n📊 變化統計:")
        print(f"  🆕 新增文件: {len(new_files)} 個")
        print(f"  🔄 修改文件: {len(modified_files)} 個")
        print(f"  ⚪ 未變化: {len(unchanged_files)} 個")
        print(f"  🗑️  已刪除: {len(deleted_files)} 個")
        
        if new_files:
            print(f"\n🆕 新增的文件:")
            for f in new_files:
                print(f"  • {f.name}")
        
        if modified_files:
            print(f"\n🔄 修改的文件:")
            for f in modified_files:
                print(f"  • {f.name}")
        
        if deleted_files:
            print(f"\n🗑️  已刪除的文件:")
            for f in deleted_files:
                print(f"  • {f}")
                del self.cache_data["processed_files"][f]
        
        return {
            "new": new_files,
            "modified": modified_files,
            "unchanged": unchanged_files,
            "deleted": deleted_files,
            "needs_update": len(new_files) > 0 or len(modified_files) > 0 or len(deleted_files) > 0
        }
    
    def run_full_analysis(self):
        """執行完整分析流程"""
        print("\n" + "="*100)
        print("🏁 開始完整分析")
        print("="*100)
        
        # 步驟 1: 分析所有部件變更
        print("\n📋 步驟 1/3: 分析所有部件變更...")
        analyzer_v2 = F1UpgradeAnalyzerV2(fiadoc_dir=str(self.fiadoc_dir))
        analyzer_v2.analyze_all_documents()
        analyzer_v2.save_to_json(self.output_complete)
        analyzer_v2.save_to_csv(self.output_complete.replace('.json', '.csv'))
        
        total_changes = len(analyzer_v2.all_changes)
        print(f"✅ 步驟 1 完成: 提取 {total_changes} 筆部件變更")
        
        # 步驟 2: 提取主要部件升級
        print("\n🔧 步驟 2/3: 提取主要部件升級...")
        extractor = MajorUpgradeExtractor(json_file=self.output_complete)
        if extractor.load_data():
            extractor.extract_major_upgrades()
            
            # 生成帶 metadata 的 JSON
            stats = extractor.get_statistics()
            output_data = {
                "metadata": {
                    "生成時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "數據源": self.output_complete,
                    "統計資訊": stats
                },
                "主要部件升級記錄": extractor.major_upgrades
            }
            
            with open(self.output_major, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            major_count = len(extractor.major_upgrades)
            print(f"✅ 步驟 2 完成: 提取 {major_count} 筆主要升級")
        else:
            print("❌ 步驟 2 失敗: 無法載入部件變更數據")
            return False
        
        # 步驟 3: 重組為結構化 JSON
        print("\n📊 步驟 3/3: 重組為結構化 JSON...")
        reorganizer = MajorUpgradeReorganizer(input_file=self.output_major)
        final_data = reorganizer.generate_final_structure()
        
        with open(self.output_organized, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        team_count = len(final_data['車隊升級記錄'])
        print(f"✅ 步驟 3 完成: 組織 {team_count} 個車隊的升級記錄")
        
        # 更新緩存
        self.cache_data["last_update"] = datetime.now().isoformat()
        self.cache_data["total_pdfs"] = len(self.cache_data["processed_files"])
        self._save_cache()
        
        return True
    
    def auto_update(self, force_update=False):
        """自動檢測並更新"""
        print("\n" + "="*100)
        print("🤖 自動化 F1 主要部件升級分析器")
        print("="*100)
        print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 掃描 PDF
        pdf_files = self.scan_pdfs()
        if not pdf_files:
            print("\n❌ 沒有找到任何 Parc Fermé PDF 文件")
            return False
        
        # 檢測變化
        changes = self.detect_changes(pdf_files)
        
        # 決定是否需要更新
        if force_update:
            print("\n🔄 強制更新模式: 重新分析所有文件")
            needs_update = True
        elif changes["needs_update"]:
            print("\n✅ 檢測到文件變化，需要更新數據")
            needs_update = True
        else:
            print("\n⚪ 沒有檢測到文件變化")
            
            # 檢查輸出文件是否存在
            if not Path(self.output_organized).exists():
                print("⚠️  輸出文件不存在，執行首次分析")
                needs_update = True
            else:
                print("✅ 數據已是最新，無需更新")
                needs_update = False
        
        # 執行分析
        if needs_update:
            success = self.run_full_analysis()
            
            if success:
                print("\n" + "="*100)
                print("✅ 分析完成！")
                print("="*100)
                print(f"\n生成的文件:")
                print(f"  1. {self.output_complete} - 所有部件變更記錄")
                print(f"  2. {self.output_major} - 主要部件升級記錄")
                print(f"  3. {self.output_organized} - 結構化升級記錄（按車隊/車手組織）")
                print(f"\n上次更新: {self.cache_data['last_update']}")
                print(f"處理文件: {self.cache_data['total_pdfs']} 個 PDF")
                print("="*100 + "\n")
                return True
            else:
                print("\n❌ 分析過程中發生錯誤")
                return False
        else:
            print("\n" + "="*100)
            print("✅ 數據已是最新")
            print("="*100)
            print(f"\n現有文件:")
            print(f"  1. {self.output_complete}")
            print(f"  2. {self.output_major}")
            print(f"  3. {self.output_organized}")
            print(f"\n上次更新: {self.cache_data.get('last_update', '從未更新')}")
            print(f"處理文件: {self.cache_data['total_pdfs']} 個 PDF")
            print("="*100 + "\n")
            return True


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description='自動化 F1 主要部件升級分析器')
    parser.add_argument('-f', '--force', action='store_true', 
                       help='強制重新分析所有文件（忽略緩存）')
    parser.add_argument('--clear-cache', action='store_true',
                       help='清除緩存記錄')
    
    args = parser.parse_args()
    
    analyzer = AutoUpdateUpgradeAnalyzer()
    
    # 清除緩存
    if args.clear_cache:
        if analyzer.cache_file.exists():
            analyzer.cache_file.unlink()
            print("✅ 緩存已清除")
        else:
            print("⚪ 沒有緩存文件")
        return
    
    # 執行自動更新
    analyzer.auto_update(force_update=args.force)


if __name__ == '__main__':
    main()
