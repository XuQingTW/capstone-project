import pandas as pd
import pyodbc

# --- 1. 讀取 Excel 資料 ---
try:
    df_equipment = pd.read_csv('simulated_data (1).xlsx - equipment.csv')
    print("成功讀取 'equipment' 資料表內容。")
    print(df_equipment.head())
except FileNotFoundError:
    print("錯誤：找不到 'simulated_data (1).xlsx - equipment.csv' 檔案。")
    exit()

# --- 2. 連接 MS SQL 資料庫 ---
# 請替換成您的 MS SQL 資料庫連線資訊
DB_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}', # 或其他您安裝的 ODBC 驅動程式
    'server': '您的伺服器名稱或IP',
    'database': '您的資料庫名稱',
    'uid': '您的使用者名稱',
    'pwd': '您的密碼'
}

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

# --- 3. 將資料寫入 SQL 資料庫 ---
# 針對您提供的 SQL DDL，我們將資料框的欄位名稱與類型進行對應
# 並將資料寫入到 'equipment' 資料表

# 定義目標資料表名稱
table_name = 'equipment'

# 創建資料表 (如果不存在)。
# 這邊的 CREATE TABLE 語句是基於您提供的 DDL。
create_table_sql = f"""
CREATE TABLE {table_name} (
    [eq_id] NVARCHAR(255) NULL,
    [name] NVARCHAR(255) NULL,
    [eq_type] NVARCHAR(100) NULL,
    [location] NVARCHAR(255) NULL,
    [status] NVARCHAR(100) NULL,
    [created_at] DATETIME2 NULL,
    [model_number] NVARCHAR(100) NULL,
    [purchase_date] DATETIME2 NULL,
    [last_maintenance_date] DATETIME2 NULL
);
"""

try:
    cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name};")
    cursor.execute(create_table_sql)
    conn.commit()
    print(f"\n成功創建或重建 '{table_name}' 資料表。")
except pyodbc.ProgrammingError as e:
    print(f"\n創建資料表時發生錯誤：{e}")
    # 如果資料表已經存在，且您不想刪除重建，可以註釋掉上面的 DROP TABLE 和 CREATE TABLE

# 準備插入資料的 SQL 語句
# 注意：這裡使用參數化查詢以防止 SQL 注入
insert_sql = f"""
INSERT INTO {table_name} (
    [eq_id], [name], [eq_type], [location], [status],
    [created_at], [model_number], [purchase_date], [last_maintenance_date]
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# 遍歷資料框並插入資料
for index, row in df_equipment.iterrows():
    try:
        # 將 NaN（Not a Number）值轉換為 None，以便 SQL NULL 處理
        # 同時處理日期格式，確保它們是 datetime 物件或 None
        data_to_insert = (
            row.get('eq_id', None) if pd.notna(row.get('eq_id')) else None,
            row.get('name', None) if pd.notna(row.get('name')) else None,
            row.get('eq_type', None) if pd.notna(row.get('eq_type')) else None,
            row.get('location', None) if pd.notna(row.get('location')) else None,
            row.get('status', None) if pd.notna(row.get('status')) else None,
            pd.to_datetime(row['created_at']) if pd.notna(row.get('created_at')) else None,
            row.get('model_number', None) if pd.notna(row.get('model_number')) else None,
            pd.to_datetime(row['purchase_date']) if pd.notna(row.get('purchase_date')) else None,
            pd.to_datetime(row['last_maintenance_date']) if pd.notna(row.get('last_maintenance_date')) else None
        )
        cursor.execute(insert_sql, data_to_insert)
    except Exception as e:
        print(f"插入第 {index} 行資料時發生錯誤：{e}")
        print(f"資料：{row.to_dict()}")
        conn.rollback() # 回滾當前事務
        continue # 跳過當前行，繼續處理下一行

conn.commit()
print(f"\n所有資料已成功匯入到 '{table_name}' 資料表。")

# 查詢資料以驗證
try:
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\n'{table_name}' 資料表中的總行數：{count}")

    cursor.execute(f"SELECT TOP 5 * FROM {table_name}")
    rows = cursor.fetchall()
    print("\n前 5 行資料：")
    for row in rows:
        print(row)
except Exception as e:
    print(f"\n查詢資料時發生錯誤：{e}")


# 關閉連線
cursor.close()
conn.close()
print("\n資料庫連線已關閉。")