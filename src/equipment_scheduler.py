# src/equipment_scheduler.py
import schedule
import time
import threading
import logging
from src.equipment_monitor import EquipmentMonitor

logger = logging.getLogger(__name__)

monitor = EquipmentMonitor()

def run_scheduler():
    """執行排程任務"""
    # 每隔 5 分鐘檢查一次設備狀態
    schedule.every(5).minutes.do(monitor.check_all_equipment)
    
    logger.info("設備監控排程器已啟動")
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    """以背景執行緒啟動排程器"""
    thread = threading.Thread(target=run_scheduler)
    thread.daemon = True
    thread.start()
    logger.info("設備監控背景執行緒已啟動")

# 提供手動檢查函數，方便測試
def manual_check():
    """手動執行設備檢查"""
    monitor.check_all_equipment()