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
                # 後續處理（發送通知等）邏輯保持不變...
                pass

        except pyodbc.Error as db_err:
            logger.error(f"檢查設備 {name} ({eq_id}) 指標時發生資料庫錯誤: {db_err}")
        except Exception as e:
            logger.error(f"檢查設備 {name} ({eq_id}) 指標時發生未知錯誤: {e}")

    # ... 其他函式 (_update_equipment_status, _send_alert_notification 等) 保持不變，但記得檢查欄位名稱 ...
    # ... _determine_severity, _severity_level 等也保持不變 ...