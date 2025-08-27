#!/usr/bin/env python3
"""
車手選擇工具模組
Driver Selection Utilities Module

提供統一的車手選擇功能，適用於所有F1分析模組
"""

from prettytable import PrettyTable

def get_drivers_list(session):
    """
    統一獲取車手列表的方法
    
    Args:
        session: FastF1 Session對象
        
    Returns:
        list: 車手代碼列表，如 ['VER', 'HAM', 'LEC', ...]
    """
    try:
        # 方法1: 從session.results獲取（最可靠）
        if hasattr(session, 'results') and session.results is not None:
            # results的index包含車手代碼
            drivers_list = []
            for driver_number in session.results.index:
                try:
                    driver_info = session.get_driver(driver_number)
                    if hasattr(driver_info, 'Abbreviation'):
                        abbr = driver_info.Abbreviation
                        if abbr and abbr not in drivers_list:
                            drivers_list.append(abbr)
                except:
                    continue
            
            if drivers_list:
                return sorted(drivers_list)
        
        # 方法2: 從session.drivers獲取（如果是車手代碼列表）
        if hasattr(session, 'drivers') and session.drivers:
            drivers = session.drivers
            if isinstance(drivers, list):
                # 檢查是否已經是車手代碼
                if all(isinstance(d, str) and len(d) == 3 for d in drivers):
                    return sorted(drivers)
        
        # 方法3: 從laps數據獲取
        if hasattr(session, 'laps') and session.laps is not None:
            if 'Driver' in session.laps.columns:
                unique_drivers = session.laps['Driver'].dropna().unique()
                return sorted([d for d in unique_drivers if isinstance(d, str)])
        
        # 如果都失敗了，返回空列表
        print("[WARNING] 無法獲取車手列表")
        return []
        
    except Exception as e:
        print(f"[ERROR] 獲取車手列表錯誤: {e}")
        return []

def get_driver_info(session, driver_code):
    """
    獲取車手詳細信息
    
    Args:
        session: FastF1 Session對象
        driver_code: 車手代碼，如 'VER'
        
    Returns:
        dict: 車手信息字典
    """
    try:
        # 通過車手代碼找到對應的車手編號
        if hasattr(session, 'results'):
            for driver_number in session.results.index:
                try:
                    driver_info = session.get_driver(driver_number)
                    if hasattr(driver_info, 'Abbreviation') and driver_info.Abbreviation == driver_code:
                        return {
                            'abbreviation': driver_info.Abbreviation,
                            'full_name': getattr(driver_info, 'FullName', driver_code),
                            'first_name': getattr(driver_info, 'FirstName', ''),
                            'last_name': getattr(driver_info, 'LastName', ''),
                            'team_name': getattr(driver_info, 'TeamName', 'Unknown'),
                            'driver_number': getattr(driver_info, 'DriverNumber', 'N/A'),
                            'team_color': getattr(driver_info, 'TeamColor', '000000')
                        }
                except:
                    continue
        
        # 如果找不到，返回基本信息
        return {
            'abbreviation': driver_code,
            'full_name': driver_code,
            'first_name': '',
            'last_name': '',
            'team_name': 'Unknown',
            'driver_number': 'N/A',
            'team_color': '000000'
        }
        
    except Exception as e:
        print(f"[ERROR] 獲取車手信息錯誤: {e}")
        return {
            'abbreviation': driver_code,
            'full_name': driver_code,
            'first_name': '',
            'last_name': '',
            'team_name': 'Unknown',
            'driver_number': 'N/A',
            'team_color': '000000'
        }

def display_drivers_table(session, drivers_list=None):
    """
    顯示車手選擇表格
    
    Args:
        session: FastF1 Session對象
        drivers_list: 車手列表，如果為None則自動獲取
        
    Returns:
        list: 車手代碼列表
    """
    try:
        if drivers_list is None:
            drivers_list = get_drivers_list(session)
        
        if not drivers_list:
            print("[ERROR] 無車手數據可顯示")
            return []
        
        print(f"\n[LIST] 可用車手列表 ({len(drivers_list)} 位):")
        driver_table = PrettyTable()
        driver_table.field_names = ["編號", "車手縮寫", "全名", "車隊", "車號"]
        driver_table.align = "l"
        
        for idx, driver_code in enumerate(drivers_list, 1):
            driver_info = get_driver_info(session, driver_code)
            driver_table.add_row([
                idx,
                driver_info['abbreviation'],
                driver_info['full_name'],
                driver_info['team_name'],
                driver_info['driver_number']
            ])
        
        print(driver_table)
        return drivers_list
        
    except Exception as e:
        print(f"[ERROR] 顯示車手表格錯誤: {e}")
        return []

def get_user_driver_selection(session, drivers_list=None):
    """
    獲取用戶選擇的車手
    
    Args:
        session: FastF1 Session對象
        drivers_list: 車手列表，如果為None則自動獲取
        
    Returns:
        str: 選擇的車手代碼，如 'VER'
    """
    try:
        if drivers_list is None:
            drivers_list = get_drivers_list(session)
        
        if not drivers_list:
            print("[ERROR] 無車手數據可選擇")
            return None
        
        # 顯示車手表格
        drivers_list = display_drivers_table(session, drivers_list)
        
        # 讓用戶選擇車手
        while True:
            try:
                choice = input(f"\n請選擇車手編號 (1-{len(drivers_list)}) 或直接輸入車手縮寫: ").strip()
                
                if choice.isdigit():
                    idx = int(choice)
                    if 1 <= idx <= len(drivers_list):
                        selected_driver = drivers_list[idx - 1]
                        break
                    else:
                        print(f"[ERROR] 請輸入有效的編號 (1-{len(drivers_list)})")
                        continue
                else:
                    # 直接輸入車手縮寫
                    choice_upper = choice.upper()
                    if choice_upper in drivers_list:
                        selected_driver = choice_upper
                        break
                    else:
                        print(f"[ERROR] 車手縮寫 '{choice}' 不存在，請重新輸入")
                        continue
                        
            except KeyboardInterrupt:
                print("\n[WARNING] 用戶取消操作")
                return None
            except Exception as e:
                print(f"[ERROR] 輸入處理錯誤: {e}")
                continue
        
        print(f"[SUCCESS] 已選擇車手: {selected_driver}")
        return selected_driver
        
    except Exception as e:
        print(f"[ERROR] 車手選擇錯誤: {e}")
        return None

# 為向後兼容提供的便利函數
def get_drivers_info_dict(session):
    """
    獲取所有車手的信息字典（為兼容舊代碼）
    
    Args:
        session: FastF1 Session對象
        
    Returns:
        dict: {driver_code: driver_info_dict, ...}
    """
    try:
        drivers_list = get_drivers_list(session)
        drivers_info = {}
        
        for driver_code in drivers_list:
            drivers_info[driver_code] = get_driver_info(session, driver_code)
        
        return drivers_info
        
    except Exception as e:
        print(f"[ERROR] 獲取車手信息字典錯誤: {e}")
        return {}

# 測試函數
if __name__ == "__main__":
    print("🧪 車手選擇工具模組測試")
    print("此模組需要在完整的F1分析系統中運行")
