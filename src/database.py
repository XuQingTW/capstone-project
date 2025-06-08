import logging
import pyodbc
from config import Config


logger = logging.getLogger(__name__)


class Database:
    """處理對話記錄與使用者偏好儲存的資料庫處理程序"""

    def __init__(self, server=None, database=None):
        """初始化資料庫連線"""
        resolved_server = server if server is not None else Config.DB_SERVER
        resolved_database = database if database is not None else Config.DB_NAME
        self.connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={resolved_server};"
            f"DATABASE={resolved_database};"
            "Trusted_Connection=yes;"
        )
        self._initialize_db()

    def _get_connection(self):
        """建立並回傳資料庫連線"""
        return pyodbc.connect(self.connection_string)

    def _initialize_db(self):
        """
        如果資料表尚未存在，則建立必要的表格。
        此版本根據推斷的 CSV 檔案欄位定義表格，並移除所有主鍵和外鍵。
        所有欄位預設允許 NULL。欄位名稱請務必與您的 CSV 表頭核對。
        """
        try:
            with self._get_connection() as conn:
                init_cur = conn.cursor()

                # 1. user_preferences (來自 user_preferences.csv)
                user_preferences_cols = """
                    [user_id] NVARCHAR(255) NULL,
                    [language] VARCHAR(50) NULL,
                    [role] NVARCHAR(50) NULL,
                    [is_admin] BIT NULL,
                    [responsible_area] NVARCHAR(255) NULL,
                    [created_at] DATETIME2 NULL,
                    [display_name] NVARCHAR(255) NULL, -- 保持 255，通常夠用
                    [email] NVARCHAR(255) NULL,         -- 保持 255，通常夠用
                    [last_active] DATETIME2 NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "user_preferences",
                    user_preferences_cols
                )

                # 2. equipment (來自 equipment.csv)
                equipment_cols = """
                    [id] INT NULL,
                    [equipment_id] NVARCHAR(255) NULL,
                    [name] NVARCHAR(255) NULL,
                    [eq_type] NVARCHAR(255) NULL,
                    [location] NVARCHAR(255) NULL,
                    [status] NVARCHAR(255) NULL, -- 保持 255
                    [last_updated] DATETIME2 NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "equipment",
                    equipment_cols
                )

                # 3. conversations (來自 conversations.csv)
                conversations_cols = """
                    [message_id] NVARCHAR(255) NULL,
                    [sender_id] NVARCHAR(255) NULL,
                    [receiver_id] NVARCHAR(255) NULL,
                    [sender_role] NVARCHAR(50) NULL,
                    [content] NVARCHAR(MAX) NULL, -- 保持 MAX，對話內容可能很長
                    [timestamp] DATETIME2 NULL DEFAULT GETDATE()
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "conversations",
                    conversations_cols
                )

                # 4. user_equipment_subscriptions (來自 user_equipment_subscriptions.csv)
                user_equipment_subscriptions_cols = """
                    [subscription_id] INT NULL,
                    [user_id] NVARCHAR(255) NULL,
                    [equipment_id] NVARCHAR(255) NULL,
                    [notification_types] NVARCHAR(255) NULL,
                    [subscribed_at] DATETIME2 NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "user_equipment_subscriptions",
                    user_equipment_subscriptions_cols
                )

                # 5. alert_history (來自 alert_history.csv) - message, resolution_notes 改為 NVARCHAR(MAX)
                alert_history_cols = """
                    [id] INT NULL,
                    [equipment_id] NVARCHAR(255) NULL,
                    [alert_type] NVARCHAR(255) NULL,
                    [severity] NVARCHAR(255) NULL,
                    [message] NVARCHAR(MAX) NULL, -- 改回 NVARCHAR(MAX)
                    [is_resolved] BIT NULL DEFAULT 0,
                    [created_at] DATETIME2 NULL,
                    [resolved_at] DATETIME2 NULL,
                    [resolved_by] NVARCHAR(255) NULL,
                    [resolution_notes] NVARCHAR(MAX) NULL -- 改回 NVARCHAR(MAX)
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "alert_history",
                    alert_history_cols
                )

                # 6. equipment_metrics (實時監測數據)
                equipment_metrics_cols = """
                    [id] INT IDENTITY(1,1) NOT NULL,
                    [equipment_id] NVARCHAR(255) NULL,
                    [metric_type] NVARCHAR(255) NULL,
                    [status] NVARCHAR(50) NULL, -- 保持 50，通常夠用
                    [value] FLOAT NULL,
                    [threshold_min] FLOAT NULL,
                    [threshold_max] FLOAT NULL,
                    [unit] NVARCHAR(50) NULL,   -- 保持 50，通常夠用
                    [timestamp] DATETIME2 NULL DEFAULT GETDATE()
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "equipment_metrics",
                    equipment_metrics_cols
                )

                # 7.  equipment_metric_thresholds (設備標準值) 
                equipment_metric_thresholds_cols = """
                    [metric_type] NVARCHAR(50) NOT NULL, -- 保持 50
                    [normal_value] FLOAT NULL,
                    [warning_min] FLOAT NULL,
                    [warning_max] FLOAT NULL,
                    [critical_min] FLOAT NULL,
                    [critical_max] FLOAT NULL,
                    [emergency_min] FLOAT NULL,
                    [emergency_max] FLOAT NULL,
                    [emergency_op] NVARCHAR(10) NULL,    -- 保持 10
                    [last_updated] DATETIME2 NULL DEFAULT GETDATE()
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "equipment_metric_thresholds",
                    equipment_metric_thresholds_cols
                )

                # 8. error_logs (來自 simulated_data - 異常紀錄.csv) - resolution_notes 改為 NVARCHAR(MAX)
                error_logs_cols = """
                    [log_date] DATETIME2 NULL,
                    [error_id] NVARCHAR(255) NULL,
                    [equipment_id] NVARCHAR(255) NULL,
                    [deformation_mm] FLOAT NULL,
                    [rpm] INT NULL,
                    [event_time] DATETIME2 NULL,
                    [detected_anomaly_type] NVARCHAR(255) NULL,
                    [downtime_duration] NVARCHAR(255) NULL,
                    [resolved_at] DATETIME2 NULL,
                    [resolution_notes] NVARCHAR(MAX) NULL -- 改回 NVARCHAR(MAX)
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "error_logs",
                    error_logs_cols
                )

                # 9. stats_abnormal_monthly (來自 各異常統計(月).csv)
                stats_abnormal_monthly_cols = """
                    [equipment_id] NVARCHAR(255) NULL,
                    [year] INT NULL,
                    [month] INT NULL,
                    [detected_anomaly_type] NVARCHAR(255) NULL, -- 保持 255
                    [downtime_duration] NVARCHAR(255) NULL,     -- 保持 255
                    [downtime_rate_percent] NVARCHAR(255) NULL, -- 保持 255
                    [description] NVARCHAR(MAX) NULL            -- 改為 NVARCHAR(MAX)，說明可能很長
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "stats_abnormal_monthly",
                    stats_abnormal_monthly_cols
                )

                # 10. stats_abnormal_quarterly (來自 各異常統計(季).csv)
                stats_abnormal_quarterly_cols = """
                    [equipment_id] NVARCHAR(255) NULL,
                    [year] INT NULL,
                    [quarter] INT NULL,
                    [detected_anomaly_type] NVARCHAR(255) NULL,
                    [downtime_duration] NVARCHAR(255) NULL,
                    [downtime_rate_percent] NVARCHAR(255) NULL,
                    [description] NVARCHAR(MAX) NULL            -- 改為 NVARCHAR(MAX)
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "stats_abnormal_quarterly",
                    stats_abnormal_quarterly_cols
                )

                # 11. stats_abnormal_yearly (來自 各異常統計(年).csv)
                stats_abnormal_yearly_cols = """
                    [equipment_id] NVARCHAR(255) NULL,
                    [year] INT NULL,
                    [detected_anomaly_type] NVARCHAR(255) NULL,
                    [downtime_duration] NVARCHAR(255) NULL,
                    [downtime_rate_percent] NVARCHAR(255) NULL,
                    [description] NVARCHAR(MAX) NULL            -- 改為 NVARCHAR(MAX)
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "stats_abnormal_yearly",
                    stats_abnormal_yearly_cols
                )

                # 12. stats_operational_monthly (來自 運作統計(月).csv)
                stats_operational_monthly_cols = """
                    [equipment_id] NVARCHAR(255) NULL,
                    [month] INT NULL,
                    [total_operation_duration] NVARCHAR(255) NULL, -- 保持 255
                    [total_downtime_duration] NVARCHAR(255) NULL, -- 保持 255
                    [downtime_rate_percent] NVARCHAR(255) NULL,   -- 保持 255
                    [description] NVARCHAR(MAX) NULL              -- 改為 NVARCHAR(MAX)
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "stats_operational_monthly",
                    stats_operational_monthly_cols
                )

                # 13. stats_operational_quarterly (來自 運作統計(季).csv)
                stats_operational_quarterly_cols = """
                    [equipment_id] NVARCHAR(255) NULL,
                    [year] INT NULL,
                    [quarter] INT NULL,
                    [total_operation_duration] NVARCHAR(255) NULL,
                    [total_downtime_duration] NVARCHAR(255) NULL,
                    [downtime_rate_percent] NVARCHAR(255) NULL,
                    [description] NVARCHAR(MAX) NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "stats_operational_quarterly",
                    stats_operational_quarterly_cols
                )

                # 14. stats_operational_yearly (來自 運作統計(年).csv)
                stats_operational_yearly_cols = """
                    [equipment_id] NVARCHAR(255) NULL,
                    [year] INT NULL,
                    [total_operation_duration] NVARCHAR(255) NULL,
                    [total_downtime_duration] NVARCHAR(255) NULL,
                    [downtime_rate_percent] NVARCHAR(255) NULL,
                    [description] NVARCHAR(MAX) NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "stats_operational_yearly",
                    stats_operational_yearly_cols
                )

                conn.commit()
            logger.info(
                "資料庫表格初始化/檢查完成 "
                "(所有表格已移除主鍵/外鍵約束)。"
            )
            logger.warning(
                "請務必檢查每個表格的欄位定義是否完全符合您 "
                "CSV 檔案的實際欄位和預期資料類型。"
            )
        except pyodbc.Error as e:
            logger.exception(f"資料庫初始化期間發生 pyodbc 錯誤: {e}")
            raise
        except Exception as ex:
            logger.exception(f"資料庫初始化期間發生非預期錯誤: {ex}")
            raise

    def add_message(self, sender_id, receiver_id, sender_role, content):
        """加入一筆新的對話記錄（包含發送者角色）"""
        try:
            with self._get_connection() as conn:
                conv_add_cur = conn.cursor()
                conv_add_cur.execute(
                    """
                    INSERT INTO conversations
                        (sender_id, receiver_id, sender_role, content)
                    VALUES (?, ?, ?, ?);
                    """,
                    (sender_id, receiver_id, sender_role, content)
                )
                conn.commit()
                return True
        except pyodbc.Error as e:
            logger.exception(f"新增對話記錄失敗: {e}")
            return False

    def get_conversation_history(self, sender_id, limit=10):
        """取得指定 sender 的對話記錄"""
        try:
            with self._get_connection() as conn:
                conv_hist_cur = conn.cursor()
                # 注意：原本您的程式碼這裡的 sender_id 應該是 user_id，此處保持與原程式碼一致的命名
                # 但通常對話歷史是針對某個用戶 (user_id)
                # 如果 sender_id 就是 user_id，那沒問題
                conv_hist_cur.execute(
                    """
                    SELECT TOP (?) sender_role, content
                    FROM conversations
                    WHERE sender_id = ?
                    ORDER BY timestamp DESC;
                    """,
                    (limit, sender_id)
                )
                # 從資料庫讀取是 DESC，但通常聊天室顯示是 ASC (舊的在上面)
                # 所以先 reverse
                messages = [
                    # 統一鍵名為 'role' 以符合 OpenAI 格式
                    {"role": sender_role, "content": content}
                    for sender_role, content in conv_hist_cur.fetchall()
                ]
                messages.reverse()  # 反轉順序，讓最新的訊息在最後
                return messages
        except pyodbc.Error as e:
            logger.exception(f"取得對話記錄失敗: {e}")
            return []

    def get_conversation_stats(self):
        """取得對話記錄統計資料"""
        try:
            with self._get_connection() as conn:
                conv_stats_cur = conn.cursor()
                conv_stats_cur.execute("SELECT COUNT(*) FROM conversations;")
                total_messages = conv_stats_cur.fetchone()[0]
                conv_stats_cur.execute(
                    "SELECT COUNT(DISTINCT sender_id) FROM conversations;"
                )
                unique_senders = conv_stats_cur.fetchone()[0]
                conv_stats_cur.execute(
                    """
                    SELECT COUNT(*) FROM conversations
                    WHERE timestamp >= DATEADD(day, -1, GETDATE());
                    """
                )
                last_24h = conv_stats_cur.fetchone()[0]
                conv_stats_cur.execute(
                    "SELECT sender_role, COUNT(*) FROM conversations "
                    "GROUP BY sender_role;"
                )
                role_counts = dict(conv_stats_cur.fetchall())
                return {
                    "total_messages": total_messages,
                    "unique_users": unique_senders,
                    "last_24h": last_24h,
                    "user_messages": role_counts.get("user", 0),
                    "assistant_messages": role_counts.get("assistant", 0),
                    "system_messages": role_counts.get("system", 0),
                    "other_messages": sum(
                        count for role, count in role_counts.items()
                        if role not in ["user", "assistant", "system"]
                    )
                }
        except pyodbc.Error as e:
            logger.exception(f"取得對話統計資料失敗: {e}")
            return {
                "total_messages": 0,
                "unique_users": 0,
                "last_24h": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "system_messages": 0,
                "other_messages": 0,
            }

    def get_recent_conversations(self, limit=20):
        """取得最近的對話列表（依 sender_id，通常是 user_id）"""
        try:
            with self._get_connection() as conn:
                recent_conv_cur = conn.cursor()
                # 這裡的 sender_id 實際上是指 user_id
                sql_query = """
                    SELECT DISTINCT TOP (?)
                        c.sender_id,   -- 這其實是 user_id
                        p.language,
                        MAX(c.timestamp) as last_activity_ts   -- 改名以區分 last_message 內容
                    FROM conversations c
                    LEFT JOIN user_preferences p ON c.sender_id = p.user_id   -- 連接基於 sender_id = user_id
                    GROUP BY c.sender_id, p.language
                    ORDER BY last_activity_ts DESC;
                """
                recent_conv_cur.execute(sql_query, (limit,))
                results = []
                for user_id_val, language, timestamp_val in recent_conv_cur.fetchall():
                    # sender_id 即 user_id
                    recent_conv_cur.execute(
                        "SELECT COUNT(*) FROM conversations WHERE sender_id = ?;",
                        (user_id_val,)
                    )
                    message_count = recent_conv_cur.fetchone()[0]
                    recent_conv_cur.execute(
                        """
                        SELECT TOP 1 content FROM conversations
                        WHERE sender_id = ? AND sender_role = 'user'   -- 通常看 user 的最後一句話
                        ORDER BY timestamp DESC;
                        """,
                        (user_id_val,)
                    )
                    last_message_content = recent_conv_cur.fetchone()
                    results.append({
                        "user_id": user_id_val,  # 改名為 user_id
                        "language": language or "zh-Hant",  # 預設語言
                        "last_activity": timestamp_val,  # 直接使用 timestamp
                        "message_count": message_count,
                        "last_message": last_message_content[0] if last_message_content else "",
                    })
                return results
        except pyodbc.Error as e:
            logger.exception(f"取得最近對話失敗: {e}")
            return []

    def set_user_preference(self, user_id, language=None, role=None):
        """設定或更新使用者偏好與角色"""
        try:
            with self._get_connection() as conn:
                user_pref_set_cur = conn.cursor()
                user_pref_set_cur.execute(
                    "SELECT user_id FROM user_preferences WHERE user_id = ?;",
                    (user_id,)
                )
                user_exists = user_pref_set_cur.fetchone()

                if user_exists:
                    # 更新現有使用者
                    update_parts = []
                    params = []
                    if language is not None:
                        update_parts.append("language = ?")
                        params.append(language)
                    if role is not None:
                        update_parts.append("role = ?")
                        params.append(role)

                    # 如果沒有要更新的欄位，至少更新 last_active
                    if not update_parts:
                        user_pref_set_cur.execute(
                            "UPDATE user_preferences SET last_active = GETDATE()"
                            " WHERE user_id = ?;",
                            (user_id,)
                        )
                    else:
                        sql = (
                            "UPDATE user_preferences SET last_active = GETDATE(), "
                            + ", ".join(update_parts)
                            + " WHERE user_id = ?;"
                        )
                        params.append(user_id)
                        user_pref_set_cur.execute(sql, tuple(params))
                else:
                    # 新增使用者
                    user_pref_set_cur.execute(
                        """
                        INSERT INTO user_preferences
                            (user_id, language, role, last_active,
                             is_admin, responsible_area)
                        VALUES (?, ?, ?, GETDATE(), 0, NULL);
                        """,
                        (user_id, language or "zh-Hant", role or "user")
                    )
                conn.commit()
                return True
        except pyodbc.Error as e:
            logger.exception(f"設定使用者偏好失敗: {e}")
            return False
    # 加回 get_user_preference 方法
    def get_user_preference(self, user_id):
        """取得使用者偏好與角色"""
        try:
            with self._get_connection() as conn:
                user_pref_get_cur = conn.cursor()
                user_pref_get_cur.execute(
                    "SELECT language, role, is_admin, responsible_area "
                    "FROM user_preferences WHERE user_id = ?;",
                    (user_id,)
                )
                result = user_pref_get_cur.fetchone()
                if result:
                    return {
                        "language": result[0],
                        "role": result[1],
                        "is_admin": result[2],
                        "responsible_area": result[3]
                    }
                # 如果未找到則創建預設偏好
                logger.info(
                    f"User {user_id} not found in preferences, "
                    "creating with defaults."
                )
                self.set_user_preference(user_id)  # 這會創建預設的 user, zh-Hant
                return {
                    "language": "zh-Hant",
                    "role": "user",
                    "is_admin": False,
                    "responsible_area": None
                }
        except pyodbc.Error as e:
            logger.exception(f"取得使用者偏好失敗: {e}")
            # 發生錯誤時回傳一個安全的預設值
            return {
                "language": "zh-Hant",
                "role": "user",
                "is_admin": False,
                "responsible_area": None
            }


db = Database()
