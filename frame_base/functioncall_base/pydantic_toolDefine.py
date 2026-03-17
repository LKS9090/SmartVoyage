from pydantic.v1 import BaseModel, Field
from config import Config
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
"""
Pydantic 是一个 Python 库，用于数据验证和序列化。
它通过使用 Python 类型注解（type hints）来定义数据模型，
并提供强大的数据验证功能。Pydantic 基于 Python 的 dataclasses 和 typing 模块，
允许开发者定义结构化的数据模型，并自动验证输入数据是否符合指定的类型和约束。
"""

conf = Config()

# 第一步：定义工具
class Add(BaseModel):
    """
    将两个数字相加
    """
    a: int = Field(..., description="第一个数字")
    b: int = Field(..., description="第二个数字")

    def invoke(self, args):
        # 验证参数 ：传统需要我们手动写逻辑俩验证，这里不需要手动编写 if-else 语句来检查每个参数的类型和完整性，由pydantic来完成，例如校验字段参数数据类型
        tool_instance = self.__class__(**args)  # 自动验证 a 和 b
        print(tool_instance)

        return tool_instance.a + tool_instance.b

class Multiply(BaseModel):
    """
    将两个数字相乘
    """
    a: int = Field(..., description="第一个数字")
    b: int = Field(..., description="第二个数字")

    def invoke(self, args):
        # 验证参数
        tool_instance = self.__class__(**args)  # 自动验证 a 和 b

        return tool_instance.a * tool_instance.b

tools = [Add, Multiply]


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
query = "2+1等于多少？"
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
    selected_tool = {"add": Add, "multiply": Multiply}[tool_call["name"].lower()]
    # 实例化工具类并调用 invoke
    tool_instance = selected_tool(**tool_call["args"])  # 使用 args 实例化
    tool_output = tool_instance.invoke(tool_call["args"])  # 调用 invoke
    messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
print("第二次 打印 message中增加tool_output 之后：\n")
print(messages)

# 可选：将工具结果传回模型以生成最终回答
final_response = llm_with_tools.invoke(messages)
print("最终模型响应：\n")
print(final_response.content)


"""
-----------------
@tools 自动生成工具的 schema，即参数结构！！
当你调用 selected_tool.invoke(tool_call["args"]) 时，invoke 方法之所以可用，
是因为 @tool 装饰器自动为装饰的函数生成了一个工具对象（StructuredTool 或类似的对象），
并提供了 invoke 方法。这个过程由 LangChain 的工具系统自动处理。
@tool 装饰器根据函数的签名（a: int, b: int）和文档字符串，自动生成工具的 schema（参数结构），并在调用 invoke 时进行基本验证。
例如，invoke 会检查 args 是否包含 a 和 b，并尝试将参数转换为指定的类型（int）。

-------------------
Pydantic 版本为何需要手动实现 invoke：
Pydantic 仅提供数据验证：
Pydantic 的 BaseModel 是一个数据模型，用于定义结构化数据的 schema（例如，a: int 和 b: int）并进行验证。
它不提供工具调用的执行逻辑，也不自动生成 invoke 方法。
因此，你需要在类中手动定义 invoke 方法，指定如何处理输入参数（args）并返回结果。
Pydantic 版本允许你完全控制 invoke 方法的实现。例如，你可以添加复杂的参数处理、错误检查或额外的计算逻辑：
这种灵活性适合需要复杂工具逻辑的场景。

LangChain 的 bind_tools 支持 Pydantic 模型，但期望工具类提供 invoke 方法（或类似的可调用接口）来执行逻辑。
没有 @tool 装饰器的自动化包装，Pydantic 模型需要显式实现 invoke。
"""