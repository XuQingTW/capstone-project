# src/initial_data.py
import logging
# import sqlite3 # <<<<<<< REMOVE THIS LINE
from database import db

logger = logging.getLogger(__name__)


def initialize_equipment_data():
    """
    初始化設備資料和一些基本使用者偏好資料到 SQL Server。
    會檢查資料是否存在，若存在則不重複插入。
    """
    try:
        with db._get_connection() as conn: # <<<<<<< Use db._get_connection()
            cursor = conn.cursor()

            # 檢查 equipment 表是否已有資料
            cursor.execute("SELECT COUNT(*) FROM equipment")
            if cursor.fetchone()[0] > 0:
                logger.info("設備資料已存在，略過初始化")
                return

            logger.info("初始化設備資料...")

            # 插入黏晶機
            die_bonders = [
                ("DB001", "黏晶機A1", "die_bonder", "生產線A", "運行中"),
                ("DB002", "黏晶機A2", "die_bonder", "生產線A", "運行中"),
                ("DB003", "黏晶機B1", "die_bonder", "生產線B", "待機中"),
            ]
            # 插入打線機
            wire_bonders = [
                ("WB001", "打線機A1", "wire_bonder", "生產線A", "運行中"),
                ("WB002", "打線機A2", "wire_bonder", "生產線A", "閒置中"),
                ("WB003", "打線機B1", "wire_bonder", "生產線B", "維護中"),
                ("WB004", "打線機B2", "wire_bonder", "生產線B", "運行中"),
            ]
            # 插入切割機
            dicers = [
                ("DC001", "切割機C1", "dicer", "生產線C", "運行中"),
                ("DC002", "切割機C2", "dicer", "生產線C", "運行中"),
            ]

            all_equipments = die_bonders + wire_bonders + dicers

            # 批量插入設備資料到 equipment 表
            # 注意：SQL Server 不支持 INSERT INTO ... VALUES (...) ON CONFLICT IGNORE
            # 而是使用 IF NOT EXISTS 或 MERGE 語句。
            # 但在初始化數據時，我們可以簡單地插入，因為前面已經檢查過 count > 0
            for eq_id, name, eq_type, location, status in all_equipments:
                try:
                    cursor.execute(
                        """
                        INSERT INTO equipment (equipment_id, name, type, location, status)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (eq_id, name, eq_type, location, status),
                    )
                except Exception as e:
                    logger.warning(f"插入設備 {eq_id} 失敗 (可能已存在): {e}")


            # 初始化一個預設管理員使用者 (如果不存在的話)
            # 假設這裡的 user_id 'U1234567890abcdefghijklmnopqrstu1' 是一個範例 LINE User ID
            # 您應該將其替換為您自己的 LINE User ID 以便接收測試通知
            default_admin_id = "U1234567890abcdefghijklmnopqrstu1" # <<<<<<< IMPORTANT: REPLACE WITH YOUR LINE USER ID

            cursor.execute(
                "SELECT COUNT(*) FROM user_preferences WHERE user_id = ?",
                (default_admin_id,)
            )
            if cursor.fetchone()[0] == 0:
                logger.info(f"初始化管理員使用者 {default_admin_id} 資料...")
                cursor.execute(
                    """
                    INSERT INTO user_preferences (user_id, language, is_admin, responsible_area)
                    VALUES (?, ?, ?, ?)
                    """,
                    (default_admin_id, 'zh-Hant', 1, 'all'), # 設置為管理員，負責所有區域
                )
            else:
                logger.info(f"管理員使用者 {default_admin_id} 資料已存在，略過初始化")


            # 這裡不再需要插入 equipment_metrics, equipment_operation_logs, user_equipment_subscriptions 的資料
            # 因為這些表已移除或已通過其他方式處理（如模擬數據或 abormal_logs）

            conn.commit()
            logger.info("設備資料初始化完成。")

    except Exception:
        logger.exception("初始化設備資料失敗")