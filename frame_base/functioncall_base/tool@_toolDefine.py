from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
from config import Config

conf = Config()

# 第一步：定义工具
@tool
def add(a: int, b: int) -> int:
    """
    将数字a与数字b相加
    Args:
        a: 第一个数字
        b: 第二个数字
    """
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """
    将数字a与数字b相乘
    Args:
        a: 第一个数字
        b: 第二个数字
    """
    return a * b

tools = [add, multiply]

# 第二步：绑定工具到模型
llm = ChatOpenAI(
    model=conf.model_name,
    api_key=conf.api_key,
    base_url="https://api.deepseek.com/v1",
    temperature=0,  # 确保输出更可控
    streaming = False

)

# 绑定工具，允许模型自动选择工具
llm_with_tools = llm.bind_tools(tools, tool_choice="auto")

# 第三步：调用回复
query = "2+1等于多少？ 2*6是多少？"
messages = [HumanMessage(query)]
print("打印 message：\n")
print(messages)
print("*" * 60)

# invoke 是同步方法，等待模型处理完成并返回完整响应
ai_msg = llm_with_tools.invoke(messages)
print("====================")
print(ai_msg)
messages.append(ai_msg)
print("第一次 打印 message.append(ai_msg) 之后：\n")
print(messages)
print("*" * 60)

# 处理工具调用
for tool_call in ai_msg.tool_calls:
    selected_tool = {"add": add, "multiply": multiply}[tool_call["name"].lower()]
    tool_output = selected_tool.invoke(tool_call["args"])  # 直接调用工具
    messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
print("第二次 打印 message中增加tool_output 之后：\n")
print(messages)

# 将工具结果传回模型以生成最终回答
final_response = llm_with_tools.invoke(messages)
print("最终模型响应：\n")
print(final_response.content)

"""
#tool@_toolDefine.py
手动实现工具调用逻辑：没有使用
LangChain 的 Agent 框架，而是通过手动调用 llm.bind_tools 和
处理 tool_calls 来实现工具调用。
 
#langchain_functioncall_agent.py
LangChain Agent 框架：基于 create_tool_calling_agent 和
AgentExecutor 构建标准化的 Agent 工作流。

"""