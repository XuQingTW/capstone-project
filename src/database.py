# database.py
import logging
import pyodbc
from config import Config  # 確保 Config 被正確匯入

logger = logging.getLogger(__name__)


class Database:
    """處理資料庫互動的程序，包括表格初始化、資料讀寫等"""

    def __init__(self, server=None, database=None):
        """初始化資料庫連線"""
        resolved_server = server if server is not None else Config.DB_SERVER
        resolved_database = database if database is not None else Config.DB_NAME
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={resolved_server};"
            f"DATABASE={resolved_database};"
            f"Trusted_Connection=yes;"
        )
        self._initialize_db() # 初始化時即檢查/建立表格結構

    def _get_connection(self):
        """建立並回傳資料庫連線"""
        return pyodbc.connect(self.connection_string)

    def _create_table_if_not_exists(self, cursor, table_name, columns_sql):
        """通用函數，用於建立表格（如果不存在）。表格不含主鍵或外鍵。"""
        # 移除欄位定義中可能存在的主鍵或外鍵字樣 (雖然此版本已手動移除)
        # columns_sql = columns_sql.replace("PRIMARY KEY", "").replace("FOREIGN KEY", "") # 雙重保險

        create_sql = f"""
            IF NOT EXISTS (
                SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[{table_name}]') AND type in (N'U')
            )
            BEGIN
                CREATE TABLE [dbo].[{table_name}] (
                    {columns_sql}
                );
            END
        """
        try:
            cursor.execute(create_sql)
            logger.info(f"表格 '{table_name}' 檢查/建立完畢 (無主鍵/外鍵)。")
        except pyodbc.Error as e:
            logger.error(f"建立表格 '{table_name}' 時發生錯誤: {e}")
            logger.error(f"執行的 SQL (部分): CREATE TABLE [dbo].[{table_name}] ( {columns_sql[:200]}... )") # 只顯示部分SQL以防過長
            raise

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
                # 欄位假設: user_id, language, role, is_admin, responsible_area, created_at, display_name, email, last_active
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
                self._create_table_if_not_exists(init_cur, "user_preferences", user_preferences_cols)

                # 2. equipment (來自 equipment.csv)
                # 欄位假設: eq_id, name, eq_type, location, status, created_at, model_number, purchase_date, last_maintenance_date
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
                self._create_table_if_not_exists(init_cur, "equipment", equipment_cols)

                # 3. conversations (來自 conversations.csv)
                # 欄位假設 (請核對您的 CSV): message_id, user_id (或 sender_id), receiver_id, sender_role, content, timestamp, 
                # message_type, is_user_message, intent, entities, response_text, response_generated_at, feedback_score, notes
                # 根據您先前的方法簽名，簡化為:
                conversations_cols = """
                    [message_id] NVARCHAR(255) NULL, 
                    [sender_id] NVARCHAR(255) NULL,       -- 對應您 add_message 中的 sender_id
                    [receiver_id] NVARCHAR(255) NULL,     -- 對應您 add_message 中的 receiver_id
                    [sender_role] NVARCHAR(50) NULL,      -- 對應您 add_message 中的 sender_role
                    [content] NVARCHAR(MAX) NULL,         -- 對應您 add_message 中的 content
                    [timestamp] DATETIME2 NULL DEFAULT GETDATE() -- 自動時間戳
                    -- 以下為 conversations.csv 中其他可能的欄位，請根據您的CSV取消註解或修改:
                    -- [user_id] NVARCHAR(255) NULL,          -- 如果您的 CSV 有 user_id 而非 sender_id
                    -- [message_type] NVARCHAR(50) NULL,
                    -- [is_user_message] BIT NULL,
                    -- [intent] NVARCHAR(100) NULL,
                    -- [entities] NVARCHAR(MAX) NULL,
                    -- [response_text] NVARCHAR(MAX) NULL,
                    -- [response_generated_at] DATETIME2 NULL,
                    -- [feedback_score] INT NULL,
                    -- [notes] NVARCHAR(MAX) NULL
                """
                self._create_table_if_not_exists(init_cur, "conversations", conversations_cols)


                # 4. user_equipment_subscriptions (來自 user_equipment_subscriptions.csv)
                # 欄位假設: subscription_id, user_id, eq_id, notification_types, subscribed_at
                user_equipment_subscriptions_cols = """
                    [subscription_id] INT NULL,
                    [user_id] NVARCHAR(255) NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [notification_types] NVARCHAR(255) NULL,
                    [subscribed_at] DATETIME2 NULL
                """
                self._create_table_if_not_exists(init_cur, "user_equipment_subscriptions", user_equipment_subscriptions_cols)

                # 5. alert_history (來自 alert_history.csv)
                # 欄位假設: alert_id, eq_id, alert_type_code, timestamp, description, severity, status, resolved_at, notes
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
                self._create_table_if_not_exists(init_cur, "alert_history", alert_history_cols)
                
                # 6. error_logs (來自 異常紀錄.csv)
                # 欄位假設: log_id, eq_id, timestamp, error_code, description, reporter, status, resolved_at, resolution_notes
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
                self._create_table_if_not_exists(init_cur, "error_logs", error_logs_cols)

                # 7. stats_abnormal_monthly (來自 各異常統計(月).csv)
                # 欄位假設: year, month, eq_id, abnormal_type, count, total_duration_minutes
                stats_abnormal_monthly_cols = """
                    [year] INT NULL,
                    [month] INT NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [abnormal_type] NVARCHAR(255) NULL,
                    [count] INT NULL,
                    [total_duration_minutes] INT NULL
                """
                self._create_table_if_not_exists(init_cur, "stats_abnormal_monthly", stats_abnormal_monthly_cols)

                # 8. stats_abnormal_quarterly (來自 各異常統計(季).csv)
                # 欄位假設: year, quarter, eq_id, abnormal_type, count, total_duration_minutes
                stats_abnormal_quarterly_cols = """
                    [year] INT NULL,
                    [quarter] INT NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [abnormal_type] NVARCHAR(255) NULL,
                    [count] INT NULL,
                    [total_duration_minutes] INT NULL
                """
                self._create_table_if_not_exists(init_cur, "stats_abnormal_quarterly", stats_abnormal_quarterly_cols)

                # 9. stats_abnormal_yearly (來自 各異常統計(年).csv)
                # 欄位假設: year, eq_id, abnormal_type, count, total_duration_minutes
                stats_abnormal_yearly_cols = """
                    [year] INT NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [abnormal_type] NVARCHAR(255) NULL,
                    [count] INT NULL,
                    [total_duration_minutes] INT NULL
                """
                self._create_table_if_not_exists(init_cur, "stats_abnormal_yearly", stats_abnormal_yearly_cols)

                # 10. stats_operational_monthly (來自 運作統計(月).csv)
                # 欄位假設: year, month, eq_id, uptime_hours, downtime_hours, utilization_rate
                stats_operational_monthly_cols = """
                    [year] INT NULL,
                    [month] INT NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [uptime_hours] FLOAT NULL,
                    [downtime_hours] FLOAT NULL,
                    [utilization_rate] FLOAT NULL
                """
                self._create_table_if_not_exists(init_cur, "stats_operational_monthly", stats_operational_monthly_cols)

                # 11. stats_operational_quarterly (來自 運作統計(季).csv)
                # 欄位假設: year, quarter, eq_id, uptime_hours, downtime_hours, utilization_rate
                stats_operational_quarterly_cols = """
                    [year] INT NULL,
                    [quarter] INT NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [uptime_hours] FLOAT NULL,
                    [downtime_hours] FLOAT NULL,
                    [utilization_rate] FLOAT NULL
                """
                self._create_table_if_not_exists(init_cur, "stats_operational_quarterly", stats_operational_quarterly_cols)

                # 12. stats_operational_yearly (來自 運作統計(年).csv)
                # 欄位假設: year, eq_id, uptime_hours, downtime_hours, utilization_rate
                stats_operational_yearly_cols = """
                    [year] INT NULL,
                    [eq_id] NVARCHAR(255) NULL,
                    [uptime_hours] FLOAT NULL,
                    [downtime_hours] FLOAT NULL,
                    [utilization_rate] FLOAT NULL
                """
                self._create_table_if_not_exists(init_cur, "stats_operational_yearly", stats_operational_yearly_cols)

                # 13. alert_types (手動定義，因為沒有提供 CSV，但先前討論過共13個表)
                # 欄位假設: alert_type_code, type_name, description_template, default_severity, created_at
                alert_types_cols = """
                    [alert_type_code] NVARCHAR(100) NULL,
                    [type_name] NVARCHAR(255) NULL,
                    [description_template] NVARCHAR(MAX) NULL,
                    [default_severity] NVARCHAR(50) NULL,
                    [created_at] DATETIME2 NULL
                """
                self._create_table_if_not_exists(init_cur, "alert_types", alert_types_cols)

                conn.commit()
            logger.info("資料庫表格初始化/檢查完成 (所有表格已移除主鍵/外鍵約束)。")
            logger.warning("請務必檢查每個表格的欄位定義是否完全符合您 CSV 檔案的實際欄位和預期資料類型。")
        except pyodbc.Error as e:
            logger.exception(f"資料庫初始化期間發生 pyodbc 錯誤: {e}")
            raise
        except Exception as ex:
            logger.exception(f"資料庫初始化期間發生非預期錯誤: {ex}")
            raise

    # --- 以下是您先前提供的其他方法，我將它們保留並做微小調整以匹配推斷的欄位 ---

    def add_message(self, sender_id, receiver_id, sender_role, content):
        """加入一筆新的對話記錄（包含發送者角色）"""
        # 假設 conversations 表有 sender_id, receiver_id, sender_role, content, timestamp 欄位
        sql = """
            INSERT INTO conversations 
                (sender_id, receiver_id, sender_role, content, timestamp)
            VALUES (?, ?, ?, ?, GETDATE()); 
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, sender_id, receiver_id, sender_role, content)
                conn.commit()
                return True
        except pyodbc.Error as e:
            logger.exception(f"新增對話記錄失敗: {e}")
            return False

    def get_conversation_history(self, sender_id_param, limit=10): # 參數名改為 sender_id_param 以避免與欄位名混淆
        """取得指定 sender 的對話記錄"""
        # 假設 conversations 表有 sender_id, sender_role, content, timestamp 欄位
        sql = """
            SELECT TOP (?) sender_role, content
            FROM conversations
            WHERE sender_id = ? 
            ORDER BY timestamp DESC;
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, limit, sender_id_param)
                messages = [
                    {"role": role, "content": content_text} # content_text 避免與外層 content 參數混淆
                    for role, content_text in cursor.fetchall()
                ]
                messages.reverse() 
                return messages
        except pyodbc.Error as e:
            logger.exception(f"取得對話記錄失敗 for sender {sender_id_param}: {e}")
            return []

    def get_conversation_stats(self):
        """取得對話記錄統計資料"""
        # 假設 conversations 表有 sender_id, sender_role, timestamp 欄位
        stats = {
            "total_messages": 0, "unique_users": 0, "last_24h": 0,
            "user_messages": 0, "assistant_messages": 0, "system_messages": 0, "other_messages": 0,
        }
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM conversations;")
                result = cursor.fetchone()
                if result: stats["total_messages"] = result[0]

                cursor.execute("SELECT COUNT(DISTINCT sender_id) FROM conversations;")
                result = cursor.fetchone()
                if result: stats["unique_users"] = result[0]
                
                cursor.execute("SELECT COUNT(*) FROM conversations WHERE timestamp >= DATEADD(day, -1, GETDATE());")
                result = cursor.fetchone()
                if result: stats["last_24h"] = result[0]

                cursor.execute("SELECT sender_role, COUNT(*) FROM conversations GROUP BY sender_role;")
                role_counts_db = dict(cursor.fetchall())
                stats["user_messages"] = role_counts_db.get("user", 0)
                stats["assistant_messages"] = role_counts_db.get("assistant", 0)
                stats["system_messages"] = role_counts_db.get("system", 0)
                stats["other_messages"] = sum(
                    count for role, count in role_counts_db.items()
                    if role not in ["user", "assistant", "system"]
                )
            return stats
        except pyodbc.Error as e:
            logger.exception(f"取得對話統計資料失敗: {e}")
            return stats # 返回預設值

    def get_recent_conversations(self, limit=20):
        """取得最近的對話列表（依 sender_id，通常是 user_id）"""
        # 假設 conversations 表有 sender_id, timestamp, content, sender_role
        # 假設 user_preferences 表有 user_id, language
        sql_query = """
            WITH RankedMessages AS (
                SELECT
                    c.sender_id,
                    p.language,
                    c.timestamp AS last_activity_ts,
                    c.content AS last_message_content,
                    ROW_NUMBER() OVER(PARTITION BY c.sender_id ORDER BY c.timestamp DESC) as rn
                FROM conversations c
                LEFT JOIN user_preferences p ON c.sender_id = p.user_id
            )
            SELECT TOP (?)
                rm.sender_id,
                rm.language,
                rm.last_activity_ts,
                (SELECT COUNT(*) FROM conversations sub_c WHERE sub_c.sender_id = rm.sender_id) as message_count,
                rm.last_message_content
            FROM RankedMessages rm
            WHERE rm.rn = 1
            ORDER BY rm.last_activity_ts DESC;
        """
        results = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query, (limit,))
                for row in cursor.fetchall():
                    results.append({
                        "user_id": row.sender_id,
                        "language": row.language or "zh-Hant",
                        "last_activity": row.last_activity_ts,
                        "message_count": row.message_count,
                        "last_message": row.last_message_content or "",
                    })
            return results
        except pyodbc.Error as e:
            logger.exception(f"取得最近對話失敗: {e}")
            return []

    def set_user_preference(self, user_id, language=None, role=None, is_admin=None, responsible_area=None, display_name=None, email=None):
        """設定或更新使用者偏好。is_admin 應為 True/False。"""
        # 假設 user_preferences 表有 user_id, language, role, is_admin, responsible_area, display_name, email, last_active, created_at
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM user_preferences WHERE user_id = ?;", (user_id,))
                user_exists = cursor.fetchone()

                db_is_admin = 1 if is_admin is True else 0 if is_admin is False else None # 轉換布林到 BIT 或保留 NULL

                if user_exists:
                    update_fields = []
                    params = []
                    if language is not None: update_fields.append("language = ?"); params.append(language)
                    if role is not None: update_fields.append("role = ?"); params.append(role)
                    if db_is_admin is not None: update_fields.append("is_admin = ?"); params.append(db_is_admin)
                    if responsible_area is not None: update_fields.append("responsible_area = ?"); params.append(responsible_area)
                    if display_name is not None: update_fields.append("display_name = ?"); params.append(display_name)
                    if email is not None: update_fields.append("email = ?"); params.append(email)
                    
                    if not update_fields: # 至少更新 last_active
                        cursor.execute("UPDATE user_preferences SET last_active = GETDATE() WHERE user_id = ?;", (user_id,))
                    else:
                        update_fields.append("last_active = GETDATE()") # 確保 last_active 被更新
                        sql = f"UPDATE user_preferences SET {', '.join(update_fields)} WHERE user_id = ?;"
                        params.append(user_id)
                        cursor.execute(sql, tuple(params))
                else:
                    # 新增使用者，created_at 和 last_active 都設為當前時間
                    sql = """
                        INSERT INTO user_preferences 
                            (user_id, language, role, is_admin, responsible_area, display_name, email, created_at, last_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE());
                    """
                    cursor.execute(sql,
                        user_id,
                        language or 'zh-Hant',
                        role or 'user',
                        db_is_admin if db_is_admin is not None else 0, # 預設非管理員
                        responsible_area,
                        display_name,
                        email
                    )
                conn.commit()
                logger.info(f"User {user_id} preferences {'updated' if user_exists else 'created'}.")
                return True
        except pyodbc.Error as e:
            logger.exception(f"設定使用者偏好失敗 for user {user_id}: {e}")
            return False

    def get_user_preference(self, user_id):
        """取得使用者偏好與角色"""
        # 假設 user_preferences 表有 user_id, language, role, is_admin, responsible_area, display_name, email
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT language, role, is_admin, responsible_area, display_name, email "
                    "FROM user_preferences WHERE user_id = ?;",
                    (user_id,)
                )
                result = cursor.fetchone()
                if result:
                    return {
                        "language": result.language,
                        "role": result.role,
                        "is_admin": bool(result.is_admin) if result.is_admin is not None else None,
                        "responsible_area": result.responsible_area,
                        "display_name": result.display_name,
                        "email": result.email
                    }
                # 如果未找到，可以選擇是否自動創建預設值
                # logger.info(f"User {user_id} not found in preferences. Creating with defaults via set_user_preference.")
                # self.set_user_preference(user_id) # 第一次調用 set_user_preference 會創建預設值
                # return self.get_user_preference(user_id) # 再次獲取（可能導致遞迴，需小心）
                # 或者直接返回預設字典
                return {
                     "language": "zh-Hant", "role": "user", "is_admin": False,
                     "responsible_area": None, "display_name": None, "email": None
                }

        except pyodbc.Error as e:
            logger.exception(f"取得使用者偏好失敗 for user {user_id}: {e}")
            return { # 發生錯誤時回傳一個安全的預設值
                 "language": "zh-Hant", "role": "user", "is_admin": False,
                 "responsible_area": None, "display_name": None, "email": None
            }


