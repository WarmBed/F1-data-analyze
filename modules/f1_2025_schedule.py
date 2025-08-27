"""
F1 2025 賽季完整賽程配置模組
提供標準化的賽事資訊和狀態管理
"""

from datetime import datetime
from typing import Dict, List, Tuple

class F1_2025_Schedule:
    """F1 2025 賽季賽程管理類"""
    
    def __init__(self):
        # 2025年 F1 賽季完整賽程（按照官方時程表）
        self.races = [
            # 已完成賽事
            {"name": "Australia", "circuit": "Albert Park", "city": "Melbourne", "date": "2025-03-16", "status": "completed"},
            {"name": "China", "circuit": "Shanghai International Circuit", "city": "Shanghai", "date": "2025-04-20", "status": "completed"},
            {"name": "Japan", "circuit": "Suzuka International Racing Course", "city": "Suzuka", "date": "2025-04-13", "status": "completed"},
            {"name": "Bahrain", "circuit": "Bahrain International Circuit", "city": "Sakhir", "date": "2025-03-02", "status": "completed"},
            {"name": "Saudi Arabia", "circuit": "Jeddah Corniche Circuit", "city": "Jeddah", "date": "2025-03-09", "status": "completed"},
            {"name": "Miami", "circuit": "Miami International Autodrome", "city": "Miami", "date": "2025-05-04", "status": "completed"},
            {"name": "Emilia Romagna", "circuit": "Autodromo Enzo e Dino Ferrari", "city": "Imola", "date": "2025-05-18", "status": "completed"},
            {"name": "Monaco", "circuit": "Circuit de Monaco", "city": "Monte Carlo", "date": "2025-05-25", "status": "completed"},
            {"name": "Spain", "circuit": "Circuit de Barcelona-Catalunya", "city": "Barcelona", "date": "2025-06-01", "status": "completed"},
            {"name": "Canada", "circuit": "Circuit Gilles Villeneuve", "city": "Montreal", "date": "2025-06-15", "status": "completed"},
            {"name": "Austria", "circuit": "Red Bull Ring", "city": "Spielberg", "date": "2025-06-29", "status": "completed"},
            {"name": "Great Britain", "circuit": "Silverstone Circuit", "city": "Silverstone", "date": "2025-07-06", "status": "completed"},
            {"name": "Hungary", "circuit": "Hungaroring", "city": "Budapest", "date": "2025-07-20", "status": "completed"},
            {"name": "Belgium", "circuit": "Circuit de Spa-Francorchamps", "city": "Spa", "date": "2025-07-27", "status": "completed"},
            
            # 未來賽事（標記為未完成）
            {"name": "Netherlands (X)", "circuit": "Circuit Zandvoort", "city": "Zandvoort", "date": "2025-08-31", "status": "upcoming"},
            {"name": "Italy (X)", "circuit": "Autodromo Nazionale di Monza", "city": "Monza", "date": "2025-09-07", "status": "upcoming"},
            {"name": "Azerbaijan (X)", "circuit": "Baku City Circuit", "city": "Baku", "date": "2025-09-21", "status": "upcoming"},
            {"name": "Singapore (X)", "circuit": "Marina Bay Street Circuit", "city": "Singapore", "date": "2025-10-05", "status": "upcoming"},
            {"name": "United States (X)", "circuit": "Circuit of the Americas", "city": "Austin", "date": "2025-10-19", "status": "upcoming"},
            {"name": "Mexico (X)", "circuit": "Autódromo Hermanos Rodríguez", "city": "Mexico City", "date": "2025-10-26", "status": "upcoming"},
            {"name": "Brazil (X)", "circuit": "Interlagos", "city": "São Paulo", "date": "2025-11-09", "status": "upcoming"},
            {"name": "Las Vegas (X)", "circuit": "Las Vegas Street Circuit", "city": "Las Vegas", "date": "2025-11-23", "status": "upcoming"},
            {"name": "Qatar (X)", "circuit": "Lusail International Circuit", "city": "Lusail", "date": "2025-11-30", "status": "upcoming"},
            {"name": "Abu Dhabi (X)", "circuit": "Yas Marina Circuit", "city": "Abu Dhabi", "date": "2025-12-07", "status": "upcoming"},
        ]
    
    def get_all_race_names(self) -> List[str]:
        """獲取所有賽事名稱列表"""
        return [race["name"] for race in self.races]
    
    def get_completed_races(self) -> List[str]:
        """獲取已完成的賽事列表"""
        return [race["name"] for race in self.races if race["status"] == "completed"]
    
    def get_upcoming_races(self) -> List[str]:
        """獲取未來賽事列表（帶X標記）"""
        return [race["name"] for race in self.races if race["status"] == "upcoming"]
    
    def get_race_info(self, race_name: str) -> Dict:
        """獲取特定賽事的詳細資訊"""
        # 移除 (X) 標記來匹配
        clean_name = race_name.replace(" (X)", "")
        for race in self.races:
            if race["name"].replace(" (X)", "") == clean_name:
                return race
        return None
    
    def is_race_completed(self, race_name: str) -> bool:
        """檢查賽事是否已完成"""
        race_info = self.get_race_info(race_name)
        return race_info["status"] == "completed" if race_info else False
    
    def get_race_display_name(self, race_name: str) -> str:
        """獲取賽事的顯示名稱（包含狀態標記）"""
        race_info = self.get_race_info(race_name)
        if race_info:
            return race_info["name"]
        return race_name
    
    def get_default_race(self) -> str:
        """獲取預設賽事（最新完成的賽事）"""
        completed_races = [race for race in self.races if race["status"] == "completed"]
        if completed_races:
            # 返回最後一場已完成的賽事
            return completed_races[-1]["name"]
        return "Japan"  # 後備選項
    
    def validate_race_data_availability(self, race_name: str) -> Tuple[bool, str]:
        """驗證賽事數據可用性"""
        if self.is_race_completed(race_name):
            return True, f"✅ {race_name} 數據可用"
        else:
            clean_name = race_name.replace(" (X)", "")
            return False, f"❌ {clean_name} 尚未進行，無實際數據"

