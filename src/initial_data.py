import pandas as pd
import pyodbc
import os
import re # 用於解析時間字符串

# 如果您使用 .env 檔案來管理資料庫憑證，請取消註釋下方兩行
# from dotenv import load_dotenv
# load_dotenv()

# --- 1. 設定 Excel 檔案路徑與資料庫連線資訊 ---
# 請確認此路徑是您模擬資料檔案的正確絕對路徑
excel_file_path = r'C:\Users\sunny\Downloads\simulated_data (1).xlsx'

DB_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}', # 或其他您安裝的 ODBC 驅動程式
    'server': os.getenv("DB_SERVER", "localhost"), # 從環境變數獲取，如果沒有則用 'localhost'
    'database': os.getenv("DB_NAME", "Project"),   # 從環境變數獲取，如果沒有則用 'Project'
    'uid': os.getenv("DB_USER"),                   # 從環境變數獲取
    'pwd': os.getenv("DB_PASSWORD")                # 從環境變數獲取
}

# 檢查是否有缺失的環境變數
if not all([DB_CONFIG['uid'], DB_CONFIG['pwd']]):
    print("錯誤：資料庫使用者名稱或密碼環境變數未設定。")
    print("請檢查您的 .env 檔案或直接在程式碼中設定 DB_CONFIG['uid'] 和 DB_CONFIG['pwd']。")
    exit()

# --- 2. 連接 MS SQL 資料庫 ---
try:
    conn = pyodbc.connect(
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['uid']};"
        f"PWD={DB_CONFIG['pwd']}"
    )
    cursor = conn.cursor()
    print("\n成功連接到 MS SQL 資料庫。")
except pyodbc.Error as ex:
    sqlstate = ex.args[0]
    print(f"\n錯誤：無法連接到 MS SQL 資料庫。錯誤代碼: {sqlstate}")
    print(ex)
    exit()

# --- 3. 定義每個資料表的匯入配置 ---
# 包含 Excel 工作表名稱、SQL 目標資料表名稱以及欄位映射與數據轉換邏輯
# column_map: 從 Excel 欄位名稱 到 SQL 欄位名稱 的映射
# transform_row_data: 一個函式，接收一個 Pandas DataFrame 的 row，返回一個 tuple，
#                     其順序必須與 insert_sql 中的欄位順序完全一致，且包含數據轉換邏輯。

