import logging
import pyodbc

logger = logging.getLogger(__name__)


class Database:
    """
    處理對話記錄、使用者偏好、設備資訊與異常統計等相關資料庫操作的主要類別。
    內含自動建立所有必要表格的功能，並提供高層級資料存取介面。
    """

    def __init__(self, server=None, database=None):
        """
        初始化 Database 物件，設定連線字串並自動建立所有必要的資料表。

        Args:
            server (str, optional): 資料庫伺服器名稱或 IP。預設為 "localhost"。
            database (str, optional): 要連接的資料庫名稱。預設為 "conversations"。

        動作說明:
            - 會根據指定的伺服器與資料庫名稱，建立 SQL Server 的連線字串。
            - 物件初始化時自動執行 self._initialize_db()，檢查並建立所有所需資料表。

        Returns:
            無
        """
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
        """
        建立並回傳一個 SQL Server 資料庫連線物件。

        Returns:
            pyodbc.Connection: 可用於查詢或寫入的 pyodbc 連線物件。

        範例:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM equipment")
        """
        return pyodbc.connect(self.connection_string)

    def _initialize_db(self):
        """
        檢查並自動建立所有系統所需資料表（若尚未存在）。

        說明:
            本方法會檢查並建立如下資料表：
                - conversations: 對話記錄
                - user_preferences: 使用者偏好與角色
                - equipment: 設備資訊
                - abnormal_logs: 異常紀錄
                - alert_history: 警報歷史
                - user_equipment_subscriptions: 使用者設備訂閱
                - operation_stats_monthly/quarterly/yearly: 各時段運作統計
                - fault_stats_monthly/quarterly/yearly: 各時段異常統計

            若資料表已存在則不會重複建立，確保資料結構完整。

        Args:
            無

        Returns:
            無

        Raises:
            Exception: 若資料庫連線或 SQL 操作發生錯誤會拋出例外。

        例外處理:
            若任何建表過程出錯，會自動記錄詳細錯誤與 traceback 至 logger，並再次 raise 例外給外部。

        使用範例:
            db = Database()  # 初始化時自動呼叫本方法
        """
        try:
            with self._get_connection() as conn:
                init_cur = conn.cursor()
                # 建立對話記錄表
                init_cur.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.tables WHERE name = 'conversations'
                    )
                    CREATE TABLE conversations (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        sender_id NVARCHAR(255) NOT NULL,
                        receiver_id NVARCHAR(255) NOT NULL,
                        sender_role NVARCHAR(50) NOT NULL,
                        content NVARCHAR(MAX) NOT NULL,
                        timestamp DATETIME2 DEFAULT GETDATE(),
                        FOREIGN KEY (sender_id) REFERENCES user_preferences(user_id),
                        FOREIGN KEY (receiver_id) REFERENCES user_preferences(user_id)
                    )
                """)
                # 建立使用者偏好表（增加 role 欄位）
                init_cur.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.tables WHERE name = 'user_preferences'
                    )
                    CREATE TABLE user_preferences (
                        user_id NVARCHAR(255) PRIMARY KEY,
                        language NVARCHAR(10) DEFAULT N'zh-Hant',
                        last_active DATETIME2 DEFAULT GETDATE(),
                        is_admin BIT DEFAULT 0,
                        responsible_area NVARCHAR(255),
                        role NVARCHAR(50) DEFAULT N'user'
                    )
                """)
                # 建立設備表
                init_cur.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.tables WHERE name = 'equipment'
                    )
                    CREATE TABLE equipment (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        equipment_id NVARCHAR(255) NOT NULL UNIQUE,
                        name NVARCHAR(255) NOT NULL,
                        type NVARCHAR(255) NOT NULL,
                        location NVARCHAR(255),
                        status NVARCHAR(255) DEFAULT N'normal',
                        last_updated DATETIME2 DEFAULT GETDATE()
                    )
                """)
                # 建立異常紀錄表
                init_cur.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.tables WHERE name = 'abnormal_logs'
                    )
                    CREATE TABLE abnormal_logs (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        event_date DATETIME2 NOT NULL,
                        equipment_id NVARCHAR(255) NOT NULL,
                        deformation_mm FLOAT,
                        rpm INT,
                        event_time TIME,
                        abnormal_type NVARCHAR(255),
                        downtime INT,
                        recovered_time TIME,
                        notes NVARCHAR(MAX),
                        FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                    )
                """)
                # 建立警報記錄表
                init_cur.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.tables WHERE name = 'alert_history'
                    )
                    CREATE TABLE alert_history (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        equipment_id NVARCHAR(255) NOT NULL,
                        alert_type NVARCHAR(255) NOT NULL,
                        severity NVARCHAR(255) NOT NULL,
                        message NVARCHAR(MAX) NOT NULL,
                        is_resolved BIT DEFAULT 0,
                        created_at DATETIME2 DEFAULT GETDATE(),
                        resolved_at DATETIME2,
                        resolved_by NVARCHAR(255),
                        resolution_notes NVARCHAR(MAX),
                        FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                    )
                """)
                # 使用者訂閱設備表
                init_cur.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.tables
                        WHERE name = 'user_equipment_subscriptions'
                    )
                    CREATE TABLE user_equipment_subscriptions (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        user_id NVARCHAR(255) NOT NULL,
                        equipment_id NVARCHAR(255) NOT NULL,
                        notification_level NVARCHAR(255) DEFAULT N'all',
                        subscribed_at DATETIME2 DEFAULT GETDATE(),
                        CONSTRAINT UQ_user_equipment UNIQUE(user_id, equipment_id)
                    )
                """)
                # 運作統計（月）
                init_cur.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.tables WHERE name = 'operation_stats_monthly'
                    )
                    CREATE TABLE operation_stats_monthly (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        equipment_id NVARCHAR(255) NOT NULL,
                        year INT,
                        month INT,
                        total_operation_time INT,
                        total_downtime INT,
                        downtime_rate FLOAT,
                        description NVARCHAR(MAX),
                        FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                    )
                """)
                # 運作統計（季）
                init_cur.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.tables WHERE name = 'operation_stats_quarterly'
                    )
                    CREATE TABLE operation_stats_quarterly (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        equipment_id NVARCHAR(255) NOT NULL,
                        year INT,
                        quarter INT,
                        total_operation_time INT,
                        total_downtime INT,
                        downtime_rate FLOAT,
                        description NVARCHAR(MAX),
                        FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                    )
                """)
                # 運作統計（年）
                init_cur.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.tables WHERE name = 'operation_stats_yearly'
                    )
                    CREATE TABLE operation_stats_yearly (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        equipment_id NVARCHAR(255) NOT NULL,
                        year INT,
                        total_operation_time INT,
                        total_downtime INT,
                        downtime_rate FLOAT,
                        description NVARCHAR(MAX),
                        FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                    )
                """)
                # 各異常統計（月）
                init_cur.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.tables WHERE name = 'fault_stats_monthly'
                    )
                    CREATE TABLE fault_stats_monthly (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        equipment_id NVARCHAR(255) NOT NULL,
                        year INT,
                        month INT,
                        abnormal_type NVARCHAR(255),
                        downtime INT,
                        downtime_rate FLOAT,
                        description NVARCHAR(MAX),
                        FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                    )
                """)
                # 各異常統計（季）
                init_cur.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.tables WHERE name = 'fault_stats_quarterly'
                    )
                    CREATE TABLE fault_stats_quarterly (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        equipment_id NVARCHAR(255) NOT NULL,
                        year INT,
                        quarter INT,
                        abnormal_type NVARCHAR(255),
                        downtime INT,
                        downtime_rate FLOAT,
                        description NVARCHAR(MAX),
                        FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                    )
                """)
                # 各異常統計（年）
                init_cur.execute("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.tables WHERE name = 'fault_stats_yearly'
                    )
                    CREATE TABLE fault_stats_yearly (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        equipment_id NVARCHAR(255) NOT NULL,
                        year INT,
                        abnormal_type NVARCHAR(255),
                        downtime INT,
                        downtime_rate FLOAT,
                        description NVARCHAR(MAX),
                        FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
                    )
                """)
                conn.commit()
                logger.info("資料庫初始化成功，包含所有自訂資料表")
        except Exception as exc:
            logger.exception(f"資料庫初始化失敗：{exc}")
            raise

    def add_message(self, sender_id, receiver_id, sender_role, content):
        """
        新增一筆對話記錄到 conversations 資料表。

        Args:
            sender_id (str): 發送訊息的 user_id（必須已存在於 user_preferences）。
            receiver_id (str): 接收訊息的 user_id（必須已存在於 user_preferences）。
            sender_role (str): 發送者的角色，例如 'user'、'assistant'、'system'。
            content (str): 傳送的訊息內容。

        Returns:
            bool: 新增成功回傳 True，若過程中出現錯誤則回傳 False。

        例外處理:
            若過程中發生任何例外（如資料庫連線失敗、外鍵不存在等），
            會自動記錄於 logger 並回傳 False。
        """
        try:
            with self._get_connection() as conn:
                conv_add_cur = conn.cursor()
                conv_add_cur.execute(
                    """
                    INSERT INTO conversations
                        (sender_id, receiver_id, sender_role, content)
                    VALUES (?, ?, ?, ?)
                    """,
                    (sender_id, receiver_id, sender_role, content)
                )
                conn.commit()
                return True
        except Exception:
            logger.exception("新增對話記錄失敗")
            return False

    def get_conversation_history(self, sender_id, limit=10):
        """
        取得指定發送者（sender_id）的對話紀錄清單，依時間由新到舊排序，回傳字典列表。

        Args:
            sender_id (str): 查詢發送訊息者的 user_id。
            limit (int, optional): 最多回傳的對話訊息數。預設 10。

        Returns:
            list of dict:
                對話紀錄列表，每筆為 dict，格式如：
                [
                    {
                        "sender_role": str,  # 訊息的發送角色（'user', 'assistant', 'system', ...）
                        "content": str       # 訊息內容
                    },
                    ...
                ]
                若查無紀錄或發生錯誤則回傳空列表。
        """
        try:
            with self._get_connection() as conn:
                conv_hist_cur = conn.cursor()
                # 修正後的 SQL 查詢
                sql_query = """
                    SELECT sender_role, content
                    FROM conversations
                    WHERE sender_id = ?
                    ORDER BY timestamp DESC
                    OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
                """
                # 參數順序：第一個 ? 是 sender_id，第二個 ? 是 limit
                conv_hist_cur.execute(sql_query, (sender_id, limit))
                
                messages = [
                    {"sender_role": row.sender_role, "content": row.content} # 假設回傳的 row 物件可以直接透過欄位名稱存取
                    for row in conv_hist_cur.fetchall()
                ]
                messages.reverse()  # 因為 OpenAI 需要的順序是時間由舊到新
                return messages
        except Exception:
            logger.exception("取得對話記錄失敗")
            return []

    def get_conversation_stats(self):
        """
        取得 conversations 對話紀錄的綜合統計資料。

        本方法會計算整體訊息數量、唯一發送者數、最近 24 小時訊息數，
        以及各角色（user、assistant、system、其他）發送的訊息數。

        Args:
            無

        Returns:
            dict: 對話統計資訊，包括以下欄位：
                - total_messages (int): 全部訊息總數
                - unique_senders (int): 發送訊息的唯一 sender_id 數
                - last_24h (int): 最近 24 小時訊息數
                - user_messages (int): user 角色發送訊息數
                - assistant_messages (int): assistant 角色發送訊息數
                - system_messages (int): system 角色發送訊息數
                - other_messages (int): 其他角色發送訊息數

        例外處理:
            若查詢失敗（如資料庫錯誤），會自動記錄於 logger，並回傳所有統計為 0 的預設 dict。

        範例:
            stats = db.get_conversation_stats()
        """
        try:
            with self._get_connection() as conn:
                conv_stats_cur = conn.cursor()
                conv_stats_cur.execute("SELECT COUNT(*) FROM conversations")
                total_messages = conv_stats_cur.fetchone()[0]
                conv_stats_cur.execute(
                    "SELECT COUNT(DISTINCT sender_id) FROM conversations"
                )
                unique_senders = conv_stats_cur.fetchone()[0]
                conv_stats_cur.execute(
                    """
                    SELECT COUNT(*) FROM conversations
                    WHERE timestamp >= DATEADD(day, -1, GETDATE())
                    """
                )
                last_24h = conv_stats_cur.fetchone()[0]
                conv_stats_cur.execute(
                    "SELECT sender_role, COUNT(*) FROM conversations GROUP BY sender_role"
                )
                role_counts = dict(conv_stats_cur.fetchall())
                return {
                    "total_messages": total_messages,
                    "unique_senders": unique_senders,
                    "last_24h": last_24h,
                    "user_messages": role_counts.get("user", 0),
                    "assistant_messages": role_counts.get("assistant", 0),
                    "system_messages": role_counts.get("system", 0),
                    "other_messages": sum(
                        count for role, count in role_counts.items()
                        if role not in ["user", "assistant", "system"]
                    )
                }
        except Exception:
            logger.exception("取得對話統計資料失敗")
            return {
                "total_messages": 0,
                "unique_senders": 0,
                "last_24h": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "system_messages": 0,
                "other_messages": 0,
            }

    def get_recent_conversations(self, limit: int = 5) -> list:
        """
        獲取最近的對話紀錄。
        Args:
            limit (int, optional): 返回的對話數量。預設 5。
        Returns:
            list: 最近對話的列表，每個元素是一個字典。
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT c.sender_id, p.language, MAX(c.timestamp) AS last_message
                    FROM conversations c
                    LEFT JOIN user_preferences p ON c.sender_id = p.user_id
                    GROUP BY c.sender_id, p.language
                    ORDER BY last_message DESC
                    OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
                    """,
                    (limit,)
                )
                results = []
                # 獲取最近對話的核心邏輯不變，只是分頁語法修改
                for sender_id, language, timestamp in cursor.fetchall():
                    # 以下兩個查詢保持不變，因為它們不是分頁查詢的主體
                    cursor.execute(
                        "SELECT COUNT(*) FROM conversations WHERE sender_id = ?",
                        (sender_id,)
                    )
                    message_count = cursor.fetchone()[0]
                    cursor.execute(
                        """
                        SELECT TOP 1 content FROM conversations
                        WHERE sender_id = ? AND sender_role = 'user'
                        ORDER BY timestamp DESC
                        """,
                        (sender_id,)
                    )
                    last_message = cursor.fetchone()
                    results.append({
                        "sender_id": sender_id,
                        "language": language or "zh-Hant",
                        "last_activity": timestamp,
                        "message_count": message_count,
                        "last_message": last_message[0] if last_message else "",
                    })
                return results
        except Exception:
            logger.exception("取得最近對話失敗")
            return []

    def set_user_preference(self, user_id: str, **kwargs) -> bool:
        """
        設定或更新指定使用者的偏好設定。

        Args:
            user_id (str): 使用者的唯一識別碼。
            **kwargs: 偏好設定的鍵值對，例如 language='zh-Hant', responsible_area='生產線A'。
                      支援的鍵包括 'language', 'responsible_area', 'is_admin'。

        Returns:
            bool: 如果設定成功則為 True，否則為 False。

        Raises:
            Exception: 如果資料庫操作失敗。

        範例:
            ```python
            db.set_user_preference("U1234567890abcdef", language="en", responsible_area="A區")
            ```
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 檢查使用者是否存在
                cursor.execute("SELECT 1 FROM user_preferences WHERE user_id = ?", (user_id,))
                exists = cursor.fetchone()

                update_fields = []
                update_values = []
                for key, value in kwargs.items():
                    # 限制可更新的欄位，防止注入不支援的欄位
                    if key in ["language", "responsible_area", "is_admin"]:
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)

                if not update_fields:
                    logger.warning(f"沒有可更新的偏好設定給使用者 {user_id}。")
                    return False

                if exists:
                    # 更新現有偏好
                    query = f"UPDATE user_preferences SET {', '.join(update_fields)} WHERE user_id = ?"
                    update_values.append(user_id)
                    cursor.execute(query, tuple(update_values))
                    logger.info(f"使用者 {user_id} 的偏好設定已更新: {kwargs}")
                else:
                    # 插入新偏好
                    insert_fields = ["user_id"] + list(kwargs.keys())
                    insert_placeholders = ["?"] * len(insert_fields)
                    insert_values = [user_id] + list(kwargs.values())

                    # 過濾掉不支援的欄位，只插入 user_preferences 表中實際存在的欄位
                    # 這裡假設 kwargs 已經被上層限制，或你需要在此處增加檢查
                    valid_insert_fields = []
                    valid_insert_values = []
                    for i, field in enumerate(insert_fields):
                        if field in ["user_id", "language", "responsible_area", "is_admin"]:
                            valid_insert_fields.append(field)
                            valid_insert_values.append(insert_values[i])

                    query = f"INSERT INTO user_preferences ({', '.join(valid_insert_fields)}) VALUES ({', '.join(['?']*len(valid_insert_fields))})"
                    cursor.execute(query, tuple(valid_insert_values))
                    logger.info(f"使用者 {user_id} 的偏好設定已新增: {kwargs}")

                conn.commit()
                return True
        except pyodbc.Error as db_err:
            logger.exception(f"設定使用者偏好 {user_id} 時發生資料庫錯誤: {db_err}")
            return False
        except Exception as e:
            logger.exception(f"設定使用者偏好 {user_id} 時發生未預期錯誤: {e}")
            return False

    def get_user_preference(self, user_id: str) -> dict:
        """
        取得指定使用者的偏好設定。

        Args:
            user_id (str): 使用者的唯一識別碼。

        Returns:
            dict: 包含使用者偏好設定的字典，如果找不到則回傳空字典。

        Raises:
            Exception: 如果資料庫操作失敗。

        範例:
            ```python
            prefs = db.get_user_preference("U1234567890abcdef")
            print(prefs.get("language", "zh-Hant"))
            ```
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT language, responsible_area, is_admin FROM user_preferences WHERE user_id = ?",
                    (user_id,),
                )
                result = cursor.fetchone()
                if result:
                    # 回傳一個字典，包含所有的偏好設定
                    return {
                        "language": result[0],
                        "responsible_area": result[1],
                        "is_admin": bool(result[2]) # 將 int 轉為 bool
                    }
                return {} # 如果找不到使用者，回傳空字典
        except pyodbc.Error as db_err:
            logger.exception(f"取得使用者偏好 {user_id} 時發生資料庫錯誤: {db_err}")
            return {}
        except Exception as e:
            logger.exception(f"取得使用者偏好 {user_id} 時發生未預期錯誤: {e}")
            return {}

    def get_all_equipment(self) -> list:
        """
        從資料庫獲取所有設備的基本資訊。

        Returns:
            list: 包含所有設備資訊字典的列表。
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT equipment_id, equipment_name, equipment_type, location, status FROM equipment")
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception:
            logger.exception("獲取所有設備資訊失敗")
            return []
        
    def get_abnormal_logs(self, equipment_id: str, limit: int = 5) -> list:
        """
        從資料庫獲取指定設備的異常紀錄。
        Args:
            equipment_id (str): 設備的唯一識別碼。
            limit (int, optional): 最多回傳的紀錄數。預設 5。
        Returns:
            list: 包含異常紀錄字典的列表。
                  每個字典包含 'event_date', 'abnormal_type', 'notes'。
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT event_date, abnormal_type, notes
                    FROM abnormal_logs
                    WHERE equipment_id = ?
                    ORDER BY event_date DESC
                    OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
                    """,
                    (equipment_id, limit) # 注意這裡參數的順序
                )
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception:
            logger.exception(f"獲取設備 {equipment_id} 的異常紀錄失敗")
            return []


db = Database()
