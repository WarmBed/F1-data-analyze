"""
F1 賽事日曆 - 2018-2024 完整賽事名稱
用於數據收集時避免 FastF1 賽程 API 問題
"""

# 2018-2024 年每個賽季的賽事名稱列表
RACE_CALENDAR = {
    2018: [
        "Australia", "Bahrain", "China", "Azerbaijan", "Spain", "Monaco",
        "Canada", "France", "Austria", "Great Britain", "Germany", "Hungary",
        "Belgium", "Italy", "Singapore", "Russia", "Japan", "United States",
        "Mexico", "Brazil", "Abu Dhabi"
    ],
    2019: [
        "Australia", "Bahrain", "China", "Azerbaijan", "Spain", "Monaco",
        "Canada", "France", "Austria", "Great Britain", "Germany", "Hungary",
        "Belgium", "Italy", "Singapore", "Russia", "Japan", "Mexico",
        "United States", "Brazil", "Abu Dhabi"
    ],
    2020: [
        "Austria", "Styria", "Hungary", "Great Britain", "70th Anniversary",
        "Spain", "Belgium", "Italy", "Tuscany", "Russia", "Eifel",
        "Portugal", "Emilia Romagna", "Turkey", "Bahrain", "Sakhir", "Abu Dhabi"
    ],
    2021: [
        "Bahrain", "Emilia Romagna", "Portugal", "Spain", "Monaco", "Azerbaijan",
        "France", "Styria", "Austria", "Great Britain", "Hungary", "Belgium",
        "Netherlands", "Italy", "Russia", "Turkey", "United States", "Mexico",
        "Brazil", "Qatar", "Saudi Arabia", "Abu Dhabi"
    ],
    2022: [
        "Bahrain", "Saudi Arabia", "Australia", "Emilia Romagna", "Miami", "Spain",
        "Monaco", "Azerbaijan", "Canada", "Great Britain", "Austria", "France",
        "Hungary", "Belgium", "Netherlands", "Italy", "Singapore", "Japan",
        "United States", "Mexico", "Brazil", "Abu Dhabi"
    ],
    2023: [
        "Bahrain", "Saudi Arabia", "Australia", "Azerbaijan", "Miami", "Monaco",
        "Spain", "Canada", "Austria", "Great Britain", "Hungary", "Belgium",
        "Netherlands", "Italy", "Singapore", "Japan", "Qatar", "United States",
        "Mexico", "Brazil", "Las Vegas", "Abu Dhabi", "Dutch"
    ],
    2024: [
        "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
        "Emilia Romagna", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
        "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
        "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
    ]
}


def get_races_for_year(year: int) -> list:
    """
    獲取指定年份的賽事列表
    
    Args:
        year: 賽季年份
        
    Returns:
        賽事名稱列表，若年份不存在則返回空列表
    """
    return RACE_CALENDAR.get(year, [])


def get_all_races(start_year: int, end_year: int) -> dict:
    """
    獲取指定年份範圍的所有賽事
    
    Args:
        start_year: 起始年份
        end_year: 結束年份
        
    Returns:
        {year: [races]} 字典
    """
    return {
        year: races 
        for year in range(start_year, end_year + 1)
        if year in RACE_CALENDAR
        for races in [RACE_CALENDAR[year]]
    }
