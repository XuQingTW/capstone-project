import logging
from datetime import datetime, timedelta
import pyodbc  # Added to resolve F821 and for type hinting if used
from database import db
from linebot_connect import send_notification # 從 linebot_connect 導入 send_notification

logger = logging.getLogger(__name__)


class EquipmentMonitor:
    """半導體設備監控與異常偵測器"""

    # 設備類型常數 (這些仍然適用，用於邏輯判斷)
    DIE_BONDER = "die_bonder"  # 黏晶機
    WIRE_BONDER = "wire_bonder"  # 打線機
    DICER = "dicer"  # 切割機

    # 嚴重程度常數
    SEVERITY_WARNING = "warning"    # 警告
    SEVERITY_CRITICAL = "critical"  # 嚴重
    SEVERITY_EMERGENCY = "emergency"  # 緊急

    def __init__(self):
        self.db = db
        # 設備類型的中文名稱對應
        self.equipment_type_names = {
            self.DIE_BONDER: "黏晶機",
            self.WIRE_BONDER: "打線機",
            self.DICER: "切割機",
        }
        # 設備類型的關鍵指標對應 - 這些現在是模擬的，不再從資料庫讀取具體指標
        # 因為 equipment_metrics 表已移除，這裡可以作為模擬或配置
        self.equipment_simulated_metrics = {
            self.DIE_BONDER: ["溫度", "壓力", "Pick準確率", "良率", "運轉時間"],
            self.WIRE_BONDER: ["溫度", "壓力", "金絲張力", "良率", "運轉時間"],
            self.DICER: ["溫度", "切割速度", "刀具磨損", "良率", "運轉時間"],
        }
        # 預設的閾值（這裡只是範例，實際應用中會從資料庫或配置載入）
        self.thresholds = {
            "溫度": {"warning": 80, "critical": 90},
            "壓力": {"warning": 50, "critical": 60},
            "Pick準確率": {"warning": 0.95, "critical": 0.90},
            "金絲張力": {"warning": 10, "critical": 12},
            "切割速度": {"warning": 500, "critical": 600},
            "刀具磨損": {"warning": 0.8, "critical": 0.9},
            "良率": {"warning": 0.98, "critical": 0.95}, # 良率是越低越糟糕
            "運轉時間": {"warning": 2000, "critical": 3000}, # 運轉時間過長可能需要維護
        }


    def _check_threshold(self, metric_name, value, equipment_id):
        """檢查單一指標是否超過閾值並返回嚴重程度和訊息"""
        # 這裡會根據實際業務邏輯來判斷
        # 假設我們有一些硬編碼的閾值，或者可以從配置中讀取
        # 為了簡化，這裡僅做範例判斷

        if metric_name not in self.thresholds:
            return None, None # 沒有設定閾值的指標不檢查

        threshold_data = self.thresholds[metric_name]
        warning_thresh = threshold_data.get("warning")
        critical_thresh = threshold_data.get("critical")

        # 對於良率，通常是越低越差
        if metric_name == "良率":
            if value < critical_thresh:
                return self.SEVERITY_CRITICAL, f"設備 {equipment_id} 的 {metric_name} 過低 ({value:.2f}% < {critical_thresh:.2f}%)，嚴重影響生產！"
            elif value < warning_thresh:
                return self.SEVERITY_WARNING, f"設備 {equipment_id} 的 {metric_name} 偏低 ({value:.2f}% < {warning_thresh:.2f}%)，請注意。"
        # 對於溫度、壓力、運轉時間、切割速度、刀具磨損等，通常是越高越差
        else:
            if value > critical_thresh:
                return self.SEVERITY_CRITICAL, f"設備 {equipment_id} 的 {metric_name} 達到嚴重閾值 ({value} > {critical_thresh})，可能導致故障！"
            elif value > warning_thresh:
                return self.SEVERITY_WARNING, f"設備 {equipment_id} 的 {metric_name} 達到警告閾值 ({value} > {warning_thresh})，請檢查。"
        return None, None # 未超閾值

    def monitor_equipment(self):
        """
        模擬監控所有設備，檢查其狀態並記錄異常。
        不再從 equipment_metrics 和 equipment_operation_logs 表讀取。
        而是從 `equipment` 表獲取設備列表，並模擬其指標數據。
        """
        logger.info("開始監控所有設備...")
        equipments = self.db.get_all_equipment() # 獲取所有設備的基本資訊
        
        if not equipments:
            logger.info("未找到任何設備可供監控。")
            return

        for equipment in equipments:
            equipment_id = equipment["equipment_id"]
            equipment_type = equipment["type"]
            equipment_name = equipment["name"]
            
            logger.info(f"監控設備: {equipment_name} (ID: {equipment_id}, Type: {equipment_type})")

            # 模擬設備的即時數據
            simulated_data = self._simulate_equipment_data(equipment_type)

            for metric, value in simulated_data.items():
                severity, message = self._check_threshold(metric, value, equipment_id)
                if severity:
                    logger.warning(f"偵測到設備 {equipment_id} 異常: {message} (嚴重性: {severity})")
                    # 記錄異常到 abnormal_logs 表
                    self.db.add_abnormal_log(
                        equipment_id=equipment_id,
                        abnormal_type=f"{metric} {severity}", # 異常類型可以更具體
                        severity=severity,
                        notes=message
                    )
                    # 發送通知 (這裡假設 send_notification 在 Line Bot 方面已被定義)
                    self._send_equipment_notification(equipment_id, message, severity)
                else:
                    logger.info(f"設備 {equipment_id} - {metric}: {value} - 正常。")

            # 模擬設備運行狀態更新 (例如，假設每次監控都表示運行中)
            self.db.update_equipment_status(equipment_id, "運行中") # 或根據模擬數據判斷

        logger.info("設備監控完成。")

    def _simulate_equipment_data(self, equipment_type: str) -> dict:
        """根據設備類型模擬其指標數據"""
        # 這裡只是範例模擬數據，實際應用中會從感測器或 SCADA 系統獲取
        data = {}
        if equipment_type == self.DIE_BONDER:
            data = {
                "溫度": 75 + (datetime.now().second % 20), # 75-94
                "壓力": 45 + (datetime.now().second % 15), # 45-59
                "Pick準確率": 0.99 - (datetime.now().second % 5) / 1000, # 0.99-0.985
                "良率": 0.99 - (datetime.now().second % 10) / 100, # 0.99-0.89
                "運轉時間": 1500 + (datetime.now().minute * 10),
            }
        elif equipment_type == self.WIRE_BONDER:
            data = {
                "溫度": 70 + (datetime.now().second % 25), # 70-94
                "壓力": 40 + (datetime.now().second % 20), # 40-59
                "金絲張力": 8 + (datetime.now().second % 5), # 8-12
                "良率": 0.98 - (datetime.now().second % 10) / 100, # 0.98-0.88
                "運轉時間": 1800 + (datetime.now().minute * 15),
            }
        elif equipment_type == self.DICER:
            data = {
                "溫度": 60 + (datetime.now().second % 30), # 60-89
                "切割速度": 450 + (datetime.now().second % 20), # 450-469
                "刀具磨損": 0.5 + (datetime.now().second % 5) / 10, # 0.5-0.9
                "良率": 0.97 - (datetime.now().second % 10) / 100, # 0.97-0.87
                "運轉時間": 1200 + (datetime.now().minute * 5),
            }
        return data


    def _send_equipment_notification(self, equipment_id: str, message: str, severity: str):
       """
        發送設備異常通知給相關負責人。
       """
    # 從 user_preferences 表中查找負責該設備類型或為管理員的使用者
    try:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()

            users = []

            # 獲取設備類型
            cursor.execute(
                "SELECT type FROM equipment WHERE equipment_id = ?",
                (equipment_id,)
            )
            equipment_type_result = cursor.fetchone()

            if equipment_type_result:
                equipment_type = equipment_type_result[0] # 正確地取值
                # 查找負責該設備類型或為管理員的用戶
                cursor.execute(
                    """
                    SELECT user_id FROM user_preferences
                    WHERE responsible_area = ? OR is_admin = 1
                    """,
                    (equipment_type,) # <<<<<<< CHANGE THIS FROM equipment_type_result[0] to equipment_type
                )
                users.extend(cursor.fetchall())

            unique_users = set(user_id for (user_id,) in users)

            # 如果沒有找到特定的負責人，則發送給所有管理員
            if not unique_users:
                cursor.execute(
                    """
                    SELECT user_id FROM user_preferences
                    WHERE is_admin = 1
                    """
                )
                admin_users = cursor.fetchall()
                unique_users = set(user_id for (user_id,) in admin_users)

            final_message = f"[設備異常通知] 設備ID: {equipment_id} ({self.equipment_type_names.get(equipment_type, '未知類型')})\n" \
                            f"嚴重性: {severity.upper()}\n" \
                            f"內容: {message}\n" \
                            f"請立即處理！"

            for user_id in unique_users:
                send_notification(user_id, final_message) # 呼叫 linebot_connect 中的 send_notification
                logger.info(f"通知已發送給使用者: {user_id} (設備 {equipment_id})")

    except pyodbc.Error as db_err:
        logger.exception(f"發送設備 {equipment_id} 的通知時發生資料庫錯誤: {db_err}")
    except Exception as e:
        logger.exception(f"發送設備 {equipment_id} 的通知時發生非預期錯誤: {e}")