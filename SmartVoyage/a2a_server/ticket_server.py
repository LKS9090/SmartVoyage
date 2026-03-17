#!/usr/bin/env_log.log python  # Shebang行，指定Python解释器（可能为自定义路径）
"""
Ticket Query A2A Server with LangChain SQL Generation
优化：处理带代码块的LLM输出，正确解析type和SQL；返回用户友好文本结果（参考weather_server.py逻辑）。
"""  # 模块文档字符串，描述服务器功能和优化点

import json  # 导入JSON模块，用于解析和生成JSON数据
import asyncio  # 导入asyncio模块，用于异步编程和事件循环管理
import re  # 导入re模块，用于正则表达式处理（虽未直接使用，但导入以备）
from python_a2a import A2AServer, run_server, AgentCard, AgentSkill, TaskStatus, TaskState  # 从python_a2a导入A2A服务器核心类和函数，用于构建代理服务器
from python_a2a.mcp import MCPClient  # 从python_a2a.mcp导入MCPClient，用于调用MCP工具服务
from langchain_openai import ChatOpenAI  # 从langchain_openai导入ChatOpenAI，用于创建OpenAI兼容的聊天模型
from langchain_core.prompts import ChatPromptTemplate  # 从langchain_core.prompts导入ChatPromptTemplate，用于构建提示模板
import colorlog  # 导入colorlog模块，用于彩色日志输出
import logging  # 导入logging模块，作为colorlog的基础日志系统
from SmartVoyage.config import Config  # 从自定义模块导入Config类，用于加载配置参数如API密钥
from datetime import datetime, timedelta  # 从datetime导入datetime和timedelta，用于日期时间计算
import pytz  # 导入pytz模块，用于时区处理

# 设置彩色日志
handler = colorlog.StreamHandler()  # 创建流处理器，用于将日志输出到标准输出
handler.setFormatter(colorlog.ColoredFormatter(  # 为处理器设置彩色格式化器
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',  # 指定日志格式：颜色、时间、级别、消息
    log_colors={'INFO': 'green', 'ERROR': 'red'}  # 定义日志级别的颜色映射：INFO绿色，ERROR红色
))  # 格式化器设置结束
logger = colorlog.getLogger()  # 获取根日志记录器
logger.addHandler(handler)  # 添加处理器到日志记录器
logger.setLevel(colorlog.INFO)  # 设置日志级别为INFO，仅记录INFO及以上级别

def initialize_llm():  # 定义初始化LLM的函数
    """初始化 LLM"""  # 函数文档字符串
    conf = Config()  # 实例化Config对象，加载配置
    try:  # 开始异常捕获块
        return ChatOpenAI(  # 创建并返回ChatOpenAI模型实例
            model=conf.model_name,  # 使用配置中的模型名称
            api_key=conf.api_key,  # 使用配置中的API密钥
            base_url=conf.api_url,  # 使用配置中的API基础URL
            temperature=0.7,  # 设置温度为0.7，允许轻微变异
            streaming=True,  # 启用流式响应
        )  # LLM创建结束
    except Exception as e:  # 捕获异常
        logger.error(f"LLM 初始化失败: {str(e)}")  # 记录错误日志
        raise  # 重新抛出异常