# 全域實例
f1_schedule = F1_2025_Schedule()

# 便捷函數
def get_all_races():
    """獲取所有賽事名稱（包含狀態標記）"""
    return f1_schedule.get_all_race_names()

def get_completed_races():
    """獲取已完成的賽事名稱"""
    return f1_schedule.get_completed_races()

def is_race_available(race_name):
    """檢查賽事數據是否可用"""
    return f1_schedule.is_race_completed(race_name)

def get_default_race():
    """獲取預設賽事"""
    return f1_schedule.get_default_race()

def validate_race_selection(race_name):
    """驗證賽事選擇的有效性"""
    return f1_schedule.validate_race_data_availability(race_name)

if __name__ == "__main__":
    # 測試模組功能
    print("🏁 F1 2025 賽季賽程")
    print("=" * 50)
    
    schedule = F1_2025_Schedule()
    
    print("📅 所有賽事:")
    for race in schedule.get_all_race_names():
        status = "✅" if schedule.is_race_completed(race.replace(" (X)", "")) else "❌"
        print(f"   {status} {race}")
    
    print(f"\n🎯 預設賽事: {schedule.get_default_race()}")
    print(f"📊 已完成賽事數量: {len(schedule.get_completed_races())}")
    print(f"🔜 未來賽事數量: {len(schedule.get_upcoming_races())}")
    
    # 測試數據可用性驗證
    print("\n🔍 數據可用性測試:")
    for test_race in ["Japan", "Singapore (X)", "Brazil (X)"]:
        available, message = schedule.validate_race_data_availability(test_race)
        print(f"   {message}")
