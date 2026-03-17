# -*- coding: utf-8 -*-
# ======================== 板块1：导入依赖模块 ========================
# 导入LangChain对接OpenAI API的Chat模型类（DeepSeek兼容该接口）
from langchain_openai import ChatOpenAI
# 导入LangChain的工具装饰器，用于定义Agent可调用的工具函数
from langchain_core.tools import tool
# 导入LangChain核心的提示词模板类，用于构建规划器/执行者的Prompt
from langchain_core.prompts import ChatPromptTemplate
# 导入字符串输出解析器，将LLM响应转换为纯字符串（便于处理规划器生成的任务列表）
from langchain_core.output_parsers import StrOutputParser
# 导入Agent执行器、ReAct模式Agent构建函数（执行者核心依赖）
from langchain.agents import AgentExecutor, create_react_agent
# 导入类型注解，用于指定列表类型（提升代码可读性）
from typing import List
"""
这段代码基于 LangChain 框架对接 DeepSeek 大模型，实现了规划模式（Planning Pattern）的 AI Agent，核心架构为「规划器（Planner）+ 执行者（Executor）」：
1.规划器：接收用户的复杂多步骤任务（如 “先算乘法，再查天气”），将其拆解为若干个独立、可执行的子任务列表；
2.执行者：基于 ReAct 模式的 Agent，逐个执行规划器拆分的子任务，自主调用对应的工具（乘法计算 / 天气查询）完成任务；
整体实现了 “复杂任务拆解→子任务逐个执行” 的完整流程，解决了单 Agent 处理多步骤任务时逻辑混乱的问题。

"""
# ======================== 板块2：DeepSeek API 配置 ========================
# --- DeepSeek API 配置 ---
# 请替换为你的 DeepSeek API 密钥
API_KEY = "sk-8d633094dd79409fad02d1aa83c6c84c"
# DeepSeek API的基础请求地址（兼容OpenAI API格式）
API_URL = "https://api.deepseek.com/v1"
# 指定要调用的DeepSeek模型名称
MODEL = "deepseek-chat"

# ======================== 板块3：初始化ChatOpenAI实例 ========================
# --- 步骤1: 初始化 ChatOpenAI ---
# 兼容 OpenAI API 的 DeepSeek LLM
llm = ChatOpenAI(
    model=MODEL,          # 指定使用的模型名称（deepseek-chat）
    api_key=API_KEY,      # 传入DeepSeek API密钥，用于身份验证
    base_url=API_URL,     # 指定DeepSeek的API地址，覆盖OpenAI默认地址
    temperature=0.8,      # 模型生成的随机性（0-1，值越高拆分任务越灵活）
    max_tokens=300        # 模型单次响应的最大令牌数，限制输出长度
)

# ======================== 板块4：定义Agent可调用的工具函数 ========================
# --- 步骤2: 定义我们的工具 ---
# 关键修改：重写 multiply 工具，使其只接受一个字符串参数，并在内部解析。
# 使用@tool装饰器标记该函数为Agent可调用的工具，自动注册工具元数据
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
        # 将输入字符串按逗号分割为两个子串（对应两个整数）
        a_str, b_str = numbers_str.split(',')
        # 去除子串两端空格并转换为整数
        a = int(a_str.strip())
        b = int(b_str.strip())
        # 返回两个整数的乘积
        return a * b
    except ValueError:
        # 捕获参数解析异常，返回友好提示（提升工具鲁棒性）
        return "输入的格式不正确，请确保是两个用逗号分隔的整数，例如：'100,25'"


# 使用@tool装饰器定义天气查询工具
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

# 将工具列表放入一个变量，便于后续传递给执行者Agent
tools = [multiply, search_weather]



# ======================== 板块5：定义规划器和执行者的Prompt模板 ========================
# --- 步骤3: 定义规划器 (Planner) 和执行者 (Executor) 的 Prompt ---

# 3.1 规划器的 Prompt
# 规划器的职责是分析用户任务，并将其分解成一系列简单的、可执行的子任务。
# 构建规划器的Prompt模板，约束模型输出“每行一个子任务”的列表格式
planner_prompt = ChatPromptTemplate.from_template(
    """你是一个任务规划师，你的工作是将用户提出的一个复杂任务分解成一系列清晰、可执行的步骤。
    你的输出应该是一个简单的任务列表，每行一个任务。

    例子:
    用户任务: "请先查上海的天气，然后计算20乘以30。"
    任务列表:
    - 查找上海的天气
    - 计算20乘以30的结果

    用户任务: {user_input}
    任务列表:
    """
)
# 构建规划器的链式调用（Prompt模板 → LLM模型 → 字符串解析器）
# 链式调用实现：输入用户复杂任务 → 模型生成子任务列表 → 解析为纯字符串
planner_chain = planner_prompt | llm | StrOutputParser()

