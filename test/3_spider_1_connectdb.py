import requests
import mysql.connector
from datetime import datetime, timedelta
import schedule
import time
import json
import gzip
import pytz

# 配置
API_KEY = "5ef0a47e161a4ea997227322317eae83"
city_codes = {
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280101",
    "深圳": "101280601"
}
BASE_URL = "https://m7487r6ych.re.qweatherapi.com/v7/weather/30d"
TZ = pytz.timezone('Asia/Shanghai')  # 使用上海时区

# MySQL 配置
db_config = {
    "host": "192.168.100.128",
    "user": "root",
    "password": "123456",
    "database": "travel_rag",
    "charset": "utf8mb4",
    "port": 3307  # 添加端口配置
}

def connect_db():
    return mysql.connector.connect(**db_config)

if __name__ == '__main__':
    conn = connect_db()
    print(conn.is_connected())
    print("数据库连接成功！")
    conn.close()