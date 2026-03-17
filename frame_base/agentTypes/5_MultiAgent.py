# -*- coding: utf-8 -*-
# ======================== 板块1：导入依赖模块 ========================
# 导入LangChain核心的Prompt相关类：
# ChatPromptTemplate（基础Prompt模板）、MessagesPlaceholder（消息占位符，用于Agent思考过程）
# SystemMessagePromptTemplate（系统消息模板）、HumanMessagePromptTemplate（用户消息模板）
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, \
    HumanMessagePromptTemplate  # 导入所有必需的 Prompt 类
# 导入LangChain对接OpenAI API的Chat模型类（DeepSeek兼容该接口）
from langchain_openai import ChatOpenAI
# 导入LangChain的工具装饰器，用于定义Agent可调用的工具函数
from langchain_core.tools import tool
# 导入Agent执行器、工具调用型Agent构建函数（核心：创建Tool Calling Agent）
from langchain.agents import AgentExecutor, create_tool_calling_agent
# 导入字符串输出解析器，将LLM响应转换为纯字符串（便于结果汇总）
from langchain_core.output_parsers import StrOutputParser
"""
这段代码基于 LangChain 框架对接 DeepSeek 大模型，实现了多智能体（Multi-agent）协作模式：
1.拆分出两个专项 Agent——「计算专家」和「信息专家」，分别负责数学计算（乘法 / 加法）和信息查询（天气 / 日期）；
2.每个 Agent 绑定专属工具集，通过 Tool Calling 模式自主调用对应工具完成子任务；
3.设计协作工作流，先将复杂跨领域任务分配给对应 Agent 执行，再通过大模型汇总所有子任务结果，生成连贯的最终回答；
整体实现了 “专项分工→独立执行→结果汇总” 的多 Agent 协作逻辑，解决了单 Agent 处理跨领域复杂任务时专业性不足、效率低的问题。
"""


# ======================== 板块2：配置与初始化 ========================
# --- 步骤1: 配置与初始化 ---
# 1.1 DeepSeek API 配置
API_KEY = "sk-8d633094dd79409fad02d1aa83c6c84c"  # 你的 DeepSeek API 密钥（用于API身份验证）
API_URL = "https://api.deepseek.com/v1"  # API 基础 URL（DeepSeek兼容OpenAI API格式）
MODEL = "deepseek-chat"  # 使用的 LLM 模型名称（DeepSeek对话模型）

# 1.2 初始化 LLM
# 创建大模型实例，对接DeepSeek API（因兼容OpenAI格式，直接用ChatOpenAI类）
llm = ChatOpenAI(
    model=MODEL,          # 指定使用的模型名称（deepseek-chat）
    api_key=API_KEY,      # 传入DeepSeek API密钥
    base_url=API_URL,     # 指定DeepSeek的API地址，覆盖OpenAI默认地址
    temperature=0.8,      # 控制模型输出的随机性（0-1，值越高回答越灵活）
    max_tokens=300        # 限制模型生成的最长 token 数量（避免输出过长）
)

# ======================== 板块3：定义工具函数 ========================
# --- 步骤2: 定义工具 ---
# 2.1 计算工具
# 使用@tool装饰器标记该函数为Agent可调用的工具，装饰器会自动注册工具元数据（如参数、描述）
@tool
def multiply(a: int, b: int) -> int:
    """用于计算两个整数的乘积。

    参数:
        a (int): 第一个整数。
        b (int): 第二个整数。
    """
    # 打印工具执行日志，标注“计算专家”身份，便于调试和跟踪执行过程
    print(f"\n[计算专家] -> 正在执行乘法: {a} * {b}")
    # 返回两个整数的乘积（核心功能）
    return a * b

# 使用@tool装饰器定义加法工具（计算专家专属）
@tool
def add(a: int, b: int) -> int:
    """用于计算两个整数的和。

    参数:
        a (int): 第一个整数。
        b (int): 第二个整数。
    """
    # 打印工具执行日志，标注“计算专家”身份
    print(f"\n[计算专家] -> 正在执行加法: {a} + {b}")
    # 返回两个整数的和
    return a + b

# 2.2 信息查询工具
# 使用@tool装饰器定义天气查询工具（信息专家专属）
@tool
def search_weather(city: str) -> str:
    """用于查询指定城市的实时天气。

    参数:
        city (str): 要查询天气的城市名称。
    """
    # 打印工具执行日志，标注“信息专家”身份
    print(f"\n[信息专家] -> 正在查询天气: {city}")
    # 模拟不同城市的天气返回结果（实际场景可对接真实天气API）
    if "北京" in city:
        return "北京今天是晴天，气温25摄氏度。"
    elif "上海" in city:
        return "上海今天是阴天，有小雨，气温22摄氏度。"
    else:
        return f"抱歉，我没有'{city}'的天气信息。"

# 使用@tool装饰器定义日期获取工具（信息专家专属）
@tool
def get_current_date() -> str:
    """用于获取当前日期。"""
    # 打印工具执行日志，标注“信息专家”身份
    print("\n[信息专家] -> 正在获取当前日期...")
    # 局部导入datetime模块（减少脚本初始化时的资源开销）
    import datetime
    # 获取当前日期并格式化为“YYYY年MM月DD日”的字符串返回
    return datetime.date.today().strftime("%Y年%m月%d日")


