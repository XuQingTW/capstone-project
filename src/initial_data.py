import re
import logging
import pandas as pd
import pyodbc
from database import db


# --- 1. 設定日誌記錄 ---
# 設定日誌系統的基本配置，方便追蹤腳本執行狀況與排查問題。
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# --- 2. 設定 Excel 檔案路徑 ---
# 定義包含所有來源數據的 Excel 檔案路徑。
EXCEL_FILE_PATH = r'data\simulated_data (1).xlsx'


# --- 3. 輔助函數 ---

def parse_threshold_string(threshold_str):
    """
    解析標準值定義字串，例如 ' > 10', '< 5', '10-20'。

    此函數使用正則表達式，彈性地將人類可讀的規則轉換為機器可處理的格式。

    Args:
        threshold_str (str): 來自 Excel 的標準值定義字串。

    Returns:
        tuple: (min_val, max_val, operator)，分別代表最小值、最大值和比較符。
    """
    if pd.isna(threshold_str) or threshold_str is None:
        return None, None, None
    s = str(threshold_str).strip()
    match = re.match(r'([><=~]?)\s*([0-9.]+)\s*([~-]\s*([0-9.]+))?', s)
    if not match:
        return None, None, None
    op, val1, _, val2 = match.groups()
    try:
        val1 = float(val1) if val1 else None
        val2 = float(val2) if val2 else None
    except ValueError:
        return None, None, None

    if op == '>':
        return val1, None, '>'
    elif op == '<':
        return None, val1, '<'
    elif op == '~' or _ == '-':
        return val1, val2, None
    else:
        return val1, val1, None


def parse_and_transform_threshold_row(row):
    """
    針對「切割機標準值」工作表的特製轉換函數。

    它使用 parse_threshold_string 來處理一行中定義了多個標準值的欄位，
    並將結果組合成一個符合資料庫欄位順序的元組 (tuple)。
    """
    metric_type = row.get("異常類型")
    # --- 關鍵修正：不再讀取 "正常值" 欄位 ---
    # normal_value, _, _ = parse_threshold_string(row.get("正常值"))
    warning_min, warning_max, _ = parse_threshold_string(row.get("輕度異常"))
    critical_min, critical_max, _ = parse_threshold_string(row.get("中度異常"))
    emergency_min, emergency_max, emergency_op = parse_threshold_string(
        row.get("重度異常")
    )
    # --- 關鍵修正：從返回的元組中移除 normal_value ---
    return (metric_type, warning_min, warning_max,
            critical_min, critical_max, emergency_min, emergency_max,
            emergency_op)