table_configs = [
    {
        "excel_sheet_name": "equipment", # Excel 工作表名稱
        "sql_table_name": "equipment",   # 對應的 SQL 資料表名稱
        "column_map": {                 # Excel 欄位 -> SQL 欄位
            "ID": "id",
            "eq_id": "eq_id",
            "name": "name",
            "eq_type": "eq_type",
            "location": "location",
            "location.1": "status", # 假設第二個 'location' 在 Pandas 中會讀作 'location.1'
            "last_updated": "last_updated"
        },
        "transform_row_data": lambda row: (
            row.get('ID', None) if pd.notna(row.get('ID')) else None,
            row.get('eq_id', None) if pd.notna(row.get('eq_id')) else None,
            row.get('name', None) if pd.notna(row.get('name')) else None,
            row.get('eq_type', None) if pd.notna(row.get('eq_type')) else None,
            row.get('location', None) if pd.notna(row.get('location')) else None,
            row.get('location.1', None) if pd.notna(row.get('location.1')) else None, # 對應到 status
            pd.to_datetime(row.get('last_updated')) if pd.notna(row.get('last_updated')) else None
        )
    },
    {
        "excel_sheet_name": "alert_history", # Excel 工作表名稱
        "sql_table_name": "alert_history",   # 對應的 SQL 資料表名稱
        "column_map": {                 # Excel 欄位 -> SQL 欄位
            "ID": "id",
            "equipment_id": "equipment_id",
            "alert_type": "alert_type",
            "severity": "severity",
            "訊息": "message"
        },
        "transform_row_data": lambda row: (
            row.get('ID', None) if pd.notna(row.get('ID')) else None,
            row.get('equipment_id', None) if pd.notna(row.get('equipment_id')) else None,
            row.get('alert_type', None) if pd.notna(row.get('alert_type')) else None,
            row.get('severity', None) if pd.notna(row.get('severity')) else None,
            row.get('訊息', None) if pd.notna(row.get('訊息')) else None
        )
    },
{
        "excel_sheet_name": "異常紀錄error_log", # Excel 工作表名稱
        "sql_table_name": "error_logs",         # 對應的 SQL 資料表名稱
        "column_map": {                 # Excel 欄位 -> SQL 欄位
            "日期": "log_date",
            "eq_id": "eq_id",
            "變形量(mm)": "deformation_mm",
            "轉速": "rpm",
            "時間": "event_time_str",
            "偵測異常類型": "detected_anomaly_type",
            "停機時長": "downtime_duration",
            "回復時間": "resolved_at_str",
            "備註": "resolution_notes"
        },
        "transform_row_data": lambda row: (
            pd.to_datetime(row.get('日期')) if pd.notna(row.get('日期')) else None,
            row.get('eq_id', None) if pd.notna(row.get('eq_id')) else None,
            row.get('變形量(mm)', None) if pd.notna(row.get('變形量(mm)')) else None,
            row.get('轉速', None) if pd.notna(row.get('轉速')) else None,
            row.get('時間', None) if pd.notna(row.get('時間')) else None,
            row.get('偵測異常類型', None) if pd.notna(row.get('偵測異常類型')) else None,
            row.get('停機時長', None) if pd.notna(row.get('停機時長')) else None,
            row.get('回復時間', None) if pd.notna(row.get('回復時間')) else None,
            row.get('備註', None) if pd.notna(row.get('備註')) else None
        )
    },
    {
        "excel_sheet_name": "運作統計(月)",
        "sql_table_name": "stats_operational_monthly",
        "column_map": {
            "月": "month",
            "總運作時長": "total_operation_duration",
            "停機總時長": "total_downtime_duration",
            "停機率(%)": "downtime_rate_percent",
            "說明": "description"
        },
        "transform_row_data": lambda row: (
            row.get('月', None) if pd.notna(row.get('月')) else None,
            row.get('總運作時長', None) if pd.notna(row.get('總運作時長')) else None,
            row.get('停機總時長', None) if pd.notna(row.get('停機總時長')) else None,
            row.get('停機率(%)', None) if pd.notna(row.get('停機率(%)')) else None,
            row.get('說明', None) if pd.notna(row.get('說明')) else None
        )
    },
    {
        "excel_sheet_name": "運作統計(季)",
        "sql_table_name": "stats_operational_quarterly",
        "column_map": {
            "equipment_id": "equipment_id",
            "年": "year",
            "季度": "quarter",
            "總運作時長": "total_operation_duration",
            "停機總時長": "total_downtime_duration",
            "停機率(%)": "downtime_rate_percent",
            "說明": "description"
        },
        "transform_row_data": lambda row: (
            row.get('equipment_id', None) if pd.notna(row.get('equipment_id')) else None,
            row.get('年', None) if pd.notna(row.get('年')) else None,
            row.get('季度', None) if pd.notna(row.get('季度')) else None,
            row.get('總運作時長', None) if pd.notna(row.get('總運作時長')) else None,
            row.get('停機總時長', None) if pd.notna(row.get('停機總時長')) else None,
            row.get('停機率(%)', None) if pd.notna(row.get('停機率(%)')) else None,
            row.get('說明', None) if pd.notna(row.get('說明')) else None
        )
    },
    {
        "excel_sheet_name": "運作統計(年)",
        "sql_table_name": "stats_operational_yearly",
        "column_map": {
            "equipment_id": "equipment_id",
            "年": "year",
            "總運作時長": "total_operation_duration",
            "停機總時長": "total_downtime_duration",
            "停機率(%)": "downtime_rate_percent",
            "說明": "description"
        },
        "transform_row_data": lambda row: (
            row.get('equipment_id', None) if pd.notna(row.get('equipment_id')) else None,
            row.get('年', None) if pd.notna(row.get('年')) else None,
            row.get('總運作時長', None) if pd.notna(row.get('總運作時長')) else None,
            row.get('停機總時長', None) if pd.notna(row.get('停機總時長')) else None,
            row.get('停機率(%)', None) if pd.notna(row.get('停機率(%)')) else None,
            row.get('說明', None) if pd.notna(row.get('說明')) else None
        )
    },
    {
        "excel_sheet_name": "各異常統計(月)",
        "sql_table_name": "stats_abnormal_monthly",
        "column_map": {
            "equipment_id": "equipment_id",
            "年": "year",
            "月": "month",
            "偵測異常類型": "detected_anomaly_type",
            "停機時長": "downtime_duration",
            "停機率(%)": "downtime_rate_percent",
            "說明": "description"
        },
        "transform_row_data": lambda row: (
            row.get('equipment_id', None) if pd.notna(row.get('equipment_id')) else None,
            row.get('年', None) if pd.notna(row.get('年')) else None,
            row.get('月', None) if pd.notna(row.get('月')) else None,
            row.get('偵測異常類型', None) if pd.notna(row.get('偵測異常類型')) else None,
            row.get('停機時長', None) if pd.notna(row.get('停機時長')) else None,
            row.get('停機率(%)', None) if pd.notna(row.get('停機率(%)')) else None,
            row.get('說明', None) if pd.notna(row.get('說明')) else None
        )
    },
    {
        "excel_sheet_name": "各異常統計(季)",
        "sql_table_name": "stats_abnormal_quarterly",
        "column_map": {
            "equipment_id": "equipment_id",
            "年": "year",
            "季度": "quarter",
            "偵測異常類型": "detected_anomaly_type",
            "停機時長": "downtime_duration",
            "停機率(%)": "downtime_rate_percent",
            "說明": "description"
        },
        "transform_row_data": lambda row: (
            row.get('equipment_id', None) if pd.notna(row.get('equipment_id')) else None,
            row.get('年', None) if pd.notna(row.get('年')) else None,
            row.get('季度', None) if pd.notna(row.get('季度')) else None,
            row.get('偵測異常類型', None) if pd.notna(row.get('偵測異常類型')) else None,
            row.get('停機時長', None) if pd.notna(row.get('停機時長')) else None,
            row.get('停機率(%)', None) if pd.notna(row.get('停機率(%)')) else None,
            row.get('說明', None) if pd.notna(row.get('說明')) else None
        )
    },
    {
        "excel_sheet_name": "各異常統計(年)",
        "sql_table_name": "stats_abnormal_yearly",
        "column_map": {
            "equipment_id": "equipment_id",
            "年": "year",
            "偵測異常類型": "detected_anomaly_type",
            "停機時長": "downtime_duration",
            "停機率(%)": "downtime_rate_percent",
            "說明": "description"
        },
        "transform_row_data": lambda row: (
            row.get('equipment_id', None) if pd.notna(row.get('equipment_id')) else None,
            row.get('年', None) if pd.notna(row.get('年')) else None,
            row.get('偵測異常類型', None) if pd.notna(row.get('偵測異常類型')) else None,
            row.get('停機時長', None) if pd.notna(row.get('停機時長')) else None,
            row.get('停機率(%)', None) if pd.notna(row.get('停機率(%)')) else None,
            row.get('說明', None) if pd.notna(row.get('說明')) else None
        )
    }
]

