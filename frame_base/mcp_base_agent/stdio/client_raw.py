import asyncio
import sys
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Require server script path (hardcoded for this example)
server_script = r"D:\PythonProjectl\SmartVoyage\frame_base\mcp_base_agent\stdio\server_stdio.py"

#配置mcp 服务器启动参数
server_params = StdioServerParameters(
    command=sys.executable,  # 使用当前相同的 Python 解释器
    args=[server_script],
)

#定义个 mcp 客户端
mcp_client = None
"""
initialize()是客户端和服务端的 “初始化握手”—— 客户端发初始化请求，服务端返回自身信息（比如支持的工具、协议版本），只有初始化完成才能调用工具
"""
#主要的异步函数 run_agent
async def run():
    global mcp_client
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_client = type("MCPClientHolder", (), {"session": session})()
            tools = await load_mcp_tools(session)
            print("tools=>",tools)
            response = await session.call_tool("get_weather", arguments={})
            print(response)

        return


 #启动运行 agent
if __name__ == "__main__":
    asyncio.run(run())