# 在檔案末尾，當 database.py 被直接執行時，可以選擇是否要初始化 db 實例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("正在直接執行 database.py (用於測試或獨立初始化)...")
    
    if not Config.DB_SERVER or not Config.DB_NAME:
        logger.error("錯誤：環境變數 DB_SERVER 或 DB_NAME 未設定。請檢查 config.py 或 .env 檔案。")
    else:
        logger.info(f"嘗試連接到伺服器: {Config.DB_SERVER}, 資料庫: {Config.DB_NAME}")
        try:
            # 建立 Database 實例時，就會執行 _initialize_db()
            db_instance = Database() 
            logger.info("Database 實例已建立，資料表結構應已檢查/初始化 (無主鍵/外鍵)。")
            
            # 您可以在此加入一些簡單的測試，例如連接和查詢一個表格
            # with db_instance._get_connection() as conn_test:
            #    logger.info("測試連接成功。")
            #    test_cursor = conn_test.cursor()
            #    # 確保查詢的表格名稱與 _initialize_db 中定義的一致
            #    test_cursor.execute("SELECT COUNT(*) FROM equipment;") 
            #    count = test_cursor.fetchone()[0]
            #    logger.info(f"Equipment 表中有 {count} 筆資料。")

        except pyodbc.Error as e:
            logger.error(f"建立 Database 實例或連接測試時發生 pyodbc 錯誤: {e.args}")
            logger.error("請檢查：1. SQL Server 是否運行。2. 連接字串。3. ODBC 驅動。4. 網路/防火牆。")
        except Exception as e_main:
            logger.error(f"執行 database.py 時發生未預期錯誤: {e_main}")