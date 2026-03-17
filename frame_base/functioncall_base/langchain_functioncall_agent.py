# 1. 导入核心依赖模块
# langchain_core.tools：提供@tool装饰器，用于定义标准化工具
from langchain_core.tools import tool
# langchain_openai：OpenAI兼容的LLM客户端（适配DeepSeek等模型）
from langchain_openai import ChatOpenAI
# langchain_core.messages：定义消息类型（用户消息/AI消息）
from langchain_core.messages import HumanMessage, AIMessage
# langchain.agents：核心Agent构建工具
# create_tool_calling_agent：创建支持工具调用的Agent
# AgentExecutor：Agent的执行器，管理完整工作流（工具调用、错误处理、日志）
from langchain.agents import create_tool_calling_agent, AgentExecutor
# langchain_core.prompts：提示词模板相关工具
# ChatPromptTemplate：构建对话式Prompt
# MessagesPlaceholder：消息占位符（用于动态填充历史/中间思考）
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# 自定义配置文件（存放模型名、API Key、base_url等）
from config import Config

# 2. 初始化配置（读取模型密钥、名称等）
conf = Config()

# 3. 第一步：定义工具（@tool装饰器自动生成工具Schema）
# @tool装饰器：自动解析函数名、参数类型、文档字符串，生成符合Function Call标准的Schema
# 替代手动编写JSON Schema，同时自动生成invoke方法
@tool
def add(a: int, b: int) -> int:
    """将数字 a 与数字 b 相加"""  # 工具描述（模型用于判断是否调用该工具）
    return a + b  # 工具核心执行逻辑

@tool
def multiply(a: int, b: int) -> int:
    """将数字 a 与数字 b 相乘"""
    return a * b

# 工具列表（Agent会基于此列表识别可用工具）
tools = [add, multiply]

# 4. 第二步：初始化大模型（对接DeepSeek，通过Cloudflare网关）
llm = ChatOpenAI(
    model=conf.model_name,          # 模型名称（如deepseek/deepseek-chat）
    api_key=conf.api_key,           # 模型API Key（或Cloudflare的占位符）
    base_url="https://api.deepseek.com/v1",  # Cloudflare网关地址
    temperature=0,                  # 工具调用场景设0，保证输出确定性
    streaming = False               # 非流式输出（Agent需要完整响应才能解析tool_calls）
)

# 5. 第三步：定义Agent的Prompt模板（核心！控制Agent的行为逻辑）
prompt = ChatPromptTemplate.from_messages([
    # System提示：定义Agent的角色和行为准则
    ("system", "你是可以利用提供的工具进行数学计算的助手。请清晰简洁地回答。"),
    # 消息占位符1：动态填充用户输入和历史对话消息（变量名：messages）
    MessagesPlaceholder(variable_name="messages"),
    # 消息占位符2：动态填充Agent的中间思考/工具调用记录（变量名：agent_scratchpad）
    # 核心作用：保存Agent的思考过程（比如“我需要调用add工具计算2+3”）和工具执行结果，供模型后续推理
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 6. 第四步：创建Tool Calling Agent
# create_tool_calling_agent：绑定模型、工具、Prompt，生成Agent实例
# 底层逻辑：Agent会将工具列表的Schema注入Prompt，让模型知道“有哪些工具可用、怎么用”
agent = create_tool_calling_agent(llm, tools, prompt)

# 7. 第五步：创建Agent执行器（AgentExecutor）
# 核心作用：管理Agent的完整执行流程（模型决策→调用工具→处理结果→生成最终回答）
agent_executor = AgentExecutor(
    agent=agent,                    # 要执行的Agent实例
    tools=tools,                    # 可用工具列表（需和Agent绑定的工具一致）
    verbose=True,                   # 开启详细日志（打印中间步骤：思考→调用工具→结果→最终回答）
    handle_parsing_errors=True      # 自动处理解析错误（比如模型输出格式异常时，重试/兜底）
)

# 8. 第六步：执行用户查询
query = "2+3等于多少？ 11*2是多少"  # 用户输入
# agent_executor.invoke：同步执行Agent，传入参数为字典（key对应Prompt中的占位符）
# "messages": [HumanMessage(content=query)]：填充Prompt中的messages占位符
response = agent_executor.invoke({"messages": [HumanMessage(content=query)]})

# 9. 第七步：打印最终结果
print("最终结果：")
# response["output"]：AgentExecutor返回的最终回答（已整合工具执行结果）
print(response["output"])

"""
被 @tool 装饰的函数会自动生成工具的元数据，
包括函数名、描述和参数信息。
功能上与tools定义的json是等价的
"""