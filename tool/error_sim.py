import pyodbc
import datetime
import os

#MS SQL Server 連線配置
class Config:
    """應用程式配置，集中管理所有環境變數"""
    DB_SERVER = os.getenv("DB_SERVER") 
    DB_NAME = os.getenv("DB_NAME") 
    DB_USER = os.getenv("DB_USER") 
    DB_PASSWORD = os.getenv("DB_PASSWORD") 
    DB_DRIVER = '{ODBC Driver 17 for SQL Server}'

class UserCancelledError(Exception):
    pass
def get_input_or_raise(prompt):
    CANCEL_KEYS = {'quit', 'cancel', '取消'}
    full_prompt = f"{prompt} (輸入 'quit' 或 '取消' 來中止操作): "
    user_input = input(full_prompt).strip()
    if user_input.lower() in CANCEL_KEYS:
        raise UserCancelledError() 
    return user_input

# 主程式
# 主程式
def main():
    config = Config()
    conn = None
    conn_str = f"DRIVER={config.DB_DRIVER};SERVER={config.DB_SERVER};DATABASE={config.DB_NAME};UID={config.DB_USER};PWD={config.DB_PASSWORD};"
    
    try:
        print("正在嘗試連線到資料庫...")
        conn = pyodbc.connect(conn_str)
        cur = conn.cursor()
        print("資料庫連線成功！\n")
        try:
            action = get_input_or_raise("請輸入 'event'（新增異常）或 'resolved'（填寫回復）").lower()

            #新增異常
            if action == "event":
                cur.execute("SELECT MAX(error_id) FROM error_logs")
                max_id = cur.fetchval()
                next_id = 1 if max_id is None else max_id + 1
                print(f"目前的ID最大值為: {max_id}，下一個將使用的ID為: {next_id}")
                
                while True:
                    prompt_text = "請輸入有效的 equipment_id"
                    equipment_id = get_input_or_raise(prompt_text).upper()
                    query = "SELECT 1 FROM equipment WHERE equipment_id = ?"
                    cur.execute(query, (equipment_id,))
                    if cur.fetchone():
                        print(f"ID '{equipment_id}' 驗證成功。")
                        break
                    else:
                        print(f"錯誤：在 'equipment' 資料表中找不到 ID '{equipment_id}'，請重新輸入。")

                # 建立數字與異常類型的對照字典
                ANOMALY_MAP = {
                    '1': '轉速太低',
                    '2': '刀具裂痕',
                    '3': '刀具變形'
                }
                print("\n請選擇偵測到的異常類型：")
                for key, value in ANOMALY_MAP.items():
                    print(f"  [{key}] {value}")
                while True:
                    user_choice = get_input_or_raise("請輸入選項數字")

                    if user_choice in ANOMALY_MAP:
                        detected_anomaly_type = ANOMALY_MAP[user_choice]
                        print(f"您的選擇是: [{user_choice}] {detected_anomaly_type}")
                        break
                    else:
                        print(f"錯誤：無效的選項 '{user_choice}'，請重新輸入。")

                if detected_anomaly_type in ["刀具裂痕", "刀具變形"]:
                    while True:
                        deformation_mm_str = get_input_or_raise("請輸入 deformation_mm")
                        try:
                            deformation_mm_val = float(deformation_mm_str)
                            break
                        except ValueError:
                            print("錯誤：請輸入有效的數值")
                    rpm = 30000 
                elif detected_anomaly_type == "轉速太低":
                    deformation_mm_val = 0
                    while True:
                        rpm_input_str = get_input_or_raise("請輸入 rpm")
                        try:
                            rpm = int(rpm_input_str)
                            break
                        except ValueError:
                            print("錯誤：請輸入有效的整數數值")
                else:
                    # 這個 else 理論上不會被執行到，因為我們已經驗證過輸入了，但保留著作為防呆
                    print("異常類型輸入錯誤，程式即將結束")
                    return
                
                notes = get_input_or_raise("請輸入 notes")
                log_date = datetime.date.today()
                event_time = datetime.datetime.now()
                sql = "INSERT INTO error_logs (error_id, log_date, equipment_id, deformation_mm, rpm, event_time, detected_anomaly_type, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                params = (next_id, log_date, equipment_id, deformation_mm_val, rpm, event_time, detected_anomaly_type, notes)
                cur.execute(sql, params)
                conn.commit()
                print(f"\n已成功新增異常事件 error_id 為：{next_id}\n")

            # (elif action == "resolved" 部分不變)
            elif action == "resolved":
                while True:
                    try:
                        error_id_str = get_input_or_raise("請輸入要回復的 error_id")
                        error_id = int(error_id_str)
                        break
                    except ValueError:
                        print("錯誤：請輸入有效的數字 error_id。")

                cur.execute("SELECT resolved_time, event_time FROM error_logs WHERE error_id = ?", (error_id,))
                row = cur.fetchone()
                if not row:
                    print("錯誤：找不到此 error_id")
                elif row.resolved_time is not None:
                    print("提示：該 error_id 已經有回復時間，不可重複填寫")
                else:
                    resolved_time = datetime.datetime.now()
                    event_time = row.event_time
                    if isinstance(event_time, str): event_time = datetime.datetime.fromisoformat(event_time)
                    total_seconds = int((resolved_time - event_time).total_seconds())
                    min_part, sec_part = divmod(total_seconds, 60)
                    cur.execute("UPDATE error_logs SET resolved_time = ?, downtime_min = ?, downtime_sec = ? WHERE error_id = ?", (resolved_time, min_part, sec_part, error_id))
                    conn.commit()
                    print(f"\n已成功更新 Error ID: {error_id}")

            else:
                print("輸入錯誤，請重新輸入 'event' 或 'resolved'")

        except UserCancelledError:
            print("\n使用者已取消操作。")

    except pyodbc.Error as ex:
        print(f"\n資料庫連線或操作發生錯誤: {ex}")
    except Exception as e:
        print(f"發生非預期的錯誤: {e}")
    finally:
        if conn:
            conn.close()
            print("\n資料庫連線已安全關閉")


if __name__ == "__main__":
    main()