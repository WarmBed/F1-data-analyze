#!/usr/bin/env python3
"""
FIA 官方文件下載器
用於自動下載和分類 F1 技術文件，識別升級套件相關資訊
"""
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
from datetime import datetime
import time
import re
from typing import List, Dict, Optional
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fia_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FIADocumentScraper:
    """FIA 文件爬蟲"""
    
    BASE_URL = "https://www.fia.com"
    DOCUMENTS_URL = f"{BASE_URL}/documents/championships/fia-formula-one-world-championship-14"
    
    # 文件類型分類（根據 FIA 命名規則）
    DOCUMENT_TYPES = {
        'technical': [
            'technical directive',
            'technical report',
            'scrutineering',
            'parc ferme',
            'technical infringement'
        ],
        'sporting': [
            'stewards decision',
            'stewards document',
            'time penalty',
            'grid penalty',
            'reprimand'
        ],
        'event': [
            'event notes',
            'race director',
            'circuit map',
            'drs zones'
        ],
        'tire': [
            'pirelli preview',
            'pirelli analysis',
            'tyre allocation'
        ],
        'upgrade': [
            'new parts',
            'upgrade',
            'technical update',
            'development'
        ]
    }
    
    def __init__(self, download_dir: str = "fia_documents"):
        """初始化爬蟲"""
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        # 建立分類資料夾
        for category in self.DOCUMENT_TYPES.keys():
            (self.download_dir / category).mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        logger.info(f"📁 下載目錄: {self.download_dir.absolute()}")
    
    def get_race_documents(self, year: int = 2025, race: Optional[str] = None, download: bool = False) -> List[Dict]:
        """
        獲取特定賽季/分站的文件清單
        
        Args:
            year: 賽季年份
            race: 分站名稱（例如 "Japan", "Monaco"）
            download: 是否邊掃描邊下載
        
        Returns:
            文件資訊列表
        """
        logger.info(f"🔍 正在搜索 {year} {race or '所有分站'} 的文件...")
        
        try:
            # 第一步：獲取主頁面，找出所有分站連結
            response = self.session.get(self.DOCUMENTS_URL, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 找出所有分站的子頁面連結
            race_links = soup.find_all('a', href=re.compile(r'/decision-document-list/nojs/\d+'))
            
            logger.info(f"📋 找到 {len(race_links)} 個分站連結")
            
            all_documents = []
            
            # 第二步：訪問每個分站的子頁面
            for i, race_link in enumerate(race_links, 1):
                race_name = race_link.get_text(strip=True)
                race_url = race_link.get('href')
                
                if not race_url.startswith('http'):
                    race_url = self.BASE_URL + race_url
                
                # 篩選特定分站
                if race and race.lower() not in race_name.lower():
                    continue
                
                logger.info(f"[{i}/{len(race_links)}] 📥 正在抓取: {race_name}")
                
                # 訪問分站子頁面（支援即時下載）
                race_docs = self._get_race_page_documents(race_url, race_name, year, download=download)
                all_documents.extend(race_docs)
                
                # 避免過度請求
                time.sleep(0.5)
            
            logger.info(f"✅ 總共找到 {len(all_documents)} 個文件")
            return all_documents
            
        except Exception as e:
            logger.error(f"❌ 獲取文件清單失敗: {e}")
            return []
    
    def _get_race_page_documents(self, race_url: str, race_name: str, year: int, download: bool = False) -> List[Dict]:
        """
        獲取單一分站頁面的所有文件
        
        Args:
            race_url: 分站頁面 URL
            race_name: 分站名稱
            year: 年份篩選
            download: 是否立即下載（邊掃描邊下載模式）
        
        Returns:
            該分站的文件列表
        """
        try:
            response = self.session.get(race_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            documents = []
            
            # 找出所有 PDF 連結
            doc_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
            
            for link in doc_links:
                doc_url = link.get('href')
                if not doc_url.startswith('http'):
                    doc_url = self.BASE_URL + doc_url
                
                doc_title = link.get_text(strip=True)
                
                # 解析文件資訊
                doc_info = self._parse_document_info(doc_url, doc_title)
                doc_info['race'] = self._clean_race_name(race_name)
                doc_info['year'] = year
                
                documents.append(doc_info)
                logger.debug(f"  ✓ {doc_title[:60]}...")
                
                # 即時下載模式
                if download:
                    self.download_document(doc_info)
            
            return documents
            
        except Exception as e:
            logger.error(f"❌ 抓取分站頁面失敗 {race_name}: {e}")
            return []
    
    def _clean_race_name(self, race_name: str) -> str:
        """清理分站名稱"""
        # 移除 "GRAND PRIX" 等後綴
        race_name = race_name.replace('GRAND PRIX', '').strip()
        race_name = race_name.replace('TESTS SEASON', '').strip()
        
        # 轉換為標題格式
        race_name = race_name.title()
        
        return race_name
    
    def _parse_document_info(self, url: str, title: str) -> Dict:
        """解析文件資訊"""
        # 從 URL 提取資訊（FIA 文件命名規則）
        # 範例: 2025_sao_paulo_grand_prix_-_technical_report.pdf
        filename = url.split('/')[-1]
        parts = filename.lower().replace('.pdf', '').split('_')
        
        # 提取年份
        year = None
        for part in parts:
            if part.isdigit() and len(part) == 4:
                year = int(part)
                break
        
        # 提取分站名稱
        race = "Unknown"
        if 'grand' in parts and 'prix' in parts:
            gp_index = parts.index('grand')
            race_parts = parts[1:gp_index]  # 假設格式是 year_race_name_grand_prix
            race = ' '.join(race_parts).title()
        
        # 分類文件類型
        category = self._classify_document(title.lower())
        
        return {
            'url': url,
            'title': title,
            'filename': filename,
            'year': year or 2025,
            'race': race,
            'category': category,
            'is_upgrade_related': self._is_upgrade_related(title.lower())
        }
    
    def _classify_document(self, title: str) -> str:
        """根據標題分類文件"""
        for category, keywords in self.DOCUMENT_TYPES.items():
            if any(keyword in title for keyword in keywords):
                return category
        return 'other'
    
    def _is_upgrade_related(self, title: str) -> bool:
        """判斷是否與升級套件相關"""
        upgrade_keywords = [
            'new parts', 'upgrade', 'technical update', 'development',
            'modification', 'aerodynamic', 'component', 'specification'
        ]
        return any(keyword in title for keyword in upgrade_keywords)
    
    def download_document(self, doc_info: Dict) -> Optional[Path]:
        """
        下載單一文件
        
        Args:
            doc_info: 文件資訊字典
        
        Returns:
            下載的檔案路徑，失敗返回 None
        """
        try:
            # 確定儲存路徑
            category_dir = self.download_dir / doc_info['category']
            save_path = category_dir / doc_info['filename']
            
            # 檢查是否已下載
            if save_path.exists():
                logger.info(f"⏭️  已存在: {doc_info['filename']}")
                return save_path
            
            # 下載文件
            logger.info(f"⬇️  下載中: {doc_info['filename']}")
            response = self.session.get(doc_info['url'], timeout=60, stream=True)
            response.raise_for_status()
            
            # 儲存檔案
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ 下載完成: {save_path.relative_to(self.download_dir)}")
            time.sleep(1)  # 避免過度請求
            
            return save_path
            
        except Exception as e:
            logger.error(f"❌ 下載失敗 {doc_info['filename']}: {e}")
            return None
    
    def download_race_documents(self, year: int, race: str, 
                                category: Optional[str] = None) -> List[Path]:
        """
        下載特定分站的所有文件
        
        Args:
            year: 賽季年份
            race: 分站名稱
            category: 文件類型（可選，例如 'technical', 'upgrade'）
        
        Returns:
            下載的檔案路徑列表
        """
        documents = self.get_race_documents(year, race)
        
        # 篩選類別
        if category:
            documents = [doc for doc in documents if doc['category'] == category]
        
        downloaded = []
        for doc in documents:
            path = self.download_document(doc)
            if path:
                downloaded.append(path)
        
        return downloaded
    
    def find_upgrade_documents(self, year: int = 2025) -> List[Dict]:
        """
        尋找所有與升級套件相關的文件
        
        Args:
            year: 賽季年份
        
        Returns:
            升級相關文件列表
        """
        logger.info(f"🔍 搜索 {year} 賽季的升級套件文件...")
        
        all_docs = self.get_race_documents(year)
        upgrade_docs = [doc for doc in all_docs if doc['is_upgrade_related']]
        
        logger.info(f"✅ 找到 {len(upgrade_docs)} 個升級相關文件")
        
        # 依分站分組
        by_race = {}
        for doc in upgrade_docs:
            race = doc['race']
            if race not in by_race:
                by_race[race] = []
            by_race[race].append(doc)
        
        # 輸出摘要
        print("\n" + "="*70)
        print(f"📊 {year} 賽季升級套件文件摘要")
        print("="*70)
        for race, docs in sorted(by_race.items()):
            print(f"\n🏁 {race}:")
            for doc in docs:
                print(f"  • {doc['title']}")
        print("="*70 + "\n")
        
        return upgrade_docs
    
    def generate_report(self, documents: List[Dict], output_file: str = "fia_documents_report.json"):
        """
        生成文件報告
        
        Args:
            documents: 文件列表
            output_file: 輸出檔案名稱
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_documents': len(documents),
            'by_category': {},
            'by_race': {},
            'upgrade_related': [],
            'documents': documents
        }
        
        # 依類別統計
        for doc in documents:
            category = doc['category']
            report['by_category'][category] = report['by_category'].get(category, 0) + 1
            
            race = doc['race']
            if race not in report['by_race']:
                report['by_race'][race] = 0
            report['by_race'][race] += 1
            
            if doc['is_upgrade_related']:
                report['upgrade_related'].append(doc)
        
        # 儲存報告
        report_path = self.download_dir / output_file
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 報告已儲存: {report_path}")
        
        return report


def main():
    """主程式 - 示範使用"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FIA 文件下載器')
    parser.add_argument('-y', '--year', type=int, default=2025, help='賽季年份')
    parser.add_argument('-r', '--race', type=str, help='分站名稱 (例如: Japan, Monaco)')
    parser.add_argument('-c', '--category', type=str, 
                       choices=['technical', 'sporting', 'event', 'tire', 'upgrade'],
                       help='文件類別')
    parser.add_argument('-u', '--upgrade-only', action='store_true', 
                       help='僅搜尋升級相關文件')
    parser.add_argument('-d', '--download', action='store_true', 
                       help='下載找到的文件')
    parser.add_argument('--list-only', action='store_true', 
                       help='僅列出文件，不下載')
    
    args = parser.parse_args()
    
    scraper = FIADocumentScraper()
    
    print("\n" + "="*70)
    print("🏎️  FIA Formula 1 文件下載器")
    print("="*70 + "\n")
    
    if args.upgrade_only:
        # 僅搜尋升級文件
        upgrade_docs = scraper.find_upgrade_documents(args.year)
        
        if args.download and upgrade_docs:
            print(f"\n⬇️  準備下載 {len(upgrade_docs)} 個升級文件...")
            for doc in upgrade_docs:
                scraper.download_document(doc)
    else:
        # 一般搜尋
        documents = scraper.get_race_documents(args.year, args.race, download=args.download)
        
        if args.category:
            documents = [doc for doc in documents if doc['category'] == args.category]
        
        if not documents:
            print("❌ 未找到符合條件的文件")
            return
        
        # 顯示清單
        print(f"找到 {len(documents)} 個文件:\n")
        for i, doc in enumerate(documents, 1):
            upgrade_flag = "🆕" if doc['is_upgrade_related'] else "  "
            print(f"{upgrade_flag} {i:2d}. [{doc['category']:10s}] {doc['race']:20s} - {doc['title']}")
        
        if args.list_only:
            return
        
        # 如果沒有使用即時下載，則在這裡統一下載
        if args.download and not args.download:  # 避免重複下載
            print(f"\n⬇️  準備下載 {len(documents)} 個文件...")
            for doc in documents:
                scraper.download_document(doc)
        
        # 生成報告
        scraper.generate_report(documents)
    
    print("\n✅ 完成!")


if __name__ == '__main__':
    main()
