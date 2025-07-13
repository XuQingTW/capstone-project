import pyodbc
import os

# 1. 資料庫連線設定
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME = os.getenv("DB_NAME", "conversations")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
driver = '{ODBC Driver 17 for SQL Server}'

# 2. 建立連線
connection_string = (
    f"DRIVER={driver};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    "Trusted_Connection=yes;"
)

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    print(f"✅ 已連線：{DB_SERVER} / 資料庫：{DB_NAME}")

    # 3. 移除所有外鍵約束
    print("🔓 移除所有外鍵約束...")
    cursor.execute("""
        DECLARE @sql NVARCHAR(MAX) = '';
        SELECT @sql += 'ALTER TABLE [' + sch.name + '].[' + t.name + '] DROP CONSTRAINT [' + fk.name + '];'
        FROM sys.foreign_keys fk
        JOIN sys.tables t ON fk.parent_object_id = t.object_id
        JOIN sys.schemas sch ON t.schema_id = sch.schema_id;
        EXEC sp_executesql @sql;
    """)

    # 4. 抓出所有資料表
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
    """)
    tables = cursor.fetchall()

    if not tables:
        print("⚠️ 無資料表可刪除。")
    else:
        print("🗑️ 開始刪除所有資料表...")
        for schema, table in tables:
            drop_stmt = f"DROP TABLE [{schema}].[{table}]"
            print(f"   → {drop_stmt}")
            cursor.execute(drop_stmt)

        conn.commit()
        print("✅ 所有資料表與結構已刪除完成")

except Exception as e:
    print(f"❌ 執行錯誤：{e}")

finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()
