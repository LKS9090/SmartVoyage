# mcp_weather_server.py
# 功能：提供天气数据库查询接口，仅支持SELECT查询，返回JSON结果。鲁棒性：异常捕获，JSON格式化。

import mysql.connector  # 导入MySQL数据库连接器，用于建立和执行数据库连接
import logging  # 导入日志模块，用于记录服务器运行和错误信息
import json  # 导入JSON模块，用于序列化和反序列化数据
from datetime import date, datetime, timedelta  # 从datetime模块导入日期、时间和时间差类，用于处理时间相关数据
from decimal import Decimal  # 导入Decimal类，用于精确小数计算，避免浮点精度问题
from python_a2a.mcp import FastMCP  # 从python_a2a.mcp导入FastMCP类，用于创建MCP工具服务器框架
import uvicorn  # 导入Uvicorn模块，用于运行ASGI服务器，支持FastAPI应用
from python_a2a.mcp import create_fastapi_app  # 从python_a2a.mcp导入create_fastapi_app函数，用于基于MCP创建FastAPI应用
"""
这是一个基于 MCP（Model Context Protocol）的天气查询服务，核心功能：
连接 MySQL 数据库（存储天气数据）
提供 SQL 查询接口
自动处理日期/时间格式化
返回 JSON 格式结果
完善的错误处理和日志记录
"""
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')  # 配置日志基本设置，级别为INFO，格式包括时间、级别和消息
logger = logging.getLogger(__name__)  # 创建名为当前模块的日志记录器，用于后续日志输出

# 自定义JSON编码器
class DateEncoder(json.JSONEncoder):  # 定义自定义JSON编码器类，继承自json.JSONEncoder，用于处理非标准类型序列化
    def default(self, obj):  # 重写default方法，处理序列化时的默认对象转换
        if isinstance(obj, (date, datetime)):  # 检查对象是否为date或datetime类型
            return obj.strftime('%Y-%m-%d %H:%M:%S') if isinstance(obj, datetime) else obj.strftime('%Y-%m-%d')  # 对于datetime返回带时间的字符串，对于date返回日期字符串
        if isinstance(obj, timedelta):  # 检查对象是否为timedelta类型
            return str(obj)  # 将时间差转换为字符串
        if isinstance(obj, Decimal):  # 检查对象是否为Decimal类型
            return float(obj)  # 将Decimal转换为浮点数以兼容JSON
        return super().default(obj)  # 对于其他类型，调用父类默认方法

# 天气服务类
class WeatherService:  # 定义天气服务类，封装数据库操作逻辑
    def __init__(self):  # 初始化方法，建立数据库连接
        # 连接数据库
        self.conn = mysql.connector.connect(  # 创建MySQL连接对象，使用connect函数
            host="192.168.100.128",  # 指定数据库主机为本地
            user="root",  # 指定数据库用户名
            password="123456",  # 指定数据库密码
            database="travel_rag",  # 指定要连接的数据库名称
            port = 3307
        )  # 连接参数结束

    def default_encoder(self, obj):  # 定义默认编码器方法，用于格式化单个对象
        if isinstance(obj, datetime):  # 检查是否为datetime
            return obj.strftime('%Y-%m-%d %H:%M:%S')  # 返回带时间的格式化字符串
        if isinstance(obj, date):  # 检查是否为date
            return obj.strftime('%Y-%m-%d')  # 返回日期格式化字符串
        if isinstance(obj, timedelta):  # 检查是否为timedelta
            return str(obj)  # 转换为字符串
        if isinstance(obj, Decimal):  # 检查是否为Decimal
            return float(obj)  # 转换为浮点数
        return obj  # 返回原对象


    def execute_query(self, sql: str) -> str:  # 定义执行SQL查询方法，输入SQL字符串，返回JSON字符串
        try:  # 开始异常捕获块，确保查询鲁棒性
            cursor = self.conn.cursor(dictionary=True)  # 创建字典游标，用于返回字典格式的结果集
            cursor.execute(sql)  # 执行传入的SQL语句
            results = cursor.fetchall()  # 获取所有查询结果
            cursor.close()  # 关闭游标，释放资源
            # 格式化结果中的日期和数值
            for result in results:  # 遍历每个结果字典
                for key, value in result.items():  # 遍历字典的每个键值对
                    if isinstance(value, (date, datetime, timedelta, Decimal)):  # 检查值是否为特殊类型
                        result[key] = self.default_encoder(value)  # 使用自定义编码器格式化该值
            return json.dumps({"status": "success", "data": results} if results else {"status": "no_data", "message": "未找到天气数据，请确认城市和日期。"}, cls=DateEncoder, ensure_ascii=False)  # 序列化为JSON，如果有结果返回success，否则no_data；使用DateEncoder，非ASCII不转义
        except Exception as e:  # 捕获任何异常
            logger.error(f"天气查询错误: {str(e)}")  # 记录错误日志
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)  # 返回错误JSON响应

    """
    执行 SQL 查询
        ↓
    获取结果 → results = cursor.fetchall()
        ↓
    判断 results 是否为空？
        ↓
        ├─ 有数据 ─→ 构建 {"status": "success", "data": results}
        │
        └─ 无数据 ─→ 构建 {"status": "no_data", "message": "..."}
        ↓
    使用 DateEncoder 进行序列化
        ↓
    设置 ensure_ascii=False（支持中文）
        ↓
    返回 JSON 字符串给客户端
    """

# 创建天气MCP服务器
def create_weather_mcp_server():  # 定义创建天气MCP服务器的主函数
    weather_mcp = FastMCP(  # 创建FastMCP实例
        name="WeatherTools",  # 设置服务器名称
        description="天气查询工具，基于 weather_data 表。",  # 设置服务器描述
        version="1.0.0"  # 设置版本号
    )  # MCP实例创建结束

    service = WeatherService()  # 实例化天气服务对象

    @weather_mcp.tool(  # 使用装饰器注册工具到MCP
        name="query_weather",  # 工具名称
        description="查询天气数据，输入 SQL，如 'SELECT * FROM weather_data WHERE city = \"北京\" AND fx_date = \"2025-07-30\"'"  # 工具描述，包括示例SQL
    )  # 工具注册参数结束
    def query_weather(sql: str) -> str:  # 定义工具函数，输入SQL，返回JSON字符串
        logger.info(f"执行天气查询: {sql}")  # 记录查询SQL的INFO日志
        return service.execute_query(sql)  # 调用服务执行查询并返回结果

    # 打印服务器信息
    logger.info("=== 天气MCP服务器信息 ===")  # 记录服务器信息分隔线
    logger.info(f"名称: {weather_mcp.name}")  # 记录服务器名称
    logger.info(f"描述: {weather_mcp.description}")  # 记录服务器描述
    tools = weather_mcp.get_tools()  # 获取所有注册工具列表
    for tool in tools:  # 遍历每个工具
        logger.info(f"- {tool['name']}: {tool['description']}")  # 记录工具名称和描述

    # 运行服务器
    port = 6001  # 设置服务器端口
    app = create_fastapi_app(weather_mcp)  # 基于MCP创建FastAPI应用
    logger.info(f"启动天气MCP服务器于 http://localhost:{port}")  # 记录启动信息
    uvicorn.run(app, host="0.0.0.0", port=port)  # 启动Uvicorn服务器，绑定所有IP，指定端口
    # host设为0.0.0.0  让非本机的Agent也能访问 支持分布式部署
if __name__ == "__main__":  # 检查是否为直接运行模块
    create_weather_mcp_server()  # 调用创建服务器函数