import logging
import pyodbc

from config import Config  # Assuming config.py exists as per original


logger = logging.getLogger(__name__)


class Database:
    """處理對話記錄與使用者偏好儲存的資料庫處理程序"""

    def __init__(self, server=None, database=None):
        """初始化資料庫連線"""
        # 修改回從 Config 讀取預設值
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
                # 欄位假設: user_id, language, role, is_admin,
                # responsible_area, created_at, display_name, email,
                # last_active
                user_preferences_cols = """
                    [user_id] NVARCHAR(255) NULL,
                    [language] VARCHAR(50) NULL,
                    [role] NVARCHAR(50) NULL,
                    [is_admin] BIT NULL,
                    [responsible_area] NVARCHAR(255) NULL,
                    [created_at] DATETIME2 NULL,
                    [display_name] NVARCHAR(100) NULL,
                    [email] NVARCHAR(255) NULL,
                    [last_active] DATETIME2 NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "user_preferences",
                    user_preferences_cols
                )

                # 2. equipment (來自 equipment.csv)
                # 欄位假設: eq_id, name, eq_type, location, status,
                # created_at, model_number, purchase_date,
                # last_maintenance_date
                equipment_cols = """
                    [eq_id] NVARCHAR(255) NULL,
                    [name] NVARCHAR(255) NULL,
                    [eq_type] NVARCHAR(100) NULL,
                    [location] NVARCHAR(255) NULL,
                    [status] NVARCHAR(100) NULL,
                    [created_at] DATETIME2 NULL,
                    [model_number] NVARCHAR(100) NULL,
                    [purchase_date] DATETIME2 NULL,
                    [last_maintenance_date] DATETIME2 NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "equipment",
                    equipment_cols
                )

                # 3. conversations (來自 conversations.csv)
                # 欄位假設 (請核對您的 CSV): message_id, user_id (或 sender_id),
                # receiver_id, sender_role, content, timestamp,
                # message_type, is_user_message, intent, entities,
                # response_text, response_generated_at, feedback_score, notes
                # 根據您先前的方法簽名，簡化為:
                conversations_cols = """
                    [message_id] NVARCHAR(255) NULL,
                    [sender_id] NVARCHAR(255) NULL,
                    [receiver_id] NVARCHAR(255) NULL,
                    [sender_role] NVARCHAR(50) NULL,
                    [content] NVARCHAR(MAX) NULL,
                    [timestamp] DATETIME2 NULL DEFAULT GETDATE()
                    -- 以下為 conversations.csv 中其他可能的欄位，
                    -- 請根據您的CSV取消註解或修改:
                    -- [user_id] NVARCHAR(255) NULL,
                    -- [message_type] NVARCHAR(50) NULL,
                    -- [is_user_message] BIT NULL,
                    -- [intent] NVARCHAR(100) NULL,
                    -- [entities] NVARCHAR(MAX) NULL,
                    -- [response_text] NVARCHAR(MAX) NULL,
                    -- [response_generated_at] DATETIME2 NULL,
                    -- [feedback_score] INT NULL,
                    -- [notes] NVARCHAR(MAX) NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "conversations",
                    conversations_cols
                )

                # 4. user_equipment_subscriptions
                # (來自 user_equipment_subscriptions.csv)
                # 欄位假設: subscription_id, user_id, eq_id,
                # notification_types, subscribed_at
                user_equipment_subscriptions_cols = """
                    [subscription_id] INT NULL,
                    [user_id] NVARCHAR(255) NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [notification_types] NVARCHAR(255) NULL,
                    [subscribed_at] DATETIME2 NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "user_equipment_subscriptions",
                    user_equipment_subscriptions_cols
                )

                # 5. alert_history (來自 alert_history.csv)
                # 欄位假設: alert_id, eq_id, alert_type_code, timestamp,
                # description, severity, status, resolved_at, notes
                alert_history_cols = """
                    [alert_id] NVARCHAR(255) NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [timestamp] DATETIME2 NULL,
                    [description] NVARCHAR(MAX) NULL,
                    [severity] NVARCHAR(50) NULL,
                    [status] NVARCHAR(50) NULL,
                    [resolved_at] DATETIME2 NULL,
                    [notes] NVARCHAR(MAX) NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "alert_history",
                    alert_history_cols
                )

                # 6. error_logs (來自 異常紀錄.csv)
                # 欄位假設: log_id, eq_id, timestamp, error_code,
                # description, reporter, status, resolved_at,
                # resolution_notes
                error_logs_cols = """
                    [log_id] NVARCHAR(255) NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [timestamp] DATETIME2 NULL,
                    [error_code] NVARCHAR(100) NULL,
                    [description] NVARCHAR(MAX) NULL,
                    [reporter] NVARCHAR(100) NULL,
                    [status] NVARCHAR(50) NULL,
                    [resolved_at] DATETIME2 NULL,
                    [resolution_notes] NVARCHAR(MAX) NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "error_logs",
                    error_logs_cols
                )

                # 7. stats_abnormal_monthly (來自 各異常統計(月).csv)
                # 欄位假設: year, month, eq_id, abnormal_type, count,
                # total_duration_minutes
                stats_abnormal_monthly_cols = """
                    [year] INT NULL,
                    [month] INT NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [abnormal_type] NVARCHAR(255) NULL,
                    [count] INT NULL,
                    [total_duration_minutes] INT NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "stats_abnormal_monthly",
                    stats_abnormal_monthly_cols
                )

                # 8. stats_abnormal_quarterly (來自 各異常統計(季).csv)
                # 欄位假設: year, quarter, eq_id, abnormal_type, count,
                # total_duration_minutes
                stats_abnormal_quarterly_cols = """
                    [year] INT NULL,
                    [quarter] INT NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [abnormal_type] NVARCHAR(255) NULL,
                    [count] INT NULL,
                    [total_duration_minutes] INT NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "stats_abnormal_quarterly",
                    stats_abnormal_quarterly_cols
                )

                # 9. stats_abnormal_yearly (來自 各異常統計(年).csv)
                # 欄位假設: year, eq_id, abnormal_type, count,
                # total_duration_minutes
                stats_abnormal_yearly_cols = """
                    [year] INT NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [abnormal_type] NVARCHAR(255) NULL,
                    [count] INT NULL,
                    [total_duration_minutes] INT NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "stats_abnormal_yearly",
                    stats_abnormal_yearly_cols
                )

                # 10. stats_operational_monthly (來自 運作統計(月).csv)
                # 欄位假設: year, month, eq_id, uptime_hours,
                # downtime_hours, utilization_rate
                stats_operational_monthly_cols = """
                    [year] INT NULL,
                    [month] INT NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [uptime_hours] FLOAT NULL,
                    [downtime_hours] FLOAT NULL,
                    [utilization_rate] FLOAT NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "stats_operational_monthly",
                    stats_operational_monthly_cols
                )

                # 11. stats_operational_quarterly (來自 運作統計(季).csv)
                # 欄位假設: year, quarter, eq_id, uptime_hours,
                # downtime_hours, utilization_rate
                stats_operational_quarterly_cols = """
                    [year] INT NULL,
                    [quarter] INT NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [uptime_hours] FLOAT NULL,
                    [downtime_hours] FLOAT NULL,
                    [utilization_rate] FLOAT NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "stats_operational_quarterly",
                    stats_operational_quarterly_cols
                )

                # 12. stats_operational_yearly (來自 運作統計(年).csv)
                # 欄位假設: year, eq_id, uptime_hours, downtime_hours,
                # utilization_rate
                stats_operational_yearly_cols = """
                    [year] INT NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [uptime_hours] FLOAT NULL,
                    [downtime_hours] FLOAT NULL,
                    [utilization_rate] FLOAT NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "stats_operational_yearly",
                    stats_operational_yearly_cols
                )

                # 13. alert_types (手動定義，因為沒有提供 CSV，但先前討論過共13個表)
                # 欄位假設: alert_type_code, type_name,
                # description_template, default_severity, created_at
                alert_types_cols = """
                    [alert_type_code] NVARCHAR(100) NULL,
                    [type_name] NVARCHAR(255) NULL,
                    [description_template] NVARCHAR(MAX) NULL,
                    [default_severity] NVARCHAR(50) NULL,
                    [created_at] DATETIME2 NULL
                """
                self._create_table_if_not_exists(
                    init_cur,
                    "alert_types",
                    alert_types_cols
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

    def _create_table_if_not_exists(
            self, cursor, table_name, columns_definition):
        """通用方法，用於檢查並建立資料表"""
        check_table_sql = (
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ?;"
        )
        cursor.execute(check_table_sql, (table_name,))
        if cursor.fetchone()[0] == 0:
            create_table_sql = f"CREATE TABLE {table_name} ({columns_definition});"
            cursor.execute(create_table_sql)
            logger.info(f"資料表 '{table_name}' 已建立。")
        else:
            logger.info(f"資料表 '{table_name}' 已存在，跳過建立。")

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
                # 注意：原本您的程式碼這裡的 sender_id 應該是 user_id，
                # 此處保持與原程式碼一致的命名
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
                # 統一鍵名為 'role' 以符合 OpenAI 格式
                messages = [
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
                # 這裡的 sender_id 應該是指 user_id
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
                    "unique_users": unique_senders,  # 改名為 unique_users 更清晰
                    "last_24h": last_24h,
                    "user_messages": role_counts.get("user", 0),
                    "assistant_messages": role_counts.get("assistant", 0),
                    # 如果您有 system role 的訊息
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
                        MAX(c.timestamp) as last_activity_ts
                            -- 改名以區分 last_message 內容
                    FROM conversations c
                    LEFT JOIN user_preferences p
                        ON c.sender_id = p.user_id
                            -- 連接基於 sender_id = user_id
                    GROUP BY c.sender_id, p.language
                    ORDER BY last_activity_ts DESC;
                """
                recent_conv_cur.execute(sql_query, (limit,))
                results = []
                for row in recent_conv_cur.fetchall():
                    user_id_val, language, timestamp_val = row
                    # sender_id 即 user_id
                    recent_conv_cur.execute(
                        "SELECT COUNT(*) FROM conversations WHERE sender_id = ?;",
                        (user_id_val,)
                    )
                    message_count = recent_conv_cur.fetchone()[0]
                    recent_conv_cur.execute(
                        """
                        SELECT TOP 1 content FROM conversations
                        WHERE sender_id = ? AND sender_role = 'user'
                            -- 通常看 user 的最後一句話
                        ORDER BY timestamp DESC;
                        """,
                        (user_id_val,)
                    )
                    last_message_row = recent_conv_cur.fetchone()
                    last_message_content = (
                        last_message_row[0] if last_message_row else ""
                    )
                    results.append({
                        "user_id": user_id_val,  # 改名為 user_id
                        "language": language or "zh-Hant",  # 預設語言
                        "last_activity": timestamp_val,  # 直接使用 timestamp
                        "message_count": message_count,
                        "last_message": last_message_content,
                    })
                return results
        except pyodbc.Error as e:
            logger.exception(f"取得最近對話失敗: {e}")
            return []

    # 加回 set_user_preference 方法
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
                self.set_user_preference(user_id)  # Default: user, zh-Hant
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