# --- 4. 完整的表格匯入設定 ---
"""
這是此腳本的設定驅動核心。
將每個「Excel工作表 -> 資料庫表格」的對應關係及轉換邏輯都定義為一個字典。
這種設計使得新增或修改匯入任務變得非常簡單，只需在此列表中增減或修改字典，
無需更動主程式邏輯，大大提高了程式碼的可維護性與擴展性。
"""
TABLE_CONFIGS = [
    {
        "excel_sheet_name": "equipment",
        "sql_table_name": "equipment",
        "sql_columns": ["equipment_id", "name", "equipment_type", "location", "status", "last_updated"],
        "transform_row_data": lambda row: (
            row.get('equipment_id'),
            row.get('name'),
            row.get('equipment_type'),
            row.get('location'),
            row.get('status'),
            pd.to_datetime(row.get('last_updated')) if pd.notna(row.get('last_updated')) else None
        )
    },
    {
        "excel_sheet_name": "alert_history",
        "sql_table_name": "alert_history",
        "sql_columns": ["error_id", "equipment_id", "alert_type", "severity", "message",
                        "is_resolved", "created_at", "resolved_at",
                        "resolved_by", "resolution_notes"],
        "transform_row_data": lambda row: (
            row.get('error_id'),
            row.get('equipment_id'),
            row.get('alert_type'),
            row.get('severity'),
            str(row.get('訊息')) if pd.notna(row.get('訊息')) else None,
            row.get('is_resolved'),
            pd.to_datetime(row.get('created_at')) if pd.notna(row.get('created_at')) else None,
            pd.to_datetime(row.get('resolved_at')) if pd.notna(row.get('resolved_at')) else None,
            str(row.get('resolved_by')) if pd.notna(row.get('resolved_by')) else None,
            str(row.get('resolution_notes')) if pd.notna(row.get('resolution_notes')) else None
        )
    },
    {
        "excel_sheet_name": "equipment_metrics",
        "sql_table_name": "equipment_metrics",
        "sql_columns": ["id", "equipment_id", "metric_type", "status",
                        "value", "threshold_min", "threshold_max", "unit", "timestamp"],
        "transform_row_data": lambda row: (
            row.get('id'),
            row.get('equipment_id'),
            row.get('metric_type'),
            str(row.get('狀態')) if pd.notna(row.get('狀態')) else None,
            row.get('value'),
            row.get('threshold_min'),
            row.get('threshold_max'),
            str(row.get('unit')) if pd.notna(row.get('unit')) else None,
            pd.to_datetime(row.get('timestamp')) if pd.notna(row.get('timestamp')) else None
        )
    },
    {
        "excel_sheet_name": "設備標準值",
        "sql_table_name": "equipment_metric_thresholds",
        # --- 關鍵修正：從 sql_columns 列表中移除 "normal_value" ---
        "sql_columns": ["metric_type", "normal_value", "warning_min", "warning_max",
                        "critical_min", "critical_max", "emergency_min",
                        "emergency_max", "emergency_op", "last_updated"],
        "transform_row_data": lambda row: (
            row.get('metric_type'),
            row.get('normal_value'),
            row.get('warning_min'),
            row.get('warning_max'),
            row.get('critical_min'),
            row.get('critical_max'),
            row.get('emergency_min'),
            row.get('emergency_max'),
            row.get('emergency_op'),
            row.get('last_updated')
        )
    },
    {
        "excel_sheet_name": "異常紀錄",
        "sql_table_name": "error_logs",
        "sql_columns": ["error_id", "log_date", "equipment_id",
                        "deformation_mm", "rpm", "event_time",
                        "detected_anomaly_type", "downtime_min",
                        "resolved_at", "resolution_notes"],
        "transform_row_data": lambda row: (
            str(row.get('error_id')),
            pd.to_datetime(str(row.get('日期'))) if pd.notna(row.get('日期')) else None,
            str(row.get('equipment_id')),
            row.get('變形量(mm)'),
            row.get('轉速'),
            pd.to_datetime(str(row.get('時間'))) if pd.notna(row.get('時間')) else None,
            str(row.get('偵測異常類型')),
            str(row.get('停機時長(分鐘)')),
            pd.to_datetime(str(row.get('回復時間'))) if pd.notna(row.get('回復時間')) else None,
            str(row.get('備註')) if pd.notna(row.get('備註')) else None
        )
    },
    {
        "excel_sheet_name": "運作統計(月)",
        "sql_table_name": "stats_operational_monthly",
        "sql_columns": ["equipment_id", "year", "month",
                        "total_operation_duration", "downtime_hrs",
                        "downtime_rate_percent", "description"],
        "transform_row_data": lambda row: (
            str(row.get('equipment_id')), row.get('年'), row.get('月'),
            str(row.get('總運作時長')),
            str(row.get('停機總時長')), str(row.get('停機率(%)')),
            str(row.get('說明'))
        )
    },
    {
        "excel_sheet_name": "運作統計(季)",
        "sql_table_name": "stats_operational_quarterly",
        "sql_columns": ["equipment_id", "year", "quarter",
                        "total_operation_duration", "downtime_hrs",
                        "downtime_rate_percent", "description"],
        "transform_row_data": lambda row: (
            str(row.get('equipment_id')), row.get('年'), row.get('季度'),
            str(row.get('總運作時長')),
            str(row.get('停機總時長')), str(row.get('停機率(%)')),
            str(row.get('說明'))
        )
    },
    {
        "excel_sheet_name": "運作統計(年)",
        "sql_table_name": "stats_operational_yearly",
        "sql_columns": ["equipment_id", "year", "total_operation_duration",
                        "downtime_hrs", "downtime_rate_percent",
                        "description"],
        "transform_row_data": lambda row: (
            str(row.get('equipment_id')), row.get('年'),
            str(row.get('總運作時長')),
            str(row.get('停機總時長')), str(row.get('停機率(%)')),
            str(row.get('說明'))
        )
    },
    {
        "excel_sheet_name": "各異常統計(月)",
        "sql_table_name": "stats_abnormal_monthly",
        "sql_columns": ["equipment_id", "year", "month",
                        "detected_anomaly_type", "downtime_hrs",
                        "downtime_rate_percent", "description"],
        "transform_row_data": lambda row: (
            str(row.get('equipment_id')), row.get('年'), row.get('月'),
            str(row.get('偵測異常類型')),
            str(row.get('停機時長')), str(row.get('停機率(%)')),
            str(row.get('說明'))
        )
    },
    {
        "excel_sheet_name": "各異常統計(季)",
        "sql_table_name": "stats_abnormal_quarterly",
        "sql_columns": ["equipment_id", "year", "quarter",
                        "detected_anomaly_type", "downtime_hrs",
                        "downtime_rate_percent", "description"],
        "transform_row_data": lambda row: (
            str(row.get('equipment_id')), row.get('年'), row.get('季度'),
            str(row.get('偵測異常類型')),
            str(row.get('停機時長')), str(row.get('停機率(%)')),
            str(row.get('說明'))
        )
    },
    {
        "excel_sheet_name": "各異常統計(年)",
        "sql_table_name": "stats_abnormal_yearly",
        "sql_columns": ["equipment_id", "year", "detected_anomaly_type",
                        "downtime_hrs", "downtime_rate_percent",
                        "description"],
        "transform_row_data": lambda row: (
            str(row.get('equipment_id')), row.get('年'),
            str(row.get('偵測異常類型')),
            str(row.get('停機時長')), str(row.get('停機率(%)')),
            str(row.get('說明'))
        )
    }
]


