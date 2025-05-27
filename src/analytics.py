import datetime
import json
import logging
import os
# import sqlite3  # <<<<<<< REMOVE THIS LINE
# 導入 database 模組中的 db 實例
from database import db # 引入 db 實例

logger = logging.getLogger(__name__)


class Analytics:
    """分析模組，用於追蹤與分析使用者行為與系統使用狀況"""

    def __init__(self): # <<<<<<< REMOVE db_path parameter
        """
        初始化分析模組。
        不再需要 db_path，因為直接使用全局的 db 實例。
        """
        # 不再需要 self.db_path, stats_dir, self.stats_path
        # self.db_path = db_path
        # stats_dir = os.path.join(os.path.dirname(db_path), "stats")
        # os.makedirs(stats_dir, exist_ok=True)
        # self.stats_path = os.path.join(stats_dir, "usage_stats.json")

        # 直接使用 database.py 中已初始化的 db 實例
        self.db = db
        # 不再需要 _initialize_analytics_tables，因為 database.py 已經處理了所有表的初始化
        # self._initialize_analytics_tables()


    # <<<<<<< REMOVE THIS ENTIRE METHOD, as DB initialization is handled in database.py
    # def _initialize_analytics_tables(self):
    #     """初始化分析用的資料表"""
    #     try:
    #         with self._get_db_connection() as conn:
    #             cursor = conn.cursor()
    #             cursor.execute(
    #                 """
    #                 CREATE TABLE IF NOT EXISTS analytics_events (
    #                     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #                     event_type TEXT NOT NULL,
    #                     user_id TEXT,
    #                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    #                     metadata TEXT
    #                 )
    #                 """
    #             )
    #             cursor.execute(
    #                 """
    #                 CREATE TABLE IF NOT EXISTS daily_stats (
    #                     date TEXT PRIMARY KEY,
    #                     total_messages INTEGER DEFAULT 0,
    #                     unique_users INTEGER DEFAULT 0,
    #                     avg_response_time REAL DEFAULT 0.0
    #                 )
    #                 """
    #             )
    #             conn.commit()
    #     except Exception as e:
    #         logger.error("初始化分析資料表失敗: %s", e)


    def _get_db_connection(self):
        """
        建立並回傳一個資料庫連線物件。
        這裡將直接使用 database.py 中 db 實例的連線方法。
        """
        return self.db._get_connection() # <<<<<<< CHANGE THIS TO USE self.db


    def log_event(self, event_type: str, user_id: str = None, metadata: dict = None):
        """記錄一個分析事件"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO analytics_events (event_type, user_id, metadata)
                    VALUES (?, ?, ?)
                    """,
                    (event_type, user_id, json.dumps(metadata) if metadata else None),
                )
                conn.commit()
        except Exception:
            logger.exception("記錄分析事件失敗")

    def get_user_activity(self, user_id: str):
        """獲取指定使用者的活動紀錄"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT event_type, timestamp, metadata
                    FROM analytics_events
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    """,
                    (user_id,),
                )
                columns = [column[0] for column in cursor.description]
                return [
                    dict(zip(columns, row)) for row in cursor.fetchall()
                ]
        except Exception:
            logger.exception(f"獲取使用者 {user_id} 活動紀錄失敗")
            return []

    def get_overall_stats(self):
        """獲取整體使用統計數據"""
        try:
            conversation_stats = self._get_conversation_stats()
            user_stats = self._get_user_stats()
            # 合併數據並回傳
            overall_stats = {
                "conversation": conversation_stats,
                "users": user_stats,
                # 可以根據需要添加更多統計數據
            }
            return overall_stats
        except Exception:
            logger.exception("獲取整體統計數據失敗")
            return {}

    def _get_conversation_stats(self):
        """取得對話統計數據"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                # 總訊息數
                cursor.execute("SELECT COUNT(*) FROM conversations")
                total_messages = cursor.fetchone()[0]

                # 訊息角色分佈
                cursor.execute(
                    "SELECT sender_role, COUNT(*) FROM conversations GROUP BY sender_role"
                )
                role_counts = dict(cursor.fetchall())

                # 過去 24 小時的訊息數
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM conversations
                    WHERE timestamp >= DATEADD(hour, -24, GETDATE())
                    """
                )
                last_24h = cursor.fetchone()[0]

                return {
                    "total_messages": total_messages,
                    "role_distribution": role_counts,
                    "last_24h": last_24h,
                }
        except Exception:
            logger.exception("取得對話統計數據失敗")
            return {}

    def _get_user_stats(self):
        """取得使用者統計數據"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                # 總使用者數 (distinct user_id)
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM conversations")
                total_users = cursor.fetchone()[0]

                # 過去 7 天的活躍使用者數 (distinct user_id)
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT sender_id) FROM conversations
                    WHERE timestamp >= DATEADD(day, -7, GETDATE())
                    """
                )
                active_users = cursor.fetchone()[0]

                # 語言分佈
                cursor.execute(
                    "SELECT language, COUNT(*) FROM user_preferences GROUP BY language"
                )
                language_distribution = dict(cursor.fetchall())
                return {
                    "total_users": total_users,
                    "active_users": active_users,
                    "language_distribution": language_distribution,
                }
        except Exception:
            logger.exception("取得使用者統計數據失敗")
            return {}


# 實例化 Analytics 類，直接使用 database.py 中已初始化的 db
analytics = Analytics()