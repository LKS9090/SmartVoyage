import schedule
import time
from datetime import datetime, timedelta
import pytz


# 设置时区为 PDT (Pacific Daylight Time)
PDT = pytz.timezone('America/Los_Angeles')
TZ = pytz.timezone('Asia/Shanghai')  # 使用上海时区
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
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "travel_rag",
    "charset": "utf8mb4"
}
def connect_db():
    return mysql.connector.connect(**db_config)

#数据爬取与解析
def fetch_weather_data(city, location):
    headers = {
        "X-QW-Api-Key": API_KEY,
        "Accept-Encoding": "gzip"
    }
    url = f"{BASE_URL}?location={location}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        if response.headers.get('Content-Encoding') == 'gzip':
            data = gzip.decompress(response.content).decode('utf-8')
        else:
            data = response.text
        return json.loads(data)
    except requests.RequestException as e:
        print(f"请求 {city} 天气数据失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"{city} JSON 解析错误: {e}, 响应内容: {response.text[:500]}...")
        return None
    except gzip.BadGzipFile:
        print(f"{city} 数据未正确解压，尝试直接解析: {response.text[:500]}...")
        return json.loads(response.text) if response.text else None
def get_latest_update_time(cursor, city):
    cursor.execute("SELECT MAX(update_time) FROM weather_data WHERE city = %s", (city,))
    result = cursor.fetchone()
    return result[0] if result[0] else None


def should_update_data(latest_time, force_update=False):
    if force_update:
        return True
    if latest_time is None:
        return True

    # 时区问题：确保 latest_time 有时区信息
    if latest_time and latest_time.tzinfo is None:
        latest_time = latest_time.replace(tzinfo=TZ)

    current_time = datetime.now(TZ)
    return (current_time - latest_time) > timedelta(days=1)

def store_weather_data(conn, cursor, city, data):
    if not data or data.get("code") != "200":
        print(f"{city} 数据无效，跳过存储。")
        return

    daily_data = data.get("daily", [])
    update_time = datetime.fromisoformat(data.get("updateTime").replace("+08:00", "+08:00")).replace(tzinfo=TZ)

    for day in daily_data:
        fx_date = datetime.strptime(day["fxDate"], "%Y-%m-%d").date()
        values = (
            city, fx_date,
            day.get("sunrise"), day.get("sunset"),
            day.get("moonrise"), day.get("moonset"),
            day.get("moonPhase"), day.get("moonPhaseIcon"),
            day.get("tempMax"), day.get("tempMin"),
            day.get("iconDay"), day.get("textDay"),
            day.get("iconNight"), day.get("textNight"),
            day.get("wind360Day"), day.get("windDirDay"), day.get("windScaleDay"), day.get("windSpeedDay"),
            day.get("wind360Night"), day.get("windDirNight"), day.get("windScaleNight"), day.get("windSpeedNight"),
            day.get("precip"), day.get("uvIndex"),
            day.get("humidity"), day.get("pressure"),
            day.get("vis"), day.get("cloud"),
            update_time
        )
        insert_query = """
        INSERT INTO weather_data (
            city, fx_date, sunrise, sunset, moonrise, moonset, moon_phase, moon_phase_icon,
            temp_max, temp_min, icon_day, text_day, icon_night, text_night,
            wind360_day, wind_dir_day, wind_scale_day, wind_speed_day,
            wind360_night, wind_dir_night, wind_scale_night, wind_speed_night,
            precip, uv_index, humidity, pressure, vis, cloud, update_time
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            sunrise = VALUES(sunrise), sunset = VALUES(sunset), moonrise = VALUES(moonrise),
            moonset = VALUES(moonset), moon_phase = VALUES(moon_phase), moon_phase_icon = VALUES(moon_phase_icon),
            temp_max = VALUES(temp_max), temp_min = VALUES(temp_min), icon_day = VALUES(icon_day),
            text_day = VALUES(text_day), icon_night = VALUES(icon_night), text_night = VALUES(text_night),
            wind360_day = VALUES(wind360_day), wind_dir_day = VALUES(wind_dir_day), wind_scale_day = VALUES(wind_scale_day),
            wind_speed_day = VALUES(wind_speed_day), wind360_night = VALUES(wind360_night),
            wind_dir_night = VALUES(wind_dir_night), wind_scale_night = VALUES(wind_scale_night),
            wind_speed_night = VALUES(wind_speed_night), precip = VALUES(precip), uv_index = VALUES(uv_index),
            humidity = VALUES(humidity), pressure = VALUES(pressure), vis = VALUES(vis),
            cloud = VALUES(cloud), update_time = VALUES(update_time)
        """
        try:
            cursor.execute(insert_query, values)
            print(f"{city} {fx_date} 数据写入/更新成功: {day.get('textDay')}, 影响行数: {cursor.rowcount}")
        except mysql.connector.Error as e:
            print(f"{city} {fx_date} 数据库错误: {e}")

    conn.commit()
    print(f"{city} 事务提交完成。")

def update_weather(force_update=False):
    print("开始更新天气数据...")
    conn = connect_db()
    cursor = conn.cursor()

    for city, location in city_codes.items():
        latest_time = get_latest_update_time(cursor, city)
        #判断是否需要更新
        if should_update_data(latest_time, force_update):
            print(f"开始更新 {city} 天气数据...")
            #爬取数据函数
            data = fetch_weather_data(city, location)
            if data:
                #存储数据函数
                store_weather_data(conn, cursor, city, data)
        else:
            print(f"{city} 数据已为最新，无需更新。最新更新时间: {latest_time}")

    cursor.close()
    conn.close()


def setup_scheduler():
    # 每天凌晨 1:00 北京时间 (PDT 4:00)
    schedule.every().day.at("04:00").do(update_weather)
    while True:
        schedule.run_pending()
        time.sleep(10)


def test_setup_scheduler():
    # 获取当前 PDT 时间 - PDT 指的是太平洋夏令时间（Pacific Daylight Time）
    now = datetime.now(TZ)  # 使用预设的时区TZ获取当前时间
    print(f"[测试日志] 当前时间: {now}")  # 打印当前时间用于调试和记录
    print(f"[测试日志] 设置每10秒触发一次 update_weather")  # 提示用户定时任务的配置信息

    # 使用 every(10).seconds 来设置每10秒执行一次
    schedule.every(10).seconds.do(update_weather)  # 配置schedule每10秒执行一次update_weather函数

    # 运行 30 秒以观察任务触发
    end_time = now + timedelta(seconds=30)  # 计算测试结束时间（当前时间+30秒）
    trigger_count = 0  # 初始化触发次数计数器
    last_trigger_time = None  # 记录上一次触发时间，初始为None

    while datetime.now(TZ) < end_time:  # 循环执行直到当前时间超过结束时间
        schedule.run_pending()  # 检查并执行所有到期的定时任务
        current_time = datetime.now(TZ)  # 获取当前时间用于比较和记录

        # 更好的触发检测方式
        idle_sec = schedule.idle_seconds()  # 获取距离下次任务执行的剩余秒数
        print(f"[测试日志] 当前时间: {current_time}, 下次执行还剩: {idle_sec}秒")  # 打印当前状态信息

        # 如果 idle_seconds 从正数变为0或负数，说明任务刚执行完
        if idle_sec is not None and idle_sec <= 0:  # 检查任务是否刚执行完毕（剩余时间<=0）
            if last_trigger_time is None or (current_time - last_trigger_time).total_seconds() >= 9:  # 确保不是重复计数（间隔至少9秒）
                print(f"[测试日志] ⚡ 任务已触发! 触发时间: {current_time}")  # 打印任务触发信息
                trigger_count += 1  # 增加触发次数计数
                last_trigger_time = current_time  # 更新最后一次触发时间

        time.sleep(1)  # 暂停1秒，避免CPU过度占用，控制循环频率

    print(f"[测试结果] 总共触发次数: {trigger_count}")  # 测试结束后输出总触发次数统计


if __name__ == "__main__":
    print("开始验证 setup_scheduler...")
    #schedule 是一个 Python 定时任务调度库
    test_setup_scheduler()