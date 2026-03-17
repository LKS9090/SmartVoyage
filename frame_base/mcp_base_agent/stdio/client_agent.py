import asyncio
import json
import sys

from dotenv import load_dotenv
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Instantiate DeepSeek LLM with deterministic output
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key="sk-8d633094dd79409fad02d1aa83c6c84c",
    base_url="https://api.deepseek.com/v1",
    # base_url="https://api.deepseek.com/v1",
    temperature=0,
    max_tokens=4096,
    streaming=False,
)

# Require server script path (hardcoded for this example)
server_script = r"D:\PythonProjectl\SmartVoyage\frame_base\mcp_base_agent\stdio\server_stdio.py"

#配置mcp服务器启动参数
server_params = StdioServerParameters(
    command=sys.executable,  # 使用当前相同的 Python 解释器
    args=[server_script],
)

#定义个mcp客户端
mcp_client = None

#主要的异步函数run_agent
async def run_agent():
    global mcp_client
    async with stdio_client(server_params) as (read, write):
        # 创建会话
        async with ClientSession(read, write) as session:
            # 初始化会话
            await session.initialize()
            #用type()动态创建了一个名为"MCPClientHolder"的类，该类包含一个session属性指向当前会话对象，然后实例化这个类并赋值给全局变量mcp_client。
            #这样做的目的是为了在全局范围内保存和访问会话对象。
            mcp_client = type("MCPClientHolder", (), {"session": session})()
            #加载工具
            tools = await load_mcp_tools(session)

            # 创建prompt模板
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个乐于助人的助手，能够调用工具回答用户问题。"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])

            # 构建工具调用代理
            agent = create_tool_calling_agent(llm, tools, prompt)

            # 创建代理执行器
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

            print("MCP Client Started! Type 'quit' to exit.")
            while True:
                # 接收用户查询
                query = input("\nQuery: ").strip()
                if query.lower() == "quit":
                    break
                # 发送用户查询给代理，并打印格式化后的响应
                response = await agent_executor.ainvoke({"input": query})
                try:
                    print("Response:")
                    print(response)
                except Exception:
                    print("解析有问题")
    return

 #启动运行agent
if __name__ == "__main__":
    asyncio.run(run_agent())