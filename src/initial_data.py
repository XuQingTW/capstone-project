import os
import re
import logging
import pandas as pd
import pyodbc
from database import db

# --- 1. 設定日誌記錄 ---
# 配置日誌記錄器，以便提供結構化的腳本執行信息
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- 2. 設定 Excel 檔案路徑與資料表配置 ---
# 確認 Excel 檔案的絕對路徑
EXCEL_FILE_PATH = r'C:\Users\sunny\Downloads\capstone-project\data\simulated_data (1).xlsx'

# 定義每個資料表的匯入配置
# excel_sheet_name: Excel 工作表名稱
# sql_table_name: SQL 目標資料表名稱
# column_map: Excel 欄位到 SQL 欄位的映射
# transform_row_data: 一個函式，用於轉換單行數據以符合 SQL 表格結構
TABLE_CONFIGS = [
    {
        "excel_sheet_name": "equipment",
        "sql_table_name": "equipment",
        "column_map": {
            "ID": "id",
            "eq_id": "eq_id",
            "name": "name",
            "eq_type": "eq_type",
            "location": "location",
            "location.1": "status",
            "last_updated": "last_updated"
        },
        "transform_row_data": lambda row: (
            row.get('ID'), row.get('eq_id'), row.get('name'), row.get('eq_type'),
            row.get('location'), row.get('location.1'),
            pd.to_datetime(row.get('last_updated')) if pd.notna(row.get('last_updated')) else None
        )
    },
    {
        "excel_sheet_name": "alert_history",
        "sql_table_name": "alert_history",
        "column_map": {
            "ID": "id",
            "equipment_id": "equipment_id",
            "alert_type": "alert_type",
            "severity": "severity",
            "訊息": "message"
        },
        "transform_row_data": lambda row: (
            row.get('ID'), row.get('equipment_id'),
            # 修正：確保從 'alert_type' 欄位讀取數據，以匹配 column_map
            row.get('alert_type'),
            row.get('severity'), row.get('訊息')
        )
    },
    {
        "excel_sheet_name": "異常紀錄error_log",
        "sql_table_name": "error_logs",
        "column_map": {
            "時間": "log_date",
            "時間_EQ_ID": "eq_id",
            "變形量(mm)": "deformation_mm",
            "轉速": "rpm",
            "時間_time_str": "event_time_str",
            "偵測異常類型": "detected_anomaly_type",
            "停機時長": "downtime_duration",
            "resolved_at": "resolved_at_str",
            "resolution_notes": "resolution_notes"
        },
        "transform_row_data": lambda row: (
            (pd.to_datetime(re.search(r'\d{4}[-/.]\d{1,2}[-/.]\d{1,2}', str(row.get('時間', ''))).group(0))
             if re.search(r'\d{4}[-/.]\d{1,2}[-/.]\d{1,2}', str(row.get('時間', ''))) else None),
            (re.search(r'(EQ\d{3})', str(row.get('時間', ''))).group(1)
             if re.search(r'(EQ\d{3})', str(row.get('時間', ''))) else None),
            row.get('變形量(mm)'), row.get('轉速'),
            (re.search(r'(am|pm)\s*\d{1,2}:\d{2}', str(row.get('時間', ''))).group(0)
             if re.search(r'(am|pm)\s*\d{1,2}:\d{2}', str(row.get('時間', ''))) else None),
            row.get('偵測異常類型'), row.get('停機時長'),
            row.get('resolved_at'), row.get('resolution_notes')
        )
    },
    # ... 其他表格配置保持不變 ...
    {
        "excel_sheet_name": "運作統計(月)",
        "sql_table_name": "stats_operational_monthly",
        "column_map": {"月": "month", "總運作時長": "total_operation_duration", "停機總時長": "total_downtime_duration", "停機率(%)": "downtime_rate_percent", "說明": "description"},
        "transform_row_data": lambda row: (row.get('月'), row.get('總運作時長'), row.get('停機總時長'), row.get('停機率(%)'), row.get('說明'))
    },
    {
        "excel_sheet_name": "運作統計(季)",
        "sql_table_name": "stats_operational_quarterly",
        "column_map": {"equipment_id": "equipment_id", "年": "year", "季度": "quarter", "總運作時長": "total_operation_duration", "停機總時長": "total_downtime_duration", "停機率(%)": "downtime_rate_percent", "說明": "description"},
        "transform_row_data": lambda row: (row.get('equipment_id'), row.get('年'), row.get('季度'), row.get('總運作時長'), row.get('停機總時長'), row.get('停機率(%)'), row.get('說明'))
    },
    {
        "excel_sheet_name": "運作統計(年)",
        "sql_table_name": "stats_operational_yearly",
        "column_map": {"equipment_id": "equipment_id", "年": "year", "總運作時長": "total_operation_duration", "停機總時長": "total_downtime_duration", "停機率(%)": "downtime_rate_percent", "說明": "description"},
        "transform_row_data": lambda row: (row.get('equipment_id'), row.get('年'), row.get('總運作時長'), row.get('停機總時長'), row.get('停機率(%)'), row.get('說明'))
    },
    {
        "excel_sheet_name": "各異常統計(月)",
        "sql_table_name": "stats_abnormal_monthly",
        "column_map": {"equipment_id": "equipment_id", "年": "year", "月": "month", "偵測異常類型": "detected_anomaly_type", "停機時長": "downtime_duration", "停機率(%)": "downtime_rate_percent", "說明": "description"},
        "transform_row_data": lambda row: (row.get('equipment_id'), row.get('年'), row.get('月'), row.get('偵測異常類型'), row.get('停機時長'), row.get('停機率(%)'), row.get('說明'))
    },
    {
        "excel_sheet_name": "各異常統計(季)",
        "sql_table_name": "stats_abnormal_quarterly",
        "column_map": {"equipment_id": "equipment_id", "年": "year", "季度": "quarter", "偵測異常類型": "detected_anomaly_type", "停機時長": "downtime_duration", "停機率(%)": "downtime_rate_percent", "說明": "description"},
        "transform_row_data": lambda row: (row.get('equipment_id'), row.get('年'), row.get('季度'), row.get('偵測異常類型'), row.get('停機時長'), row.get('停機率(%)'), row.get('說明'))
    },
    {
        "excel_sheet_name": "各異常統計(年)",
        "sql_table_name": "stats_abnormal_yearly",
        "column_map": {"equipment_id": "equipment_id", "年": "year", "偵測異常類型": "detected_anomaly_type", "停機時長": "downtime_duration", "停機率(%)": "downtime_rate_percent", "說明": "description"},
        "transform_row_data": lambda row: (row.get('equipment_id'), row.get('年'), row.get('偵測異常類型'), row.get('停機時長'), row.get('停機率(%)'), row.get('說明'))
    }
]


