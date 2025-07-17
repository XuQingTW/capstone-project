import pyodbc
import datetime

# ========= MS SQL Server 連線參數 =========
conn = pyodbc.connect(
    r'DRIVER={ODBC Driver 17 for SQL Server};SERVER=YOUR_SERVER;DATABASE=YOUR_DB;UID=YOUR_UID;PWD=YOUR_PWD'
)
cur = conn.cursor()

# ========= 使用者互動主流程 =========
action = input("請輸入 'event'（新增異常）或 'resolved'（填寫回復）: ").strip().lower()

#新增異常
if action == "event":
    equipment_id = input("請輸入 equipment_id：")
    detected_anomaly_type = input("請輸入 detected_anomaly_type（轉速太低 或 刀具裂痕 或 刀具變形）：").strip()

    if detected_anomaly_type in ["刀具裂痕", "刀具變形"]:
        # deformation_mm 不可空且需數值
        while True:
            deformation_mm = input("請輸入 deformation_mm（變形量，單位mm，不可空）：").strip()
            try:
                deformation_mm_val = float(deformation_mm)
                break
            except ValueError:
                print("請輸入有效的數值！")
        rpm = 3000
    elif detected_anomaly_type == "轉速太低":
        deformation_mm_val = 0
        # rpm 不可空且需整數
        while True:
            rpm_input = input("請輸入 rpm（轉速，不可空）：").strip()
            try:
                rpm = int(rpm_input)
                break
            except ValueError:
                print("請輸入有效的整數數值！")
    else:
        print("異常類型輸入錯誤，請重新輸入！")
        cur.close()
        conn.close()
        exit()

    notes = input("請輸入 notes（備註，請先填寫異常的嚴重程度）：")
    log_date = datetime.date.today()
    event_time = datetime.datetime.now()

    # 寫入資料
    sql = """
    INSERT INTO error_logs (
        log_date, equipment_id, deformation_mm, rpm,
        event_time, detected_anomaly_type, notes
    )
    OUTPUT INSERTED.error_id
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        log_date,
        equipment_id,
        deformation_mm_val,
        rpm,
        event_time,
        detected_anomaly_type,
        notes
    )
    new_error_id = cur.execute(sql, params).fetchval()
    conn.commit()
    print("已成功新增異常事件至 error_logs！")
    print(f"本次異常的 error_id 為：{new_error_id}")

#填寫回復
elif action == "resolved":
    error_id = input("請輸入要回復的 error_id：").strip()
    cur.execute("SELECT resolved_time, event_time FROM error_logs WHERE error_id = ?", (error_id,))
    row = cur.fetchone()
    if not row:
        print("找無此錯誤（error_id）！")
    elif row[0] is not None:
        print("該 error_id 已經有回復時間，不可重複填寫！")
    else:
        resolved_time = datetime.datetime.now()
        event_time = row[1]
        if isinstance(event_time, str):  # 若是字串格式要轉換
            event_time = datetime.datetime.fromisoformat(event_time)
        total_seconds = int((resolved_time - event_time).total_seconds())
        min_part = total_seconds // 60
        sec_part = total_seconds % 60

        cur.execute(
            "UPDATE error_logs SET resolved_time = ?, downtime_min = ?, downtime_sec = ? WHERE error_id = ?",
            (resolved_time, min_part, sec_part, error_id)
        )
        conn.commit()
        print(f"已成功填寫回復時間 resolved_time：{resolved_time}")
        print(f"自動計算停機時間：{min_part}分{sec_part}秒")

else:
    print("輸入錯誤，請重新輸入 'event' 或 'resolved'。")

cur.close()
conn.close()
#請新增傳送line通知給使用者，新增異常及回復都需要。訊息請先參考excel內的alert_history