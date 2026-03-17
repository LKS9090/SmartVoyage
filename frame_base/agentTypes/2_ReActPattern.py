# -*- coding: utf-8 -*-
# ======================== 板块1：导入依赖模块 ========================
# 导入LangChain对接OpenAI API的Chat模型类（DeepSeek兼容该接口）
from langchain_openai import ChatOpenAI
# 导入LangChain的工具装饰器，用于定义Agent可调用的工具函数
from langchain_core.tools import tool
# 导入LangChain核心的提示词模板类，用于构建ReAct风格的Agent提示词
from langchain_core.prompts import ChatPromptTemplate
# 导入Agent执行器、ReAct模式Agent构建函数（核心：实现思考-行动循环）
from langchain.agents import AgentExecutor, create_react_agent

# ======================== 板块2：DeepSeek API 配置 ========================
# --- DeepSeek API 配置 ---
# 替换为你的DeepSeek API密钥（对接Cloudflare网关的DeepSeek服务）
API_KEY = "sk-8d633094dd79409fad02d1aa83c6c84c"
# DeepSeek API的基础请求地址（通过Cloudflare网关转发）
API_URL = "https://api.deepseek.com/v1"
# 指定要调用的DeepSeek模型名称
MODEL = "deepseek-chat"

# ======================== 板块3：初始化ChatOpenAI实例 ========================
# --- 步骤1: 初始化 ChatOpenAI ---
# 创建大模型实例，对接DeepSeek API（兼容OpenAI格式）
llm = ChatOpenAI(
    model=MODEL,          # 指定使用的模型名称（deepseek-chat）
    api_key=API_KEY,      # 传入DeepSeek API密钥
    base_url=API_URL,     # 指定自定义的API地址（覆盖OpenAI默认地址）
    temperature=0.8,      # 模型生成的随机性（0-1，值越高越灵活）
    max_tokens=300        # 模型单次响应的最大令牌数，限制返回内容长度
)

# ======================== 板块4：定义Agent可调用的工具函数 ========================
# --- 步骤2: 定义工具 ---
# 使用@tool装饰器标记该函数为Agent可调用的工具，装饰器会自动注册工具元数据
@tool
def multiply(numbers_str: str) -> int:
    """用于计算两个整数的乘积。

    参数:
        numbers_str (str): 包含两个整数的字符串，用逗号分隔，例如："100,25"。

    返回:
        int: 两个整数的乘积。
    """
    # 打印工具执行日志，便于调试（查看当前处理的乘法参数）
    print(f"正在执行乘法: {numbers_str}")
    try:
        # 将输入的字符串按逗号分割为两个子串（对应两个整数）
        a_str, b_str = numbers_str.split(',')
        # 去除子串两端的空格并转换为整数
        a = int(a_str.strip())
        b = int(b_str.strip())
        # 返回两个整数的乘积
        return a * b
    except ValueError:
        # 捕获参数解析异常（如格式错误、非整数输入），返回友好提示
        return "输入的格式不正确，请确保是两个用逗号分隔的整数，例如：'100,25'"



# 使用@tool装饰器定义第二个工具函数：天气查询
@tool
def search_weather(city: str) -> str:
    """用于查询指定城市的实时天气。

    参数:
        city (str): 要查询天气的城市名称。

    返回:
        str: 该城市的天气信息。
    """
    # 打印工具执行日志，便于调试（查看当前查询的城市）
    print(f"正在查询天气: {city}")
    # 模拟不同城市的天气返回结果（实际场景可对接真实天气API）
    if "北京" in city:
        return "北京今天是晴天，气温25摄氏度。"
    elif "上海" in city:
        return "上海今天是阴天，有小雨，气温22摄氏度。"
    else:
        return f"抱歉，我没有'{city}'的天气信息。"

# 将工具列表放入一个变量，便于后续传递给ReAct Agent
tools = [multiply, search_weather]

# ======================== 板块5：自定义ReAct风格的Prompt模板 ========================
# --- 步骤3: 自定义 ReAct 风格的 Prompt ---
# 定义ReAct模式的提示词模板，核心是约束Agent的思考-行动逻辑
react_prompt_template = """你是一个有用的 AI 助手，可以访问以下工具：

{tools}

请根据用户输入一步步推理，并按以下规则操作：
1. 每次输出只能包含一个动作（Action 和 Action Input）或一个最终答案（Final Answer）。
2. 如果用户输入包含多个任务，依次处理每个任务，不要一次性输出所有步骤。
3. 每次行动前，说明你的思考（Thought），并选择合适的工具或直接给出最终答案。
4. 如果需要使用工具，格式必须为：
   Thought: [你的思考]
   Action: [工具名称]
   Action Input: [工具的输入参数，例如对于multiply工具，使用'100,25'格式]
5. 如果可以直接回答或所有任务都完成，格式为：
   Thought: [你的思考]
   Final Answer: [最终答案]

可用的工具名称有: {tool_names}

用户输入: {input}
{agent_scratchpad}
"""

# 将字符串模板转换为LangChain的ChatPromptTemplate实例（适配Agent调用）
react_prompt = ChatPromptTemplate.from_template(react_prompt_template)


# ======================== 板块6：创建ReAct Agent和执行器 ========================
# --- 步骤4: 创建 ReAct 风格的 Agent ---
# 基于大模型、工具列表、ReAct提示词创建ReAct风格的Agent
react_agent = create_react_agent(llm, tools, react_prompt)


# --- 步骤5: 创建 Agent Executor ---
# AgentExecutor 负责协调ReAct Agent的思考-行动循环（核心：执行工具调用、处理循环逻辑）
react_executor = AgentExecutor(
    agent=react_agent,               # 传入构建好的ReAct Agent
    tools=tools,                     # 传入Agent可调用的工具列表
    verbose=True,                    # 开启verbose模式，打印详细执行过程（思考、行动、工具调用步骤）
    handle_parsing_errors=True       # 启用错误处理，当工具调用格式解析失败时自动重试
)



# ======================== 板块7：测试运行ReAct Agent ========================
# --- 步骤6: 运行并测试 Agent ---
# 主程序入口：仅当脚本直接运行时执行以下代码（导入时不执行）
if __name__ == "__main__":
    # 测试用例1: 单任务 - 查询上海天气（触发search_weather工具）
    print("--- 运行Agent，查询: 上海今天的天气怎么样？ ---")
    response_weather = react_executor.invoke({"input": "上海今天的天气怎么样？"})
    print(f"\n--- Agent响应: ---")
    print(response_weather.get("output", "没有找到输出。"))
    print("-" * 30 + "\n")

    # 测试用例2: 单任务 - 数学计算（触发multiply工具）
    print("--- 运行Agent，查询: 100乘以25等于多少？ ---")
    response_math = react_executor.invoke({"input": "100乘以25等于多少？"})
    print(f"\n--- Agent响应: ---")
    print(response_math.get("output", "没有找到输出。"))
    print("-" * 30 + "\n")

    # 测试用例3: 多任务 - 同时查询乘法+天气（Agent会依次处理每个任务）
    print("--- 运行Agent，查询: 100乘以25等于多少？ 上海的天气如何？ ---")
    response_multi = react_executor.invoke({"input": "100乘以25等于多少？ 上海的天气如何？"})
    print(f"\n--- Agent响应: ---")
    print(response_multi.get("output", "没有找到输出。"))
    print("-" * 30 + "\n")