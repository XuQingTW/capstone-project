# test_equipment_alert.py
import sqlite3
import logging
from src.database import db
from src.equipment_monitor import EquipmentMonitor

logging.basicConfig(level=logging.INFO)

def simulate_abnormal_metric():
    """模擬異常指標以測試警告功能"""
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # 將黏晶機溫度設為異常高值
            cursor.execute("""
                INSERT INTO equipment_metrics
                (equipment_id, metric_type, value, threshold_min, threshold_max, unit)
                VALUES ('DB001', '溫度', 32.5, 18.0, 28.0, '°C')
            """)
            
            # 將打線機金絲張力設為異常低值
            cursor.execute("""
                INSERT INTO equipment_metrics
                (equipment_id, metric_type, value, threshold_min, threshold_max, unit)
                VALUES ('WB001', '金絲張力', 12.5, 15.0, 22.0, 'cN')
            """)
            
            # 將切割機良率設為異常低值
            cursor.execute("""
                INSERT INTO equipment_metrics
                (equipment_id, metric_type, value, threshold_min, threshold_max, unit)
                VALUES ('DC001', '良率', 92.5, 98.0, NULL, '%')
            """)
            
            conn.commit()
            print("已成功模擬異常指標")
            
            # 立即運行監控檢查
            monitor = EquipmentMonitor()
            monitor.check_all_equipment()
            print("已完成設備檢查，檢查 LINE 是否收到通知")
            
    except Exception as e:
        print(f"測試失敗: {e}")

if __name__ == "__main__":
    simulate_abnormal_metric()