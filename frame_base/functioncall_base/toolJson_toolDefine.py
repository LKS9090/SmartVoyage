from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
from config import Config
import warnings
warnings.filterwarnings("ignore")

conf = Config()

# 第一步：定义工具函数
def add(a: int, b: int) -> int:
    """
    将数字a与数字b相加
    Args:
        a: 第一个数字
        b: 第二个数字
    """
    return a + b

def multiply(a: int, b: int) -> int:
    """
    将数字a与数字b相乘
    Args:
        a: 第一个数字
        b: 第二个数字
    """
    return a * b

# 定义工具调用分发函数
def call_function(name: str, args: dict) -> str:
    """
    根据工具名称调用对应的工具函数
    Args:
        name: 工具名称
        args: 工具参数
    Returns:
        工具执行结果（字符串格式）
    """
    try:
        if name == "add":
            return str(add(**args))
        if name == "multiply":
            return str(multiply(**args))
        return f"未知工具: {name}"
    except Exception as e:
        return f"工具调用失败: {str(e)}"




# 定义 JSON 格式的工具 schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "add",
            "description": "将数字a与数字b相加",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "integer",
                        "description": "第一个数字"
                    },
                    "b": {
                        "type": "integer",
                        "description": "第二个数字"
                    }
                },
                "required": ["a", "b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "multiply",
            "description": "将数字a与数字b相乘",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "integer",
                        "description": "第一个数字"
                    },
                    "b": {
                        "type": "integer",
                        "description": "第二个数字"
                    }
                },
                "required": ["a", "b"]
            }
        }
    }
]

# 第二步：初始化模型
#https://api-docs.deepseek.com/zh-cn/guides/reasoning_model
llm = ChatOpenAI(
    # model=conf.model_name,
    model="deepseek-chat",
    api_key='sk-945138b82e0e4f7da47f498400c94f05',
    base_url="https://api.deepseek.com/v1",
    temperature=0,  # 确保输出更可控
    streaming = False
)
"""
temperature 是大模型的随机性控制参数，取值范围通常是 0 ~ 2（不同模型略有差异），核心作用是：
数值越低：模型输出越 “保守、确定、可预测”，每次回答几乎一致；
数值越高：模型输出越 “开放、随机、有创意”，每次回答可能不一样。
"""

# 第三步：调用回复
# query = "2+3等于多少？ 11*2是多少"
query = "2+1等于多少？"
messages = [HumanMessage(query)]
print("打印 message：\n")
print(messages)
print("*" * 60)

# invoke 是同步方法，传递 tools 参数
try:
    ai_msg = llm.invoke(messages, tools=tools, tool_choice="auto")
    # ai_msg = llm.invoke(messages, tool_choice="auto")
    print("====================")
    print(ai_msg)
    messages.append(ai_msg)
    print("第一轮 打印 message.append(ai_msg) 之后：\n")
    print(messages)
    print("*" * 60)

    # 处理工具调用
    # 判断消息中是否有tool_calls，以判断工具是否被调用
    if hasattr(ai_msg, 'tool_calls') and ai_msg.tool_calls:
        for tool_call in ai_msg.tool_calls:
            # 使用 call_function 处理工具调用
            tool_output = call_function(tool_call["name"], tool_call["args"])
            messages.append(ToolMessage(content=tool_output, tool_call_id=tool_call["id"]))
        print("第二轮  message中增加tool_output 之后：\n")
        print(messages)
        print("*" * 60)

        # 将工具结果传回模型以生成最终回答
        final_response = llm.invoke(messages, tools=tools)
        print("最终模型响应：\n")
        print(final_response.content)
    else:
        print("模型未生成工具调用，直接返回文本:")
        print(ai_msg.content)
except Exception as e:
    print(f"模型调用失败: {str(e)}")

"""
. 作用
if hasattr(ai_msg, 'tool_calls') and ai_msg.tool_calls: 的作用是：

检查 tool_calls 属性是否存在:
hasattr(ai_msg, 'tool_calls') 验证 ai_msg（通常是 AIMessage 对象）是否具有 tool_calls 属性。
这防止了直接访问 ai_msg.tool_calls 时可能抛出的 AttributeError，如果模型响应不包含 tool_calls（例如，模型返回纯文本而非工具调用）。
确保 tool_calls 不为空:
ai_msg.tool_calls 检查 tool_calls 属性是否为非空值（例如，包含工具调用的列表）。
这避免了处理空列表（[]）的情况，确保只有在有实际工具调用时才进入后续逻辑。
安全处理工具调用:
"""