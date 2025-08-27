#!/usr/bin/env python3
"""
F1 Analysis CLI - 簡化主程式 (使用統一函數映射器)
F1 Analysis CLI - Simplified Main Program (Using Unified Function Mapper)
版本: 6.0 (統一映射器版)
作者: F1 Analysis Team

完全使用統一函數映射器的簡化主程式
符合核心開發原則：參數化執行、無互動模式、統一介面
"""

import os
import sys
import argparse
from typing import Optional, Union

# 確保 modules 目錄在 Python 路徑中
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, 'modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

def create_argument_parser():
    """創建命令行參數解析器"""
    parser = argparse.ArgumentParser(
        description="F1 遙測分析系統 - 統一映射器版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
    python %(prog)s -y 2025 -r Japan -s R -f 1
    python %(prog)s -y 2024 -r Bahrain -s Q -f 14.1
    python %(prog)s --list-races
    python %(prog)s -f 52  # API 健康檢查
        """
    )
    
    parser.add_argument('-y', '--year', type=int, default=2025,
                       help='賽季年份 (2024 或 2025，預設: 2025)')
    parser.add_argument('-r', '--race', type=str, default='Japan',
                       help='賽事名稱 (預設: Japan)')
    parser.add_argument('-s', '--session', type=str, default='R',
                       help='賽段類型: R=正賽, Q=排位賽, FP1/FP2/FP3=練習賽, S=衝刺賽 (預設: R)')
    parser.add_argument('-f', '--function', type=str,
                       help='分析功能編號 (1-52 或子功能如 4.1, 14.1)')
    parser.add_argument('--list-races', action='store_true',
                       help='列出支援的賽事')
    parser.add_argument('--debug', action='store_true',
                       help='啟用除錯模式')
    
    return parser

def run_analysis(year: int, race: str, session: str, function_id: Union[int, str]):
    """執行分析功能
    
    Args:
        year: 賽季年份
        race: 賽事名稱  
        session: 賽段類型
        function_id: 功能編號
        
    Returns:
        bool: 執行是否成功
    """
    try:
        print(f"🚀 開始執行分析...")
        print(f"   年份: {year}")
        print(f"   賽事: {race}")
        print(f"   賽段: {session}")
        print(f"   功能: {function_id}")
        print("=" * 50)
        
        # 導入統一函數映射器
        from modules.function_mapper import F1AnalysisFunctionMapper
        from modules.compatible_data_loader import CompatibleF1DataLoader
        from modules.compatible_f1_analysis_instance import create_f1_analysis_instance
        
        # 系統功能不需要載入數據
        system_functions = [18, 19, 20, 21, 22, 49, 50, 51, 52]
        
        if isinstance(function_id, str):
            try:
                func_num = int(function_id)
                need_data = func_num not in system_functions
            except ValueError:
                need_data = True  # 子功能通常需要數據
        else:
            need_data = function_id not in system_functions
        
        # 初始化組件
        data_loader = None
        f1_analysis_instance = None
        dynamic_team_mapping = None
        
        if need_data:
            # 初始化數據載入器
            print("📥 載入賽事數據...")
            data_loader = CompatibleF1DataLoader()
            
            # 載入數據 (使用正確的方法名稱)
            success = data_loader.load_race_data(year, race, session)
            if not success:
                print("❌ 數據載入失敗")
                return False
            
            # 創建 F1 分析實例
            print("🔧 創建分析實例...")
            f1_analysis_instance = create_f1_analysis_instance(data_loader)
            dynamic_team_mapping = getattr(f1_analysis_instance, 'dynamic_team_mapping', None)
            
            print("✅ 數據載入完成")
        
        # 創建統一函數映射器
        function_mapper = F1AnalysisFunctionMapper(
            data_loader=data_loader,
            dynamic_team_mapping=dynamic_team_mapping,
            f1_analysis_instance=f1_analysis_instance
        )
        
        # 執行分析功能
        print(f"⚡ 執行功能 {function_id}...")
        result = function_mapper.execute_function_by_number(function_id)
        
        # 處理結果
        if result.get("success", False):
            print("=" * 50)
            print(f"✅ {result.get('message', '分析完成')}")
            if "data" in result:
                print(f"📊 返回數據類型: {type(result['data'])}")
            print("=" * 50)
            return True
        else:
            print("=" * 50)
            print(f"❌ {result.get('message', '分析失敗')}")
            if "error" in result:
                print(f"錯誤詳情: {result['error']}")
            print("=" * 50)
            return False
            
    except Exception as e:
        print("=" * 50)
        print(f"❌ 執行分析功能 {function_id} 時發生錯誤: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        print("=" * 50)
        return False

def list_supported_races():
    """列出支援的賽事"""
    print("\n🏁 F1 分析系統支援的賽事列表")
    print("=" * 60)
    
    races_2024 = [
        "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
        "Emilia Romagna", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
        "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
        "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
    ]
    
    races_2025 = [
        "Australia", "China", "Japan", "Bahrain", "Saudi Arabia", "Miami",
        "Monaco", "Spain", "Canada", "Austria", "Great Britain", "Hungary",
        "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
        "United States", "Mexico", "Brazil", "Qatar", "Abu Dhabi"
    ]
    
    print("📅 2024 賽季:")
    for i, race in enumerate(races_2024, 1):
        print(f"   {i:2d}. {race}")
    
    print("\n📅 2025 賽季:")
    for i, race in enumerate(races_2025, 1):
        print(f"   {i:2d}. {race}")
    
    print("\n💡 功能編號 (1-52):")
    print("   1. 降雨強度分析")
    print("   2. 賽道位置分析")
    print("   3. 進站策略分析")
    print("   4. 事故分析")
    print("   5. 單一車手綜合分析")
    print("   6. 單一車手詳細遙測分析")
    print("   7. 車手對比分析")
    print("   14.1. 車手數據統計總覽")
    print("   14.2. 車手遙測資料統計")
    print("   14.3. 車手超車分析")
    print("   14.4. 最速圈排名分析")
    print("   52. API 健康檢查")
    print("   ...")

def main():
    """主程式進入點"""
    global args
    
    try:
        # 解析命令行參數
        parser = create_argument_parser()
        args = parser.parse_args()
        
        # 列出賽事
        if args.list_races:
            list_supported_races()
            return
        
        # 檢查功能編號
        if not args.function:
            print("❌ 請指定分析功能編號 (-f)")
            print("使用 --help 查看使用說明")
            print("使用 --list-races 查看支援的賽事和功能")
            sys.exit(1)
        
        # 檢查 modules 目錄
        if not os.path.exists(modules_dir):
            print(f"❌ 找不到 modules 目錄: {modules_dir}")
            print("請確保在正確的工作目錄中運行此程式")
            sys.exit(1)
        
        # 執行分析
        success = run_analysis(args.year, args.race, args.session, args.function)
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 程式已被使用者中斷，再見！")
    except Exception as e:
        print(f"\n❌ 程式執行錯誤: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
