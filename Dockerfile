# 使用官方 Python 3.9 作為基礎映像
FROM python:3.9

# 設定工作目錄
WORKDIR /app

# 複製專案檔案到容器
COPY . .
COPY key.json /app/key.json

# 安裝專案所需的 Python 套件
RUN pip install -r requirements.txt

# 指定容器啟動時執行的指令
CMD ["python", "linebot_connect.py"]