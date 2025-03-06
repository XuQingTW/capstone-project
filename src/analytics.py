import os
import json
import logging
import sqlite3
import datetime
from collections import defaultdict, Counter
from pathlib import Path

logger = logging.getLogger(__name__)

class Analytics:
    """分析模組，用於追蹤與分析使用者行為與系統使用狀況"""
    
    def __init__(self, db_path="data/conversations.db"):
        """初始化分析模組"""
        self.db_path = db_path
        
        # 確保分析資料目錄存在
        stats_dir = os.path.join(os.path.dirname(db_path), "stats")
        os.makedirs(stats_dir, exist_ok=True)
        self.stats_path = os.path.join(stats_dir, "usage_stats.json")
        
        # 初始化分析表格
        self._initialize_analytics_tables()
    
    def _initialize_analytics_tables(self):
        """初始化分析用的資料表"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 建立事件追蹤表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
                ''')
                
                # 建立每日使用統計表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    total_messages INTEGER DEFAULT 0,
                    unique_users INTEGER DEFAULT 0,
                    avg_response_time REAL DEFAULT 0,
                    data JSON
                )
                ''')
                
                # 建立關鍵字追蹤表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS keyword_stats (
                    keyword TEXT PRIMARY KEY,
                    count INTEGER DEFAULT 0,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                conn.commit()
        except Exception as e:
            logger.error(f"初始化分析表格失敗: {e}")
    
    def _get_db_connection(self):
        """取得資料庫連線"""
        return sqlite3.connect(self.db_path)
    
    def track_event(self, event_type, user_id=None, metadata=None):
        """
        記錄一個事件
        
        參數:
            event_type: 事件類型 (例如: message, powerbi_view, language_change)
            user_id: 使用者 ID
            metadata: 額外資訊，會以 JSON 格式儲存
        """
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO analytics_events (event_type, user_id, metadata) VALUES (?, ?, ?)",
                    (event_type, user_id, metadata_json)
                )
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"記錄事件失敗: {e}")
            return False
    
    def track_keywords(self, text, increment=1):
        """
        追蹤常用關鍵字
        
        參數:
            text: 要分析的文字
            increment: 增加的計數
        """
        # 簡單的關鍵字提取邏輯，實際應用可加入更複雜的 NLP 處理
        # 這裡僅示範將字串以空格分割，篩選長度大於 1 的單詞
        if not text or not isinstance(text, str):
            return False
        
        keywords = [word for word in text.lower().split() if len(word) > 1]
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                for keyword in keywords:
                    # 檢查關鍵字是否存在
                    cursor.execute("SELECT count FROM keyword_stats WHERE keyword = ?", (keyword,))
                    result = cursor.fetchone()
                    
                    if result:
                        # 更新現有關鍵字
                        cursor.execute(
                            "UPDATE keyword_stats SET count = count + ?, last_used = CURRENT_TIMESTAMP WHERE keyword = ?",
                            (increment, keyword)
                        )
                    else:
                        # 新增關鍵字
                        cursor.execute(
                            "INSERT INTO keyword_stats (keyword, count) VALUES (?, ?)",
                            (keyword, increment)
                        )
                
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"追蹤關鍵字失敗: {e}")
            return False
    
    def get_top_keywords(self, limit=20):
        """取得最常使用的關鍵字"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT keyword, count FROM keyword_stats ORDER BY count DESC LIMIT ?",
                    (limit,)
                )
                return [(keyword, count) for keyword, count in cursor.fetchall()]
        except Exception as e:
            logger.error(f"取得關鍵字統計失敗: {e}")
            return []
    
    def generate_daily_stats(self, date=None):
        """
        生成每日統計數據
        
        參數:
            date: 日期字串 (YYYY-MM-DD)，若未提供則使用今天
        """
        if date is None:
            date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 取得當日訊息總數
                cursor.execute("""
                    SELECT COUNT(*) FROM conversations 
                    WHERE date(timestamp) = ?
                """, (date,))
                total_messages = cursor.fetchone()[0]
                
                # 取得當日獨立使用者數
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM conversations 
                    WHERE date(timestamp) = ?
                """, (date,))
                unique_users = cursor.fetchone()[0]
                
                # 取得各類事件統計
                cursor.execute("""
                    SELECT event_type, COUNT(*) FROM analytics_events 
                    WHERE date(timestamp) = ?
                    GROUP BY event_type
                """, (date,))
                event_counts = dict(cursor.fetchall())
                
                # 取得語言偏好分佈
                cursor.execute("""
                    SELECT language, COUNT(*) FROM user_preferences
                    GROUP BY language
                """)
                language_distribution = dict(cursor.fetchall())
                
                # 組織統計數據
                stats_data = {
                    "date": date,
                    "total_messages": total_messages,
                    "unique_users": unique_users,
                    "events": event_counts,
                    "language_distribution": language_distribution
                }
                
                # 將統計數據存入每日統計表
                stats_json = json.dumps(stats_data)
                
                # 檢查是否已有當日統計
                cursor.execute("SELECT date FROM daily_stats WHERE date = ?", (date,))
                if cursor.fetchone():
                    # 更新現有統計
                    cursor.execute("""
                        UPDATE daily_stats 
                        SET total_messages = ?, unique_users = ?, data = ?
                        WHERE date = ?
                    """, (total_messages, unique_users, stats_json, date))
                else:
                    # 插入新統計
                    cursor.execute("""
                        INSERT INTO daily_stats (date, total_messages, unique_users, data)
                        VALUES (?, ?, ?, ?)
                    """, (date, total_messages, unique_users, stats_json))
                
                conn.commit()
                
                return stats_data
                
        except Exception as e:
            logger.error(f"生成每日統計失敗: {e}")
            return None
    
    def get_usage_trends(self, days=30):
        """
        取得使用趨勢數據
        
        參數:
            days: 要回溯的天數
        """
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 取得每日訊息量趨勢
                cursor.execute("""
                    SELECT date(timestamp) as day, COUNT(*) as count 
                    FROM conversations
                    WHERE timestamp BETWEEN ? AND ?
                    GROUP BY day
                    ORDER BY day
                """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
                
                message_trend = {day: count for day, count in cursor.fetchall()}
                
                # 取得每日使用者量趨勢
                cursor.execute("""
                    SELECT date(timestamp) as day, COUNT(DISTINCT user_id) as count 
                    FROM conversations
                    WHERE timestamp BETWEEN ? AND ?
                    GROUP BY day
                    ORDER BY day
                """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
                
                user_trend = {day: count for day, count in cursor.fetchall()}
                
                # 生成完整日期範圍 (包含無數據的日期)
                date_range = []
                current = start_date
                while current <= end_date:
                    date_str = current.strftime('%Y-%m-%d')
                    date_range.append(date_str)
                    current += datetime.timedelta(days=1)
                
                # 組合完整趨勢數據
                trends = {
                    "dates": date_range,
                    "messages": [message_trend.get(date, 0) for date in date_range],
                    "users": [user_trend.get(date, 0) for date in date_range]
                }
                
                return trends
                
        except Exception as e:
            logger.error(f"取得使用趨勢失敗: {e}")
            return None
            
    def export_stats(self, format="json"):
        """
        匯出統計數據
        
        參數:
            format: 輸出格式 (目前僅支援 json)
        """
        if format != "json":
            raise ValueError("目前僅支援 JSON 格式匯出")
        
        try:
            # 取得各種統計數據
            conversation_stats = self._get_conversation_stats()
            user_stats = self._get_user_stats()
            keyword_stats = self.get_top_keywords(50)
            usage_trends = self.get_usage_trends(30)
            
            # 組合匯出數據
            export_data = {
                "generated_at": datetime.datetime.now().isoformat(),
                "conversation_stats": conversation_stats,
                "user_stats": user_stats,
                "top_keywords": dict(keyword_stats),
                "usage_trends": usage_trends
            }
            
            # 寫入 JSON 檔案
            with open(self.stats_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return self.stats_path
            
        except Exception as e:
            logger.error(f"匯出統計數據失敗: {e}")
            return None
    
    def _get_conversation_stats(self):
        """取得對話統計數據"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 總訊息數
                cursor.execute("SELECT COUNT(*) FROM conversations")
                total_messages = cursor.fetchone()[0]
                
                # 各角色訊息數
                cursor.execute("""
                    SELECT role, COUNT(*) 
                    FROM conversations 
                    GROUP BY role
                """)
                role_counts = dict(cursor.fetchall())
                
                # 過去 24 小時訊息數
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM conversations 
                    WHERE timestamp > datetime('now', '-1 day')
                """)
                last_24h = cursor.fetchone()[0]
                
                return {
                    "total_messages": total_messages,
                    "role_distribution": role_counts,
                    "last_24h": last_24h
                }
                
        except Exception as e:
            logger.error(f"取得對話統計失敗: {e}")
            return {}
    
    def _get_user_stats(self):
        """取得使用者統計數據"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 使用者總數
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM conversations")
                total_users = cursor.fetchone()[0]
                
                # 活躍使用者數 (過去 7 天有發送訊息的使用者)
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) 
                    FROM conversations 
                    WHERE timestamp > datetime('now', '-7 day')
                """)
                active_users = cursor.fetchone()[0]
                
                # 語言偏好分佈
                cursor.execute("""
                    SELECT language, COUNT(*) 
                    FROM user_preferences 
                    GROUP BY language
                """)
                language_distribution = dict(cursor.fetchall())
                
                return {
                    "total_users": total_users,
                    "active_users": active_users,
                    "language_distribution": language_distribution
                }
                
        except Exception as e:
            logger.error(f"取得使用者統計失敗: {e}")
            return {}

# 建立分析模組實例
analytics = Analytics()