# 3.2 执行者的 Prompt
# 执行者的职责是执行单个任务。在这里，我们使用 ReAct 模式作为执行者，
# 因为它能根据任务描述选择并调用正确的工具。
# 注意：我们使用一个简化版的 ReAct Prompt，因为它只需要处理单个任务。
executor_react_prompt_template = """你是一个专业的工具执行者，可以访问以下工具：

{tools}

请严格按照以下步骤执行任务：
1. 先思考（Thought）：我需要什么信息？
2. 如果需要工具帮助，执行行动（Action）：
   Thought: 我需要思考如何完成任务。
   Action: [工具名称]
   Action Input: [工具的输入参数]
3. 观察工具返回的结果（Observation）
4. 重复上述步骤直到获得所有必要信息
5. 最后给出最终答案：
   Thought: 我现在可以给出最终答案了。
   Final Answer: [最终答案]

重要规则：
- 每次只执行一个 Action，不要在同一轮输出中包含多个 Thought
- 只有在获得所有必要信息后才给出 Final Answer
- 对于 multiply 工具，请使用'数字 1，数字 2'的格式

可用的工具名称有：{tool_names}

请执行以下任务：
{input}
{agent_scratchpad}
"""
# 将字符串模板转换为LangChain的ChatPromptTemplate实例（适配ReAct Agent调用）
executor_prompt = ChatPromptTemplate.from_template(executor_react_prompt_template)

# ======================== 板块6：创建ReAct Agent作为执行者 ========================
# --- 步骤4: 创建 ReAct Agent 作为执行者 ---
# 基于大模型、工具列表、执行者Prompt创建ReAct风格的执行者Agent
executor_agent = create_react_agent(llm, tools, executor_prompt)
# 创建Agent执行器，协调执行者Agent与工具的交互（核心：处理ReAct思考-行动循环）
executor_executor = AgentExecutor(
    agent=executor_agent,  # 传入构建好的ReAct执行者Agent
    tools=tools,           # 传入Agent可调用的工具列表
    verbose=True           # 开启verbose模式，打印详细执行过程（思考、工具调用步骤）
)



# ======================== 板块7：定义规划模式工作流函数 ========================
# --- 步骤5: 定义并运行规划模式的工作流 ---
def execute_planning_pattern(query: str):
    # 打印规划模式启动提示，便于查看流程进度
    print("--- 启动规划模式 ---")

    # 规划器分解任务
    print("\n规划器正在分解任务...")
    # 调用规划器链式调用，传入用户复杂任务，生成子任务列表字符串
    plan = planner_chain.invoke({"user_input": query})
    # 解析子任务列表：按换行分割 → 去除空行 → 去除每个任务的首尾空格
    tasks = [task.strip() for task in plan.split('\n') if task.strip()]
    # 打印拆解后的子任务列表，清晰展示规划结果
    print("规划器生成的任务列表:")
    for i, task in enumerate(tasks):
        print(f"  {i + 1}. {task}")

    # 执行者逐一执行任务
    print("\n执行者正在逐一执行任务...")
    # 遍历规划器拆分的子任务，逐个执行
    for i, task in enumerate(tasks):
        print(f"\n--- 执行任务 {i + 1}: {task} ---")
        # 调用执行者Agent执行单个子任务
        executor_executor.invoke({"input": task})

    # 打印所有任务执行完毕的提示，标记流程结束
    print("\n--- 所有任务执行完毕！---")



# ======================== 板块8：测试运行规划模式 ========================
# --- 步骤6: 运行并测试 ---
# 主程序入口：仅当脚本直接运行时执行以下代码（导入时不执行）
if __name__ == "__main__":
    # 定义测试用的复杂任务：先算乘法，再查上海天气
    test_query = "请先计算 50 乘以 60 的结果，然后告诉我上海的天气怎么样？"
    # 运行规划模式工作流，触发“任务拆解→逐个执行”全流程
    execute_planning_pattern(test_query)