def main():  # 定义主函数，包含服务器初始化和运行逻辑
    # 定义数据库 schema# 定义票务表SQL schema字符串，用于Prompt上下文
    database_schema_string = """  
    CREATE TABLE IF NOT EXISTS train_tickets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        departure_city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
        arrival_city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
        departure_time DATETIME NOT NULL,
        arrival_time DATETIME NOT NULL,
        train_number VARCHAR(20) NOT NULL,
        seat_type VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
        total_seats INT NOT NULL,
        remaining_seats INT NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_train (departure_time, train_number)
    );

    CREATE TABLE IF NOT EXISTS flight_tickets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        departure_city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
        arrival_city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
        departure_time DATETIME NOT NULL,
        arrival_time DATETIME NOT NULL,
        flight_number VARCHAR(20) NOT NULL,
        cabin_type VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
        total_seats INT NOT NULL,
        remaining_seats INT NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_flight (departure_time, flight_number)
    );

    CREATE TABLE IF NOT EXISTS concert_tickets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        artist VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
        city VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
        venue VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
        start_time DATETIME NOT NULL,
        end_time DATETIME NOT NULL,
        ticket_type VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
        total_seats INT NOT NULL,
        remaining_seats INT NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_concert (start_time, artist, ticket_type)
    );
    """  # schema字符串结束

    # 优化 SQL 提示模板：添加缺失字段到SELECT（如train_number, flight_number, artist）
    sql_prompt = ChatPromptTemplate.from_template(  # 从模板创建ChatPromptTemplate，用于SQL生成
        """
系统提示：你是一个专业的票务SQL生成器，根据对话历史：
1. 分类查询类型（train: 火车/高铁, flight: 机票, concert: 演唱会），输出：{{"type": "train/flight/concert"}}
2. 根据分类，生成对应表的 SELECT 语句，仅查询指定字段：
   - train_tickets: id, departure_city, arrival_city, departure_time, arrival_time, train_number, seat_type, price, remaining_seats
   - flight_tickets: id, departure_city, arrival_city, departure_time, arrival_time, flight_number, cabin_type, price, remaining_seats
   - concert_tickets: id, artist, city, venue, start_time, end_time, ticket_type, price, remaining_seats
3. 如果无法分类或缺少必要信息，输出：{{"status": "input_required", "message": "请提供票务类型（如火车票、机票、演唱会）和必要信息（如城市、日期）。"}} 
4. 无结果不编造，输出纯 SQL。
5. 不要包含 ```json 或 ```sql

schema：
{schema}

示例：
- 对话: user: 火车票 北京 上海 2025-07-31 硬卧
  输出: 
  {{"type": "train"}}
  SELECT id, departure_city, arrival_city, departure_time, arrival_time, train_number, seat_type, price, remaining_seats FROM train_tickets WHERE departure_city = '北京' AND arrival_city = '上海' AND DATE(departure_time) = '2025-07-31' AND seat_type = '硬卧'
- 对话: user: 机票 上海 广州 2025-09-11 头等舱
  输出: 
  {{"type": "flight"}}
  SELECT id, departure_city, arrival_city, departure_time, arrival_time, flight_number, cabin_type, price, remaining_seats FROM flight_tickets WHERE departure_city = '上海' AND arrival_city = '广州' AND DATE(departure_time) = '2025-09-11' AND cabin_type = '头等舱'
- 对话: user: 演唱会 北京 刀郎 2025-08-23 看台
  输出: 
  {{"type": "concert"}}
  SELECT id, artist, city, venue, start_time, end_time, ticket_type, price, remaining_seats FROM concert_tickets WHERE city = '北京' AND artist = '刀郎' AND DATE(start_time) = '2025-08-23' AND ticket_type = '看台'
- 对话: user: 火车票
  输出: 
  {{"type": "train"}}
  SELECT id, departure_city, arrival_city, departure_time, arrival_time, train_number, seat_type, price, remaining_seats FROM train_tickets WHERE DATE(departure_time) = '2025-07-31' ORDER BY price ASC LIMIT 5
- 对话: user: 你好
  输出: {{"status": "input_required", "message": "请提供票务类型（如火车票、机票、演唱会）和必要信息（如城市、日期）。"}} 

对话历史: {conversation}
当前日期: {current_date} (Asia/Shanghai)
        """  # Prompt模板字符串结束，包含系统提示、schema占位符、示例
    )  # sql_prompt创建结束

    # Agent 卡片定义
    agent_card = AgentCard(  # 创建AgentCard实例，定义代理元数据
        name="Ticket Query Assistant",  # 设置代理名称
        description="基于 LangChain 提供票务查询服务的助手",  # 设置代理描述
        url="http://localhost:5006",  # 设置代理URL
        version="1.0.4",  # 设置版本号
        capabilities={"streaming": True, "memory": True},  # 设置能力：支持流式和内存
        skills=[  # 定义技能列表
            AgentSkill(  # 创建第一个AgentSkill实例
                name="execute ticket query",  # 技能名称
                description="根据客户端提供的输入执行票务查询，返回数据库结果，支持自然语言输入",  # 技能描述
                examples=["火车票 北京 上海 2025-07-31 硬卧", "机票 北京 上海 2025-07-31 经济舱", "演唱会 北京 刀郎 2025-08-23 看台"]  # 技能示例
            )  # 技能定义结束
        ]  # 技能列表结束
    )  # agent_card创建结束

    # 票务查询服务器类
    class TicketQueryServer(A2AServer):  # 定义票务查询服务器类，继承自A2AServer
        def __init__(self):  # 初始化方法
            super().__init__(agent_card=agent_card)  # 调用父类初始化，传入代理卡片
            self.llm = initialize_llm()  # 初始化并保存LLM实例
            self.sql_prompt = sql_prompt  # 保存Prompt模板
            self.schema = database_schema_string  # 保存数据库schema

        def generate_sql_query(self, conversation: str) -> dict:  # 定义生成SQL查询方法，输入对话历史，返回字典
            """根据对话历史生成 SQL 或追问 JSON"""  # 方法文档字符串
            try:  # 开始异常捕获块
                current_date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')  # 获取当前日期（Asia/Shanghai时区），格式化为字符串
                chain = self.sql_prompt | self.llm  # 创建LangChain链：Prompt + LLM
                output = chain.invoke({"schema": self.schema, "conversation": conversation, "current_date": current_date}).content.strip()  # 调用链生成输出，传入schema，剥离空白
                logger.info(f"原始 LLM 输出: {output}")  # 记录原始LLM输出日志

                # 解析 LLM 输出，处理可能的代码块标记
                lines = output.split('\n')  # 将输出按行拆分
                type_line = lines[0].strip()  # 获取第一行作为类型行，剥离空白
                if type_line.startswith('```json'):  # 检查是否以JSON代码块开头
                    type_line = lines[1].strip()  # 取下一行为类型行
                    sql_lines = lines[3:-1] if lines[-1].strip() == '```' else lines[3:]  # 提取SQL行，跳过代码块标记
                else:  # 非代码块情况
                    sql_lines = lines[1:] if len(lines) > 1 else []  # 取剩余行为SQL行

                # 提取 type 和 SQL
                if type_line.startswith('{"type":'):  # 检查类型行是否为type JSON
                    query_type = json.loads(type_line)["type"]  # 解析并提取类型
                    sql_query = ' '.join([line.strip() for line in sql_lines if line.strip() and not line.startswith('```')])  # 连接SQL行，过滤空行和代码块
                    logger.info(f"分类类型: {query_type}, 生成的 SQL: {sql_query}")  # 记录类型和SQL日志
                    return {"status": "sql", "type": query_type, "sql": sql_query}  # 返回SQL状态字典，包括类型
                elif type_line.startswith('{"status": "input_required"'):  # 检查是否为追问JSON
                    return json.loads(type_line)  # 解析并返回JSON
                else:  # 无效格式
                    logger.error(f"无效的 LLM 输出格式: {output}")  # 记录错误日志
                    return {"status": "input_required", "message": "无法解析查询类型或SQL，请提供更明确的信息。"}  # 返回默认追问
            except Exception as e:  # 捕获异常
                logger.error(f"SQL 生成失败: {str(e)}")  # 记录错误日志
                return {"status": "input_required", "message": "查询无效，请提供票务相关信息。"}  # 返回追问JSON

        def handle_task(self, task):  # 定义处理任务方法，输入任务对象
            """处理任务：提取输入，生成 SQL，调用 MCP，返回用户友好文本结果（参考weather_server.py逻辑）"""  # 方法文档字符串
            message_data = task.message or {}  # 获取任务消息，默认空字典
            content = message_data.get("content", {})  # 从消息中获取内容
            conversation = content.get("text", "") if isinstance(content, dict) else ""  # 提取文本对话历史
            logger.info(f"对话历史: {conversation}")  # 记录对话历史日志

            try:  # 开始异常捕获块
                gen_result = self.generate_sql_query(conversation)  # 生成SQL或追问结果
                if gen_result["status"] == "input_required":  # 检查是否需要追问
                    task.status = TaskStatus(  # 设置任务状态
                        state=TaskState.INPUT_REQUIRED,  # 状态为输入所需
                        message={"role": "agent", "content": {"text": gen_result["message"]}}  # 添加追问消息
                    )  # TaskStatus设置结束
                    return task  # 返回任务

                sql_query = gen_result["sql"]  # 提取SQL查询
                query_type = gen_result["type"]  # 提取查询类型
                logger.info(f"执行 SQL 查询: {sql_query} (类型: {query_type})")  # 记录SQL和类型日志

                # 调用 MCP，线程安全异步执行
                client = MCPClient("http://localhost:6002")  # 创建MCP客户端，连接票务MCP服务器
                loop = asyncio.get_event_loop_policy().new_event_loop()  # 创建新事件循环，确保线程安全
                try:  # 开始循环管理块
                    asyncio.set_event_loop(loop)  # 设置当前事件循环
                    ticket_result = loop.run_until_complete(client.call_tool("query_tickets", sql=sql_query))  # 异步调用MCP工具，传入SQL
                finally:  # 确保循环关闭
                    loop.close()  # 关闭事件循环

                response = json.loads(ticket_result) if isinstance(ticket_result, str) else ticket_result  # 解析MCP响应为字典
                logger.info(f"MCP 返回: {response}")  # 记录MCP响应日志

                if response.get("status") == "no_data":  # 检查响应状态
                    response_text = f"{response['message']} 如果需要其他日期，请补充。"  # 生成无数据提示文本
                else:  # 有数据情况
                    data = response.get("data", [])  # 提取数据列表
                    response_text = ""  # 初始化响应文本
                    for d in data:  # 遍历每个数据项
                        if query_type == "train":  # 火车票类型
                            response_text += f"{d['departure_city']} 到 {d['arrival_city']} {d['departure_time']}: 车次 {d['train_number']}，{d['seat_type']}，票价 {d['price']}元，剩余 {d['remaining_seats']} 张\n"  # 格式化火车票文本
                        elif query_type == "flight":  # 机票类型
                            response_text += f"{d['departure_city']} 到 {d['arrival_city']} {d['departure_time']}: 航班 {d['flight_number']}，{d['cabin_type']}，票价 {d['price']}元，剩余 {d['remaining_seats']} 张\n"  # 格式化机票文本
                        elif query_type == "concert":  # 演唱会类型
                            response_text += f"{d['city']} {d['start_time']}: {d['artist']} 演唱会，{d['ticket_type']}，场地 {d['venue']}，票价 {d['price']}元，剩余 {d['remaining_seats']} 张\n"  # 格式化演唱会文本

                    if not response_text:  # 检查文本是否为空
                        response_text = "无结果。如果需要其他日期，请补充。"  # 设置无结果提示

                task.artifacts = [{"parts": [{"type": "text", "text": response_text.strip()}]}]  # 设置任务产物为剥离空白的文本部分
                task.status = TaskStatus(state=TaskState.COMPLETED)  # 设置任务状态为完成
            except Exception as e:  # 捕获异常
                logger.error(f"查询失败: {str(e)}")  # 记录错误日志
                task.artifacts = [{"parts": [{"type": "text", "text": f"查询失败: {str(e)} 请重试或提供更多细节。"}]}]  # 设置错误产物文本
                task.status = TaskStatus(state=TaskState.COMPLETED)  # 设置任务状态为完成

            return task  # 返回处理后的任务

    # 创建并运行服务器
    ticket_server = TicketQueryServer()  # 实例化票务查询服务器

    print("\n=== 服务器信息 ===")  # 打印服务器信息分隔线
    print(f"名称: {ticket_server.agent_card.name}")  # 打印代理名称
    print(f"描述: {ticket_server.agent_card.description}")  # 打印代理描述
    print("\n技能:")  # 打印技能标题
    for skill in ticket_server.agent_card.skills:  # 遍历技能列表
        print(f"- {skill.name}: {skill.description}")  # 打印每个技能的名称和描述

    run_server(ticket_server, host="0.0.0.0", port=5006)  # 运行A2A服务器，绑定所有IP，端口5006

if __name__ == "__main__":  # 检查是否为直接运行模块
    import sys  # 导入sys模块，用于系统退出
    try:  # 开始异常捕获块
        main()  # 调用主函数
        sys.exit(0)  # 正常退出
    except KeyboardInterrupt:  # 捕获键盘中断
        print("\n✅ 程序被用户中断")  # 打印中断消息
        sys.exit(0)  # 正常退出