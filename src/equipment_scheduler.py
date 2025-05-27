import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import time # For time.sleep if needed for testing

from equipment_monitor import EquipmentMonitor
from config import Config # 引入 Config 來獲取排程間隔

logger = logging.getLogger(__name__)

# 初始化設備監控器
equipment_monitor = EquipmentMonitor()

# 初始化排程器
scheduler = BackgroundScheduler()

def monitor_all_equipment_job():
    """
    排程器將執行的任務：監控所有設備。
    """
    logger.info(f"排程任務執行: 監控所有設備 ({datetime.now()})")
    try:
        equipment_monitor.monitor_equipment()
    except Exception as e:
        logger.error(f"監控設備任務執行失敗: {e}")


def start_scheduler():
    """
    啟動排程器並設定監控任務。
    """
    # 檢查是否已存在相同的任務，避免重複添加
    if not scheduler.get_job("monitor_all_equipment"):
        # 從 Config 中獲取監控間隔，預設為 5 分鐘
        monitor_interval_minutes = Config.MONITOR_INTERVAL_MINUTES
        logger.info(f"設定設備監控任務，每 {monitor_interval_minutes} 分鐘執行一次。")
        
        # 添加監控任務
        scheduler.add_job(
            monitor_all_equipment_job,
            trigger=IntervalTrigger(minutes=monitor_interval_minutes),
            id="monitor_all_equipment",  # 設定唯一的任務 ID
            name="Monitor All Equipment",
            next_run_time=datetime.now() # 立即執行一次，然後按間隔執行
        )
    else:
        logger.info("設備監控任務已存在，不重複添加。")

    if not scheduler.running:
        logger.info("啟動排程器...")
        scheduler.start()
    else:
        logger.info("排程器已在運行中。")


# 可以在此處添加一個簡單的測試，確保排程器可以啟動
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # 確保在獨立運行時有日誌輸出
    
    print("啟動設備監控排程器範例...")
    start_scheduler()
    
    try:
        # 讓主執行緒保持運行，以便排程器可以在後台工作
        while True:
            time.sleep(2) # 每隔 2 秒檢查一次，保持進程活躍
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("排程器已關閉。")