# --- 4. 迴圈遍歷配置並匯入資料 ---
for config in table_configs:
    sheet_name = config["excel_sheet_name"]
    sql_table_name = config["sql_table_name"]
    column_map = config["column_map"]
    transform_row_data = config["transform_row_data"]

    print(f"\n--- 開始處理資料表: {sql_table_name} (來源 Excel 工作表: {sheet_name}) ---")

    try:
        # 讀取 Excel 檔案的特定工作表
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        
        # 檢查 DataFrame 是否為空（只有標頭沒有數據行）
        if df.empty:
            print(f"警告：工作表 '{sheet_name}' 讀取後為空，跳過匯入。")
            continue

        print(f"成功讀取 '{sheet_name}' 工作表內容。")
        print("DataFrame 實際欄位名稱：", df.columns.tolist())

        # 根據 column_map 準備 SQL INSERT 語句的欄位列表
        sql_columns = ', '.join([f"[{sql_col}]" for sql_col in column_map.values()])
        placeholders = ', '.join(['?' for _ in column_map.values()])
        
        insert_sql = f"""
        INSERT INTO {sql_table_name} (
            {sql_columns}
        ) VALUES ({placeholders})
        """

        # 遍歷資料框並插入資料
        successful_inserts = 0
        failed_inserts = 0
        for index, row in df.iterrows():
            try:
                data_to_insert = transform_row_data(row)
                cursor.execute(insert_sql, data_to_insert)
                successful_inserts += 1
            except Exception as e:
                failed_inserts += 1
                print(f"插入 {sql_table_name} 表格第 {index} 行資料時發生錯誤：{e}")
                print(f"原始資料：{row.to_dict()}")
                conn.rollback() # 回滾當前事務
                continue # 跳過當前行，繼續處理下一行
        
        conn.commit()
        print(f"\n'{sql_table_name}' 資料表資料匯入完成。成功: {successful_inserts} 行, 失敗: {failed_inserts} 行。")

        # 查詢資料以驗證
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {sql_table_name}")
            count = cursor.fetchone()[0]
            print(f"'{sql_table_name}' 資料表中的總行數：{count}")

            cursor.execute(f"SELECT TOP 5 * FROM {sql_table_name}")
            rows = cursor.fetchall()
            print("前 5 行資料：")
            for r in rows:
                print(r)
        except Exception as e:
            print(f"查詢 '{sql_table_name}' 資料時發生錯誤：{e}")

    except FileNotFoundError:
        print(f"錯誤：找不到 Excel 檔案 '{excel_file_path}'。請檢查路徑是否正確。")
        break # 如果主 Excel 檔案找不到，則停止所有處理
    except KeyError: # 當 sheet_name 不存在時
        print(f"警告：Excel 工作表 '{sheet_name}' 不存在於 '{excel_file_path}' 中，跳過此資料表。")
    except Exception as e:
        print(f"處理 '{sheet_name}' 工作表時發生其他錯誤：{e}")
        continue # 繼續處理下一個資料表

# --- 5. 關閉連線 ---
cursor.close()
conn.close()
print("\n所有資料表資料匯入完成。資料庫連線已關閉。")