def import_data_from_excel():
    """
    從指定的 Excel 檔案讀取數據，並將其匯入到 MS SQL Server 資料庫中。
    採用 `Old-initial_data.py` 的結構化風格，使用集中的資料庫連接和日誌記錄。
    """
    try:
        # 使用 db 物件獲取資料庫連線
        with db._get_connection() as conn:
            cursor = conn.cursor()
            logger.info("成功連接到 MS SQL 資料庫。")

            # 遍歷所有表格配置進行資料匯入
            for config in TABLE_CONFIGS:
                sheet_name = config["excel_sheet_name"]
                sql_table_name = config["sql_table_name"]
                transform_row_data = config["transform_row_data"]

                logger.info(f"--- 開始處理資料表: {sql_table_name} (來源: {sheet_name}) ---")

                try:
                    # 檢查目標資料表是否已存在資料
                    cursor.execute(f"SELECT COUNT(*) FROM {sql_table_name}")
                    if cursor.fetchone()[0] > 0:
                        logger.info(f"資料表 '{sql_table_name}' 已存在資料，跳過匯入。")
                        continue

                    # 讀取 Excel 工作表
                    data_frame = pd.read_excel(EXCEL_FILE_PATH, sheet_name=sheet_name)
                    data_frame = data_frame.where(pd.notna(data_frame), None) # 將 NaN 轉換為 None

                    if data_frame.empty:
                        logger.warning(f"工作表 '{sheet_name}' 為空，跳過。")
                        continue
                    
                    logger.info(f"成功讀取 '{sheet_name}' 工作表，共 {len(data_frame)} 行。")

                    # 準備 SQL INSERT 語句
                    sql_columns_list = [f"[{col}]" for col in config["column_map"].values()]
                    sql_columns_str = ', '.join(sql_columns_list)
                    placeholders_str = ', '.join(['?' for _ in sql_columns_list])
                    insert_sql = f"INSERT INTO {sql_table_name} ({sql_columns_str}) VALUES ({placeholders_str})"

                    # 逐行插入資料
                    successful_inserts = 0
                    for index, row in data_frame.iterrows():
                        try:
                            data_to_insert = transform_row_data(row)
                            cursor.execute(insert_sql, data_to_insert)
                            successful_inserts += 1
                        except Exception as e:
                            logger.error(f"插入第 {index + 1} 行到 '{sql_table_name}' 時失敗: {e}")
                            logger.error(f"失敗的資料: {row.to_dict()}")
                            conn.rollback() # 回滾單筆失敗的交易

                    conn.commit()
                    logger.info(f"'{sql_table_name}' 資料匯入完成。成功插入 {successful_inserts} 行。")

                except pd.errors.ParserError as e:
                    logger.error(f"解析 Excel 工作表 '{sheet_name}' 失敗: {e}")
                except Exception as e:
                    logger.error(f"處理工作表 '{sheet_name}' 時發生未預期錯誤: {e}")
                    # 發生錯誤時跳到下一個表格
                    continue
        
    except FileNotFoundError:
        logger.error(f"錯誤：找不到 Excel 檔案 '{EXCEL_FILE_PATH}'。請檢查路徑。")
    except pyodbc.Error as e:
        logger.error(f"資料庫操作失敗: {e}")
    except Exception as e:
        logger.error(f"執行匯入腳本時發生未知錯誤: {e}")


if __name__ == '__main__':
    logger.info("腳本啟動：開始從 Excel 匯入初始資料到資料庫。")
    import_data_from_excel()
    logger.info("所有資料匯入任務完成。")