# ======================== 板块4：创建独立的专项Agent ========================
# --- 步骤3: 创建两个独立的 Agent ---
# 3.1 创建“计算专家” Agent
# 定义计算专家的专属工具列表（仅包含乘法、加法工具，保证专业性）
math_tools = [multiply, add]
# 创建完整的 Tool Calling Prompt（计算专家专属）
# 这包括一个系统消息，一个用户消息占位符，以及一个 Agent 中间思考过程的占位符。
math_prompt = ChatPromptTemplate.from_messages([
    # 系统消息：定义计算专家的角色定位（专注数学计算，排除无关干扰）
    SystemMessagePromptTemplate.from_template("你是一个强大的数学计算专家，可以访问和使用各种数学工具。"),
    # 用户消息占位符：接收计算相关的子任务输入（如“计算25*4”）
    HumanMessagePromptTemplate.from_template("{input}"),
    # Agent思考过程占位符：保存工具调用历史、中间思考（Tool Calling模式必需）
    MessagesPlaceholder(variable_name="agent_scratchpad")
])
# 创建计算专家Agent（基于Tool Calling模式，绑定专属工具和Prompt）
math_agent = create_tool_calling_agent(llm, math_tools, math_prompt)
# 创建计算专家的Agent执行器（协调Agent与工具的交互、处理工具调用循环）
math_executor = AgentExecutor(
    agent=math_agent,     # 传入构建好的计算专家Agent
    tools=math_tools,     # 传入计算专属工具列表
    verbose=True          # 开启verbose模式，打印详细执行过程（思考、工具调用步骤）
)

# 3.2 创建“信息专家” Agent
# 定义信息专家的专属工具列表（仅包含天气查询、日期获取工具）
info_tools = [search_weather, get_current_date]
# 手动创建完整的 Tool Calling Prompt（信息专家专属）
info_prompt = ChatPromptTemplate.from_messages([
    # 系统消息：定义信息专家的角色定位（专注信息查询）
    SystemMessagePromptTemplate.from_template("你是一个强大的信息查询专家，可以访问和使用各种查询工具。"),
    # 用户消息占位符：接收信息查询相关的子任务输入（如“查北京天气”）
    HumanMessagePromptTemplate.from_template("{input}"),
    # Agent思考过程占位符：保存工具调用历史、中间思考
    MessagesPlaceholder(variable_name="agent_scratchpad")
])
# 创建信息专家Agent（基于Tool Calling模式，绑定专属工具和Prompt）
info_agent = create_tool_calling_agent(llm, info_tools, info_prompt)
# 创建信息专家的Agent执行器
info_executor = AgentExecutor(
    agent=info_agent,     # 传入构建好的信息专家Agent
    tools=info_tools,     # 传入信息专属工具列表
    verbose=True          # 开启verbose模式，打印详细执行过程
)


# ======================== 板块5：多Agent协作工作流 ========================
# --- 步骤4: 协调和总结工作流 ---
def multi_agent_workflow(query: str, math_task: str, info_task: str):
    # 打印协作流程启动提示，便于查看整体进度
    print("--- 启动多智能体协作流程 ---")
    # 打印用户原始请求，清晰展示协作的核心目标
    print(f"\n用户原始请求: {query}")

    # 4.1 让“计算专家”执行任务
    print("\n[主程序] -> 将任务分配给计算专家...")
    # 调用计算专家执行器，传入计算子任务，获取执行结果（取output字段，无则返回None）
    math_result = math_executor.invoke({"input": math_task}).get("output")
    # 打印计算专家返回的结果，跟踪子任务完成情况
    print(f"\n[主程序] -> 计算专家返回结果: {math_result}")

    # 4.2 让“信息专家”执行任务
    print("\n[主程序] -> 将任务分配给信息专家...")
    # 调用信息专家执行器，传入信息查询子任务，获取执行结果
    info_result = info_executor.invoke({"input": info_task}).get("output")
    # 打印信息专家返回的结果
    print(f"\n[主程序] -> 信息专家返回结果: {info_result}")

    # 4.3 使用 LLM 进行最终结果总结
    print("\n[主程序] -> 使用大模型进行最终总结...")
    # 构建总结用的Prompt模板，约束模型整合子任务结果生成连贯回答
    summarize_prompt = ChatPromptTemplate.from_messages([
        # 系统消息：定义总结助手的角色（整合多Agent结果、生成完整回答）
        ("system", "你是一个善于总结和整合信息的助手。请根据以下信息，为用户原始请求生成一个完整的回答。"),
        # 用户消息：传入原始请求、计算结果、信息查询结果，供模型整合
        ("human",
         f"用户请求: {query}\n\n计算结果: {math_result}\n\n信息查询结果: {info_result}\n\n请整合以上信息，生成一个连贯的最终回答。")
    ])
    # 构建总结链式调用（Prompt模板 → LLM模型 → 字符串解析器）
    summarize_chain = summarize_prompt | llm | StrOutputParser()
    # 调用总结链式调用，生成最终综合回答（传入query仅为占位，实际用模板内的变量）
    final_answer = summarize_chain.invoke({"query": query})

    # 打印协作流程完成提示
    print("\n--- 协作流程已完成！---")
    # 打印最终综合回答，展示多Agent协作的最终成果
    print(f"最终综合回答:\n{final_answer}")
    # 返回最终回答，便于后续复用（如保存、接口返回等）
    return final_answer




# ======================== 板块6：测试运行多Agent协作流程 ========================
# --- 步骤5: 运行并测试 ---
# 主程序入口：仅当脚本直接运行时执行以下代码（导入时不执行）
if __name__ == "__main__":
    # 定义用户原始请求（跨领域复杂任务：计算+信息查询）
    original_query = "请先计算 25 乘以 4，然后告诉我北京今天的天气和当前日期。"
    # 拆分计算子任务（仅保留计算相关内容，分配给计算专家）
    math_task = "计算 25 乘以 4"
    # 拆分信息查询子任务（仅保留信息相关内容，分配给信息专家）
    info_task = "查询北京今天的天气和当前日期"

    # 启动多Agent协作工作流，传入原始请求和拆分后的子任务
    multi_agent_workflow(original_query, math_task, info_task)