# --- 5. 最終的匯入主程式 (已簡化) ---
def import_data_from_excel():
    """從指定的 Excel 檔案讀取數據，並使用高效能的批次插入將其匯入到資料庫中。"""
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.fast_executemany = True
            logger.info("成功連接到 MS SQL 資料庫，已啟用 fast_executemany。")

            for config in TABLE_CONFIGS:
                sheet_name = config["excel_sheet_name"]
                sql_table_name = config["sql_table_name"]
                sql_columns = config["sql_columns"]
                transform_row_data = config["transform_row_data"]

                logger.info(
                    f"--- 開始處理資料表: {sql_table_name} (來源: {sheet_name}) ---"
                )

                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{sql_table_name}]")
                    if cursor.fetchone()[0] > 0:
                        logger.info(
                            f"資料表 '{sql_table_name}' 已存在資料，跳過匯入。"
                        )
                        continue

                    data_frame = pd.read_excel(
                        EXCEL_FILE_PATH, sheet_name=sheet_name
                    )
                    data_frame = data_frame.where(pd.notna(data_frame), None)

                    if data_frame.empty:
                        logger.warning(f"工作表 '{sheet_name}' 為空，跳過。")
                        continue

                    logger.info(
                        f"成功讀取 Excel 工作表 '{sheet_name}'，"
                        f"共 {len(data_frame)} 行。"
                    )

                    sql_columns_str = ', '.join(
                        [f"[{col}]" for col in sql_columns]
                    )
                    placeholders_str = ', '.join(['?' for _ in sql_columns])
                    insert_sql = (
                        f"INSERT INTO [{sql_table_name}] ({sql_columns_str}) "
                        f"VALUES ({placeholders_str})"
                    )

                    data_to_insert = [
                        transform_row_data(row) for _, row in data_frame.iterrows()
                    ]

                    if data_to_insert:
                        logger.info(
                            f"準備將 {len(data_to_insert)} 行資料批次插入到 "
                            f"'{sql_table_name}'..."
                        )
                        try:
                            # 直接執行插入，因為 database.py 中的表格結構現在是正確的
                            cursor.executemany(insert_sql, data_to_insert)
                            conn.commit()
                            logger.info(
                                f"'{sql_table_name}' 資料匯入完成。"
                            )
                        except pyodbc.Error as e:
                            logger.error(
                                f"批次插入到 '{sql_table_name}' 時發生資料庫錯誤，"
                                f"正在回滾: {e}"
                            )
                            conn.rollback()

                except Exception as e:
                    logger.error(
                        f"處理工作表 '{sheet_name}' 時發生未預期錯誤: {e}"
                    )
                    continue

    except Exception as e:
        logger.error(f"執行 Excel 匯入腳本時發生未知錯誤: {e}")


if __name__ == '__main__':
    """
    使用 `if __name__ == '__main__':` 是一個 Python 的標準做法。
    它確保 `import_data_from_excel()` 只有在腳本被直接執行時才會被調用，
    而不是在它被其他 Python 腳本匯入時。這讓腳本既可以獨立運行，也可以被當作模組使用。
    """
    logger.info("腳本啟動：開始匯入初始資料到資料庫。")
    import_data_from_excel()
    logger.info("所有資料匯入任務完成。")
