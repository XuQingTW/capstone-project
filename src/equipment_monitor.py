# equipment_monitor.py (修改後，符合您的新要求)

import logging
import pandas as pd
from datetime import datetime, timedelta
import pyodbc
from database import db

logger = logging.getLogger(__name__)

# 指向您提供標準的 Excel 檔案
STANDARDS_EXCEL_FILE = r'C:\Users\sunny\Downloads\capstone-project\data\simulated_data (1).xlsx'

class EquipmentMonitor:
    """半導體設備監控與異常偵測器（僅監控切割機並從 Excel 讀取標準）"""

    # 設備類型常數 (已移除黏晶機和打線機)
    DICER = "dicer"  # 切割機

    # 嚴重程度常數
    SEVERITY_WARNING = "warning"
    SEVERITY_CRITICAL = "critical"
    SEVERITY_EMERGENCY = "emergency"

    def __init__(self):
        self.db = db
        # 移除黏晶機和打線機的設定
        self.equipment_type_names = {
            self.DICER: "切割機",
        }
        self.equipment_metrics = {
            self.DICER: ["溫度", "轉速", "冷卻水溫", "切割精度", "良率", "運轉時間"],
        }
        # 新增：在初始化時從 Excel 載入標準
        self.metric_standards = self._load_metric_standards_from_excel()
        if not self.metric_standards:
            logger.error("未能從 Excel 成功載入異常標準，監控功能可能不準確。")

    def _load_metric_standards_from_excel(self):
        """
        從指定的 Excel 檔案 '工作表1' 載入最新的異常判斷標準。
        """
        try:
            logger.info(f"正在從 {STANDARDS_EXCEL_FILE} 的 '工作表1' 載入異常標準...")
            df = pd.read_excel(STANDARDS_EXCEL_FILE, sheet_name="工作表1")
            
            standards = {}
            for _, row in df.iterrows():
                eq_type = row.get('設備類型')
                metric_type = row.get('指標類型')
                if not eq_type or not metric_type:
                    continue
                
                if eq_type not in standards:
                    standards[eq_type] = {}
                
                standards[eq_type][metric_type] = {
                    'min': row.get('閾值下限'),
                    'max': row.get('閾值上限'),
                    'unit': row.get('單位')
                }
            logger.info("成功載入異常標準。")
            return standards
        except FileNotFoundError:
            logger.error(f"找不到標準設定檔：{STANDARDS_EXCEL_FILE}")
            return {}
        except Exception as e:
            logger.exception(f"讀取異常標準 Excel 檔案時發生錯誤: {e}")
            return {}

    def check_all_equipment(self):
        """檢查所有設備是否有異常"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT eq_id, name, eq_type FROM equipment WHERE status <> 'offline';"
                )
                equipments = cursor.fetchall()
                for eq_id, name, eq_type in equipments:
                    # !! 注意：此功能仍需 'equipment_metrics' 資料表來提供即時數值 !!
                    # 一旦該表可用，請取消下面這行的註解以啟用監控
                    # self._check_equipment_metrics(conn, eq_id, name, eq_type)
                    pass
                logger.info("設備檢查完成（指標監控功能需手動啟用）。")
        except pyodbc.Error as db_err:
            logger.exception(f"檢查所有設備時發生資料庫錯誤: {db_err}")
        except Exception as e:
            logger.exception(f"檢查所有設備時發生非預期錯誤: {e}")

    # =========================================================================
    # !! 以下函式 (_check_equipment_metrics) 邏輯已更新 !!
    # 它現在會使用從 Excel 載入的標準，但仍需 'equipment_metrics' 表提供即時數據。
    # =========================================================================
    def _check_equipment_metrics(self, conn, eq_id, name, equipment_type):
        """(待啟用) 檢查設備的指標是否異常（使用從 Excel 讀取的標準）"""
        try:
            cursor = conn.cursor()
            # 這段 SQL 仍然需要 'equipment_metrics' 表來獲取設備回傳的最新數值
            sql_get_metrics = """
                WITH RankedMetrics AS (
                    SELECT
                        metric_type, value, timestamp,
                        ROW_NUMBER() OVER(
                            PARTITION BY equipment_id, metric_type
                            ORDER BY timestamp DESC
                        ) as rn
                    FROM equipment_metrics
                    WHERE equipment_id = ? AND timestamp > DATEADD(minute, -30, GETDATE())
                )
                SELECT metric_type, value, timestamp
                FROM RankedMetrics WHERE rn = 1;
            """
            cursor.execute(sql_get_metrics, (eq_id,))
            
            latest_metrics = cursor.fetchall()
            if not latest_metrics:
                return

            anomalies = []
            for metric_type, value, ts in latest_metrics:
                # 從載入的標準中查找閾值
                standard = self.metric_standards.get(equipment_type, {}).get(metric_type)
                if not standard:
                    continue  # 如果 Excel 中沒有定義此指標的標準，則跳過

                val_float = float(value) if value is not None else None
                min_thresh = float(standard['min']) if pd.notna(standard['min']) else None
                max_thresh = float(standard['max']) if pd.notna(standard['max']) else None

                if val_float is not None:
                    if (min_thresh is not None and val_float < min_thresh) or \
                       (max_thresh is not None and val_float > max_thresh):
                        
                        severity = self._determine_severity(metric_type, val_float, min_thresh, max_thresh)
                        anomalies.append({
                            "metric": metric_type, "value": val_float,
                            "min": min_thresh, "max": max_thresh,
                            "unit": standard.get('unit'), "severity": severity,
                            "timestamp": ts
                        })

            if anomalies:
                highest_severity = max(
                    (a["severity"] for a in anomalies),
                    key=self._severity_level,
                    default=self.SEVERITY_WARNING
                )
                anomaly_messages = []
                for anomaly in anomalies:
                    ts_str = (
                        anomaly['timestamp'].strftime('%H:%M:%S')
                        if anomaly.get('timestamp') else 'N/A'
                    )
                    msg = ""
                    if anomaly["min"] is not None and anomaly["value"] < anomaly["min"]:
                        msg = (
                            f"指標 {anomaly['metric']} 值 {anomaly['value']:.2f} "
                            f"低於下限 {anomaly['min']:.2f} {anomaly['unit'] or ''} "
                            f"(於 {ts_str})"
                        )
                    elif anomaly["max"] is not None and anomaly["value"] > anomaly["max"]:
                        msg = (
                            f"指標 {anomaly['metric']} 值 {anomaly['value']:.2f} "
                            f"超出上限 {anomaly['max']:.2f} {anomaly['unit'] or ''} "
                            f"(於 {ts_str})"
                        )
                    if msg:
                        anomaly_messages.append(msg)

                full_message = (
                    f"設備 {name} ({equipment_id}) 異常提醒 "
                    f"({self._severity_emoji(highest_severity)} {highest_severity.upper()}):\n"
                    + "\n".join(anomaly_messages)
                )

                for anomaly in anomalies:
                    alert_msg_for_db = (
                        f"指標 {anomaly['metric']} 值 {anomaly['value']:.2f} "
                        f"(閾值 {anomaly['min']:.2f}-{anomaly['max']:.2f} "
                        f"{anomaly['unit'] or ''})"
                    )
                    cursor.execute(
                        """
                        INSERT INTO alert_history (equipment_id, alert_type, severity, message)
                        VALUES (?, ?, ?, ?);
                        """,
                        (
                            equipment_id,
                            f"{anomaly['metric']}_alert",
                            anomaly["severity"],
                            alert_msg_for_db
                        )
                    )

                self._update_equipment_status(
                    conn, equipment_id, highest_severity, full_message
                )
                conn.commit()  # 確保在更新狀態後提交
                self._send_alert_notification(equipment_id, full_message, highest_severity)
                logger.info(
                    f"設備 {name} ({equipment_id}) 異常已記錄及通知 ({highest_severity})。"
                )
            else:
                cursor.execute(
                    "SELECT status FROM equipment WHERE equipment_id = ?;", (equipment_id,)
                )
                current_status_row = cursor.fetchone()
                if current_status_row and current_status_row[0] not in ['normal', 'offline']:
                    logger.info(
                        f"設備 {name} ({equipment_id}) 指標已恢復正常，"
                        f"先前狀態為 {current_status_row[0]}。"
                    )
                    self._update_equipment_status(conn, equipment_id, "normal", "指標已恢復正常")
                    conn.commit()

        except pyodbc.Error as db_err:
            logger.error(
                f"檢查設備 {name} ({equipment_id}) 指標時發生資料庫錯誤: {db_err}"
            )
        except Exception as e:
            logger.error(
                f"檢查設備 {name} ({equipment_id}) 指標時發生未知錯誤: {e}"
            )

    def _update_equipment_status(
        self, conn, equipment_id, new_status_key, alert_message_for_log="狀態更新"
    ):
        """輔助函數：更新設備狀態並記錄到 alert_history (如果狀態改變)"""
        status_map = {
            self.SEVERITY_WARNING: "warning",
            self.SEVERITY_CRITICAL: "critical",
            self.SEVERITY_EMERGENCY: "emergency",
            "normal": "normal",
            "offline": "offline",
            "stale_data": "warning"  # 長時間未回報數據也視為一種警告
        }
        db_status = status_map.get(new_status_key, "warning")  # 預設為 warning

        cursor = conn.cursor()
        cursor.execute(
            "SELECT status FROM equipment WHERE equipment_id = ?;", (equipment_id,)
        )
        current_status_row = cursor.fetchone()

        if current_status_row and current_status_row[0] != db_status:
            cursor.execute(
                "UPDATE equipment SET status = ?, last_updated = GETDATE() "
                "WHERE equipment_id = ?;",
                (db_status, equipment_id)
            )
            if new_status_key == "normal" or db_status != current_status_row[0]:
                alert_type = (
                    "status_change" if new_status_key != "normal" else "recovery"
                )
                severity_for_log = (
                    new_status_key if new_status_key != "normal" else "info"
                )  # 'info' for recovery
                is_resolved_log = 1 if new_status_key == "normal" else 0
                cursor.execute(
                    """
                    INSERT INTO alert_history
                        (equipment_id, alert_type, severity, message, is_resolved)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        equipment_id,
                        alert_type,
                        severity_for_log,
                        alert_message_for_log,
                        is_resolved_log
                    )
                )
            logger.info(
                f"設備 {equipment_id} 狀態從 {current_status_row[0]} 更新為 {db_status}。"
            )
            return True  # 狀態已更新
        return False  # 狀態未改變

    def _check_operation_status(self, conn, equipment_id, name, equipment_type):
        """檢查設備運行狀態，包括長時間運行、異常停機等"""
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, operation_type, start_time, lot_id, product_id
                FROM equipment_operation_logs
                WHERE equipment_id = ? AND end_time IS NULL
                ORDER BY start_time ASC;
                """,
                (equipment_id,),
            )
            operations = cursor.fetchall()
            if not operations:
                return

            for op_id, op_type, start_time_db, lot_id, product_id in operations:
                operation_duration = datetime.now() - start_time_db
                max_duration_hours = {
                    self.DIE_BONDER: 6, self.WIRE_BONDER: 8, self.DICER: 4,
                }.get(equipment_type, 8)

                if operation_duration > timedelta(hours=max_duration_hours):
                    severity = self.SEVERITY_WARNING
                    duration_str = str(operation_duration).split('.')[0]
                    message = (
                        f"設備 {name} ({equipment_id}) 的作業 '{op_type}' (ID: {op_id}) "
                        f"已持續運行 {duration_str}，"
                        f"超過預期 {max_duration_hours} 小時，請注意檢查。"
                    )

                    cursor.execute(
                        "SELECT id FROM alert_history "
                        "WHERE equipment_id = ? AND alert_type = ? AND is_resolved = 0 "
                        "AND message LIKE ?;",
                        (equipment_id, "operation_long_running", f"%ID: {op_id}%")
                    )

                    if not cursor.fetchone():  # 如果沒有未解決的相同作業長時間運行警報
                        cursor.execute(
                            """
                            INSERT INTO alert_history
                                (equipment_id, alert_type, severity, message)
                            VALUES (?, ?, ?, ?);
                            """,
                            (equipment_id, "operation_long_running", severity, message),
                        )
                        conn.commit()  # 提交警報記錄
                        self._send_alert_notification(equipment_id, message, severity)
                        logger.info(
                            f"設備 {name} ({equipment_id}) 作業 {op_id} "
                            "長時間運行異常已通知。"
                        )
                    else:
                        logger.debug(
                            f"設備 {name} ({equipment_id}) 作業 {op_id} "
                            "長時間運行警報已存在且未解決，跳過重複通知。"
                        )
                    return  # 通常一個設備同時只會有一個主要運行作業
        except pyodbc.Error as db_err:
            logger.error(
                f"檢查設備 {name} ({equipment_id}) 運行狀態時發生資料庫錯誤: {db_err}"
            )
        except Exception as e:
            logger.error(
                f"檢查設備 {name} ({equipment_id}) 運行狀態時發生未知錯誤: {e}"
            )

    def _determine_severity(self, metric_type, value, threshold_min, threshold_max):
        val = float(value) if value is not None else 0
        min_thresh = float(threshold_min) if threshold_min is not None else float('-inf')
        max_thresh = float(threshold_max) if threshold_max is not None else float('inf')

        # 通常這些值越高越危險，或越低越危險
        if metric_type in ["溫度", "壓力", "轉速", "金絲張力"]:
            if max_thresh != float('inf') and val > max_thresh:  # 超出上限
                if val >= max_thresh * 1.2:
                    return self.SEVERITY_EMERGENCY
                if val >= max_thresh * 1.1:
                    return self.SEVERITY_CRITICAL
                return self.SEVERITY_WARNING
            # 低於下限 (某些指標，如壓力，過低也可能危險)
            if min_thresh != float('-inf') and val < min_thresh:
                return self.SEVERITY_WARNING  # 暫時都設為 WARNING
        # 通常這些值越低越嚴重
        elif metric_type in ["良率", "Pick準確率", "切割精度"]:
            if min_thresh != float('-inf') and val < min_thresh:
                if val <= min_thresh * 0.8:
                    return self.SEVERITY_CRITICAL
                if val <= min_thresh * 0.9:  # 調整分級
                    return self.SEVERITY_WARNING
                return self.SEVERITY_WARNING  # 預設是警告

        return self.SEVERITY_WARNING  # 預設為警告
                # 後續處理（發送通知等）邏輯保持不變...
        pass

    def _severity_level(self, severity):
        levels = {
            self.SEVERITY_WARNING: 1,
            self.SEVERITY_CRITICAL: 2,
            self.SEVERITY_EMERGENCY: 3,
            "info": 0,
            "normal_recovery": 0
        }
        return levels.get(severity, 0)

    def _severity_emoji(self, severity):
        emojis = {
            self.SEVERITY_WARNING: "⚠️",
            self.SEVERITY_CRITICAL: "🔴",
            self.SEVERITY_EMERGENCY: "🚨",
            "info": "ℹ️",
            "normal_recovery": "✅"
        }
        return emojis.get(severity, "⚠️")

    def _get_equipment_data(self, conn_unused, equipment_id):  # conn_unused 標示為未使用
        try:
            with self.db._get_connection() as new_conn:
                cursor = new_conn.cursor()
                cursor.execute(
                    "SELECT name, type, location FROM equipment WHERE equipment_id = ?;",
                    (equipment_id,),
                )
                result = cursor.fetchone()
                if result:
                    return {
                        "name": result[0], "type": result[1],
                        "type_name": self.equipment_type_names.get(result[1], result[1]),
                        "location": result[2]
                    }
        except pyodbc.Error as db_err:
            logger.error(
                f"從 _get_equipment_data 獲取設備 {equipment_id} 資料失敗: {db_err}"
            )
        return {
            "name": "未知", "type": "未知",
            "type_name": "未知設備", "location": "未知"
        }

    def _generate_ai_recommendation(self, anomalies, equipment_data):
        """產生 AI 增強的異常描述和建議（使用現有的 OpenAI 服務）"""
        try:
            from src.main import OpenAIService  # 保持局部導入

            context_parts = []
            for anomaly in anomalies:
                ts_str = (
                    anomaly['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    if anomaly.get('timestamp') else 'N/A'
                )
                min_val_str = f"{anomaly['min']:.2f}" if anomaly['min'] is not None else "N/A"
                max_val_str = f"{anomaly['max']:.2f}" if anomaly['max'] is not None else "N/A"
                value_str = f"{anomaly['value']:.2f}" if anomaly['value'] is not None else "N/A"

                context_parts.append(
                    f"- 指標 '{anomaly['metric']}': 目前值 {value_str} "
                    f"(正常範圍: {min_val_str} - {max_val_str} {anomaly['unit'] or ''}), "
                    f"記錄時間: {ts_str}"
                )
            context = "偵測到的異常狀況:\n" + "\n".join(context_parts)

            prompt = (
                "作為一個半導體設備維護專家，請分析以下設備的異常狀況並提供具體的初步排查建議和可能的解決方案。\n"
                f"設備資料：名稱 {equipment_data.get('name')}, "
                f"型號 {equipment_data.get('type_name')}, "
                f"位置 {equipment_data.get('location')}\n"
                f"異常詳情：\n{context}\n"
                "請以簡潔、條列式的方式提供建議，重點放在操作員或初級維護人員可以執行的檢查步驟。"
            )

            system_ai_user_id = "SYSTEM_AI_HELPER_EQUIPMENT"
            # 確保有此用戶的偏好
            db.set_user_preference(system_ai_user_id, language="zh-Hant")

            service = OpenAIService(message=prompt, user_id=system_ai_user_id)
            response = service.get_response()
            return response
        except ImportError as imp_err:
            logger.error(f"無法導入 OpenAIService: {imp_err}")
            return "無法獲取 AI 建議 (模組導入錯誤)。"
            logger.error(f"檢查設備 {name} ({eq_id}) 指標時發生資料庫錯誤: {db_err}")
        except Exception as e:
            logger.exception(f"產生 AI 建議時發生錯誤: {e}")
            return "無法獲取 AI 建議 (系統錯誤)。"

    def _send_alert_notification(self, equipment_id, message, severity):
        """發送通知給訂閱該設備的使用者及相關負責人"""
        try:
            from src.linebot_connect import send_notification  # 保持局部導入

            user_ids_to_notify = set()

            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                level_filter_tuple = ()
                if severity == self.SEVERITY_EMERGENCY:
                    level_filter_tuple = ('all', 'critical', 'emergency')
                elif severity == self.SEVERITY_CRITICAL:
                    level_filter_tuple = ('all', 'critical')
                elif severity == self.SEVERITY_WARNING:
                    level_filter_tuple = ('all',)
                else:  # info, normal_recovery 等
                    level_filter_tuple = ('all',)  # 或者不發送非警告級別的通知

                if level_filter_tuple:
                    # 動態生成 IN (...) 中的佔位符
                    placeholders = ', '.join(['?'] * len(level_filter_tuple))
                    sql_subscriptions = (
                        f"SELECT user_id FROM user_equipment_subscriptions "
                        f"WHERE equipment_id = ? AND notification_level IN ({placeholders});"
                    )
                    params = [equipment_id] + list(level_filter_tuple)
                    cursor.execute(sql_subscriptions, params)
                    for row in cursor.fetchall():
                        user_ids_to_notify.add(row[0])
            logger.error(f"檢查設備 {name} ({eq_id}) 指標時發生未知錯誤: {e}")

            cursor.execute(
                    "SELECT type FROM equipment WHERE equipment_id = ?;", (equipment_id,)
                )
            equipment_info = cursor.fetchone()
            if equipment_info:
                    equipment_type = equipment_info[0]
                    cursor.execute(
                        "SELECT user_id FROM user_preferences "
                        "WHERE responsible_area = ? OR is_admin = 1;",
                        (equipment_type,)
                    )
                    for row in cursor.fetchall():
                        user_ids_to_notify.add(row[0])

            if not user_ids_to_notify:
                logger.warning(
                    f"設備 {equipment_id} 發生警報，但找不到任何符合條件的通知對象。"
                )
                
            final_message = (
                f"{self._severity_emoji(severity)} "
                f"設備警報 ({equipment_id}):\n{message}"
            )

            for user_id_val in user_ids_to_notify:
                if send_notification(user_id_val, final_message):
                    logger.info(
                        f"警報通知已發送給使用者: {user_id_val} 針對設備 {equipment_id}"
                    )
                else:
                    logger.error(f"發送警報通知給使用者: {user_id_val} 失敗")

        except pyodbc.Error as db_err:
            logger.exception(
                f"發送設備 {equipment_id} 的通知時發生資料庫錯誤: {db_err}"
            )
        except ImportError:  # send_notification 導入失敗
            logger.error("無法導入 send_notification 函數。警報無法發送。")
        except Exception as e:
            logger.exception(
                f"發送設備 {equipment_id} 的通知時發生非預期錯誤: {e}"
            )
    # ... 其他函式 (_update_equipment_status, _send_alert_notification 等) 保持不變，但記得檢查欄位名稱 ...
    # ... _determine_severity, _severity_level 等也保持不變 ...