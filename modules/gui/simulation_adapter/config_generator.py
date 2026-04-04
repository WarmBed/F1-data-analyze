
import json
import os

class AcConfigGenerator:
    """
    AC 設定檔生成器
    負責將融合後的參數轉換為 AC 可讀的 JSON 和 INI 格式。
    """
    def __init__(self, output_dir='ac_sim_output'):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_json(self, grid_data, filename='sim_summary.json'):
        """
        生成 JSON 摘要文件
        """
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(grid_data, f, indent=4, ensure_ascii=False)
            print(f"[OK] JSON summary saved to: {filepath}")
        except Exception as e:
            print(f"[ERROR] Error saving JSON: {e}")

    def generate_ini(self, grid_data, filename='entry_list.ini'):
        """
        生成 AC Server 專用的 entry_list.ini
        """
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for idx, car in enumerate(grid_data):
                    f.write(f"[CAR_{idx}]\n")
                    f.write(f"DRIVERNAME={car['driver']}\n")
                    f.write(f"TEAM={car['team']}\n")
                    f.write(f"MODEL={car.get('model', 'rss_formula_hybrid_x_2026')}\n")
                    f.write(f"SKIN={car.get('skin', 'default')}\n")
                    f.write(f"AI_LEVEL={car['sim_params']['ai_level']}\n")
                    f.write(f"AGGRESSION={car['sim_params']['aggression']}\n")
                    f.write(f"BALLAST={car['sim_params']['ballast']}\n")
                    f.write(f"RESTRICTOR={car['sim_params']['restrictor']}\n")
                    f.write("\n")
            print(f"[OK] AC INI config saved to: {filepath}")
        except Exception as e:
            print(f"[ERROR] Error saving INI: {e}")
