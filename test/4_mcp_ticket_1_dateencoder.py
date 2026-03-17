# mcp_ticket_server.py
# 功能：提供票务数据库查询接口，仅支持SELECT查询，返回JSON结果。鲁棒性：异常捕获，JSON格式化，去掉预订功能。

import mysql.connector
import logging
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from python_a2a.mcp import FastMCP
import uvicorn
from python_a2a.mcp import create_fastapi_app

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 自定义JSON编码器
#这个 DateEncoder 类的核心作用是解决Python特殊数据类型在JSON序列化时的兼容性问题。
# 序列化是指将对象或数据结构转换为可以存储或传输的格式的过程，反之称为反序列化。
#例如时间 和 时间间隔，以及 Decimal 类型的数据。
# 自定义JSON编码器，用于处理不能直接序列化为JSON的特殊数据类型
class DateEncoder(json.JSONEncoder):
    # 重写 default 方法，这是 JSONEncoder 的核心方法，用于处理不能识别的对象
    def default(self, obj):
        # 检查对象是否为 date 或 datetime 类型
        # 例如：obj = datetime(2025, 8, 11, 8, 0, 0)
        if isinstance(obj, (date, datetime)):
            # 如果是 datetime 类型，则格式化为 'YYYY-MM-DD HH:MM:SS' 字符串
            # 示例：datetime(2025, 8, 11, 8, 0, 0) -> '2025-08-11 08:00:00'
            # 否则（是 date 类型），则格式化为 'YYYY-MM-DD' 字符串
            # 示例：date(2025, 8, 11) -> '2025-08-11'
            return obj.strftime('%Y-%m-%d %H:%M:%S') if isinstance(obj, datetime) else obj.strftime('%Y-%m-%d')
        # 检查对象是否为 timedelta 类型（时间间隔）
        # 例如：obj = timedelta(days=1, hours=2)
        if isinstance(obj, timedelta):
            # 将 timedelta 对象转换为字符串
            # 示例：timedelta(days=1, hours=2) -> '1 day, 2:00:00'
            return str(obj)
        # 检查对象是否为 Decimal 类型
        # 例如：obj = Decimal('123.45')
        if isinstance(obj, Decimal):
            # 将 Decimal 类型转换为浮点数（float）
            # 示例：Decimal('123.45') -> 123.45
            return float(obj)
        # 如果对象不是上述任何一种类型，则调用父类（json.JSONEncoder）的 default 方法进行处理
        # 示例：如果 obj 是一个普通的字符串或整数，则交由父类处理
        return super().default(obj)

if __name__ == '__main__':
    encoder = DateEncoder()
    print(encoder.default(datetime(2025, 8, 11, 8, 0)))
    print(encoder.default(date(2025, 8, 11)))
    print(encoder.default(timedelta(days=1)))
    print(encoder.default(Decimal('123.45'))) #Decimal 是一种在金融计算中常用的数据类型，可以提供更高的精度，避免浮点数计算中的误差。

    """
    它定义了一个名为 DateEncoder 的自定义 JSON 编码器。
    这是为了解决在将数据库查询结果（其中可能包含日期、时间、时间间隔或 Decimal 类型的数据）
    转换为标准的 JSON 格式时出现的兼容性问题。
    """