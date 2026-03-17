# -*- coding: utf-8 -*-
# ======================== 板块1：导入依赖模块 ========================
# 导入LangChain核心的提示词模板类，用于构建Agent的系统提示
from langchain_core.prompts import ChatPromptTemplate
# 导入LangChain对接OpenAI API的Chat模型类（DeepSeek兼容该接口）
from langchain_openai import ChatOpenAI
# 导入LangChain的工具装饰器，用于定义Agent可调用的工具函数
from langchain_core.tools import tool
# 导入LangChain的消息类型，用于构建对话上下文（本代码未直接使用，但为工具调用基础依赖）
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
# 导入Agent执行器、工具调用型Agent构建函数、ReAct模式Agent构建函数
from langchain.agents import AgentExecutor, create_tool_calling_agent, create_react_agent
# 导入LangChain的hub模块（本代码未直接使用，为扩展预留）
from langchain import hub
# 导入类型注解，用于指定函数参数/返回值的类型，提升代码可读性和类型检查
from typing import List, Union
"""
这段代码基于 LangChain 框架，结合兼容 OpenAI API 格式的 DeepSeek 大模型，实现了一个具备自主工具调用能力的 AI Agent。
核心功能是：让 Agent 能够根据用户的自然语言查询（如查天气、算乘法），自主判断是否需要调用预设的工具函数
（乘法计算、城市天气查询），完成工具调用并整合结果后返回最终响应；同时封装了通用的运行函数，
方便测试不同查询场景下 Agent 的工具调用逻辑。
"""
# ======================== 板块2：DeepSeek API 配置 ========================
# 请替换为你的 DeepSeek API 密钥
API_KEY = "sk-8d633094dd79409fad02d1aa83c6c84c"
# DeepSeek API的基础请求地址（兼容OpenAI API格式）
API_URL = "https://api.deepseek.com/v1"
# 指定要调用的DeepSeek模型名称
MODEL = "deepseek-chat"

# ======================== 板块3：初始化ChatOpenAI实例 ========================
# 虽然我们用的是DeepSeek，但它兼容OpenAI的API格式，所以可以使用ChatOpenAI类
llm = ChatOpenAI(
    model=MODEL,          # 指定使用的模型名称
    api_key=API_KEY,      # 传入DeepSeek API密钥
    base_url=API_URL,     # 指定DeepSeek的API地址，覆盖OpenAI默认地址
    temperature=0.8,      # 模型生成的随机性（0-1，值越高越灵活）
    max_tokens=300        # 模型单次响应的最大令牌数，限制返回内容长度
)

# ======================== 板块4：定义Agent可调用的工具函数 ========================
# 使用@tool装饰器标记该函数为Agent可调用的工具，装饰器会自动处理函数的元数据（如描述）
@tool
def multiply(a: int, b: int) -> int:
    """用于计算两个整数的乘积。"""  # 工具的描述文档，Agent会读取该描述判断是否调用此工具
    print(f"正在执行乘法: {a} * {b}")  # 打印工具执行日志，便于调试
    return a * b  # 返回两个整数的乘积

# 使用@tool装饰器定义第二个工具函数：天气查询
@tool
def search_weather(city: str) -> str:
    """用于查询指定城市的实时天气。"""  # 工具描述，告知Agent该工具的用途
    print(f"正在查询天气: {city}")  # 打印工具执行日志
    # 模拟不同城市的天气返回结果（实际场景可对接真实天气API）
    if "北京" in city:
        return "北京今天是晴天，气温25摄氏度。"
    elif "上海" in city:
        return "上海今天是阴天，有小雨，气温22摄氏度。"
    else:
        return f"抱歉，我没有'{city}'的天气信息。"

# 将工具列表放入一个变量，便于后续传递给Agent
tools = [multiply, search_weather]

# ======================== 板块5：定义通用执行函数 ========================
# 通用的执行函数，用于运行agent并打印结果
def run_agent_and_print(agent_executor, query):
    """一个通用函数，用于运行Agent并打印结果。"""
    # 打印当前查询的提示信息，便于区分不同测试用例
    print(f"--- 运行Agent，查询: {query} ---")
    # 调用Agent执行器的invoke方法，传入用户输入（字典格式，key为input）
    response = agent_executor.invoke({"input": query})
    # 打印Agent响应的提示分隔符
    print(f"\n--- Agent响应: ---")
    # 获取响应中的output字段（Agent的最终回答），若不存在则返回默认提示
    print(response.get("output", "没有找到输出。"))
    # 打印分隔线，美化输出格式
    print("-" * 30 + "\n")

# ======================== 板块6：构建工具调用型Agent ========================
# 步骤1: 自定义一个 Agent 的 Prompt 模板
# 这个 Prompt 告诉 LLM 它的角色，以及如何使用工具。
# 注意 {tools}, {tool_names}, {input} 是必需的占位符。
tool_use_prompt = ChatPromptTemplate.from_messages([
    # 系统提示：定义Agent的角色和工具调用规则
    ("system", "你是一个强大的AI助手，可以访问和使用各种工具来回答问题。请根据用户的问题，决定是否需要调用工具。当需要调用工具时，请使用正确的JSON格式。"),
    # 用户输入占位符：接收用户的查询内容
    ("user", "{input}"),
    # 思考过程占位符：保存Agent的思考过程、工具调用历史（核心，不可省略）
    ("placeholder", "{agent_scratchpad}")
])

# 步骤2: 创建一个 LLM 能够识别和使用的 Agent
# 使用 create_tool_calling_agent 函数，它能让 LLM 自动判断何时以及如何调用工具
tool_calling_agent = create_tool_calling_agent(
    llm,            # 传入初始化好的大模型实例
    tools,          # 传入Agent可调用的工具列表
    tool_use_prompt # 传入自定义的提示词模板
)

# 步骤3: 创建 Agent Executor
# AgentExecutor 负责 Agent 和工具之间的协调（如调用工具、处理工具返回结果、多轮思考）
tool_use_executor = AgentExecutor(
    agent=tool_calling_agent,  # 传入构建好的工具调用型Agent
    tools=tools,               # 传入工具列表
    verbose=True               # 开启 verbose 模式，可以打印详细的执行过程（如思考、工具调用步骤）
)

# ======================== 板块7：测试运行Agent ========================
# 主程序入口：仅当脚本直接运行时执行以下代码（导入时不执行）
if __name__ == "__main__":
    # 测试1：查询上海天气（触发search_weather工具）
    run_agent_and_print(tool_use_executor, "上海今天的天气怎么样？")
    # 测试2：多任务查询（同时触发乘法工具+天气工具）
    run_agent_and_print(tool_use_executor, "30乘以5等于多少？ 上海天气怎么样")