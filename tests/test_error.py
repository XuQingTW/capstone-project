import pyodbc
import datetime
import os

#MS SQL Server 連線配置
class Config:
    """應用程式配置，集中管理所有環境變數"""
    DB_SERVER = os.getenv("DB_SERVER", "your_server_name.database.windows.net") 
    DB_NAME = os.getenv("DB_NAME", "Project") 
    DB_USER = os.getenv("DB_USER", "your_username") 
    DB_PASSWORD = os.getenv("DB_PASSWORD", "your_password") 
    DB_DRIVER = '{ODBC Driver 17 for SQL Server}' 

# 主程式
def main():
    """主執行函式"""
    config = Config()
    conn = None

    #建立連線字串
    conn_str = (
        f"DRIVER={config.DB_DRIVER};"
        f"SERVER={config.DB_SERVER};"
        f"DATABASE={config.DB_NAME};"
        f"UID={config.DB_USER};"
        f"PWD={config.DB_PASSWORD};"
    )
    
    try:
        #建立資料庫連線和游標
        print("正在嘗試連線到資料庫...")
        conn = pyodbc.connect(conn_str)
        cur = conn.cursor()
        print("資料庫連線成功！\n")

        #使用者互動主流程
        action = input("請輸入 'event'（新增異常）或 'resolved'（填寫回復）: ").strip().lower()

        # 新增異常
        if action == "event":
            cur.execute("SELECT MAX(error_id) FROM error_logs")
            max_id = cur.fetchval() # fetchval() 直接取得第一行第一欄的值
            next_id = 1 if max_id is None else max_id + 1
            print(f"目前的ID最大值為: {max_id}，下一個將使用的ID為: {next_id}")
            equipment_id = input("請輸入 equipment_id：")
            detected_anomaly_type = input("請輸入 detected_anomaly_type（轉速太低 或 刀具裂痕 或 刀具變形）：").strip()

            if detected_anomaly_type in ["刀具裂痕", "刀具變形"]:
                while True:
                    deformation_mm = input("請輸入 deformation_mm（變形量，單位mm，不可空）：").strip()
                    try:
                        deformation_mm_val = float(deformation_mm)
                        break
                    except ValueError:
                        print("錯誤：請輸入有效的數值！")
                rpm = 3000
            elif detected_anomaly_type == "轉速太低":
                deformation_mm_val = 0
                while True:
                    rpm_input = input("請輸入 rpm（轉速，不可空）：").strip()
                    try:
                        rpm = int(rpm_input)
                        break
                    except ValueError:
                        print("錯誤：請輸入有效的整數數值！")
            else:
                print("異常類型輸入錯誤，程式即將結束！")
                return

            notes = input("請輸入 notes（備註，請先填寫異常的嚴重程度）：")
            log_date = datetime.date.today()
            event_time = datetime.datetime.now()

            # 寫入資料
            sql = """
            INSERT INTO error_logs (
                error_id, log_date, equipment_id, deformation_mm, rpm,
                event_time, detected_anomaly_type, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (next_id, log_date, equipment_id, deformation_mm_val, rpm, event_time, detected_anomaly_type, notes)

            cur.execute(sql, params)
            conn.commit()
            print("\n")
            print("已成功新增異常事件至 error_logs！")
            print(f"本次異常的 error_id 為：{next_id}")
            print("\n")

        #填寫回復
        elif action == "resolved":
            error_id = input("請輸入要回復的 error_id：").strip()
            cur.execute("SELECT resolved_time, event_time FROM error_logs WHERE error_id = ?", (error_id,))
            row = cur.fetchone()

            if not row:
                print("錯誤：找不到此 error_id！")
            elif row.resolved_time is not None:
                print("提示：該 error_id 已經有回復時間，不可重複填寫！")
            else:
                resolved_time = datetime.datetime.now()
                event_time = row.event_time
                
                # 防呆：確保 event_time 是 datetime 物件
                if isinstance(event_time, str):
                    event_time = datetime.datetime.fromisoformat(event_time)
                
                total_seconds = int((resolved_time - event_time).total_seconds())
                min_part = total_seconds // 60
                sec_part = total_seconds % 60

                cur.execute(
                    "UPDATE error_logs SET resolved_time = ?, downtime_min = ?, downtime_sec = ? WHERE error_id = ?",
                    (resolved_time, min_part, sec_part, error_id)
                )
                conn.commit()
                
                print("\n")
                print(f"已成功更新 Error ID: {error_id}")
                print(f"填寫回復時間 resolved_time：{resolved_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"自動計算停機時間：{min_part}分 {sec_part}秒")
        else:
            print("輸入錯誤，請重新輸入 'event' 或 'resolved'。")

    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"資料庫連線或操作發生錯誤")
        print(f"錯誤訊息: {ex}")
        print("請檢查您的網路連線、資料庫伺服器狀態以及連線參數。")

    finally:
        # --- 關鍵：無論成功或失敗，最後都確保連線被關閉 ---
        if conn:
            conn.close()
            print("\n資料庫連線已安全關閉。")


if __name__ == "__main__":
    main()