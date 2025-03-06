# 使用官方 Python 3.11 作為基礎映像與 CI/CD 一致
FROM python:3.11

# 設定工作目錄
WORKDIR /app

# 複製專案檔案到容器
COPY . .

# 安裝專案所需的 Python 套件
RUN pip install -r requirements.txt

# 指定容器啟動時執行的指令 - 修正執行路徑
CMD ["python", "-m", "src.linebot_connect"]

# 設定 `key.json` 作為環境變數
ENV KEY_JSON_PATH=/app/key.json
ENV PYTHONPATH=/app