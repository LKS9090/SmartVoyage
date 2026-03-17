import os
import sys
import json
import warnings
import logging
import asyncio
from typing import Optional, List

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from mcp import ClientSession
from mcp.client.sse import sse_client
# 从您的源码来看，load_mcp_tools 和 convert_mcp_tool_to_langchain_tool
# 似乎在同一个模块中，假设为 langchain_mcp_adapters.tools
from langchain_mcp_adapters.tools import load_mcp_tools, convert_mcp_tool_to_langchain_tool

from dotenv import load_dotenv



# Suppress specific warnings
warnings.filterwarnings('ignore')

# Instantiate DeepSeek LLM with deterministic output
llm = ChatOpenAI(
    model="deepseek-reasoner",
    # model="deepseek-chat",
    api_key="sk-8d633094dd79409fad02d1aa83c6c84c",
    base_url="https://api.deepseek.com/v1",
    temperature=0,
    max_tokens=4096,
)

# MCP server URL for SSE connection
server_url = "http://localhost:8002/sse"

# Global holder for the active MCP session (used by tool adapter)
mcp_client = None


# Main async function: connect, load tools, create agent, run chat loop
async def run():
    global mcp_client
    async with sse_client(url=server_url) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            # 这里的 mcp_client 只是一个持有 session 的简单对象
            mcp_client = type("MCPClientHolder", (), {"session": session})()

            # 使用正确的函数签名调用 load_mcp_tools，它已经包含了正确的转换逻辑
            tools = await load_mcp_tools(session)

            # 也可以手动转换，但需要传入 session

            llm_with_tools=llm.bind_tools(tools)
            print("加载以及绑定tools成功！")
            reponse=llm_with_tools.invoke("上海天气")
            print(reponse)



# Entry point: run the async agent loop
if __name__ == "__main__":
    try:
        asyncio.run(run())
        # 如果程序成功运行到这里，说明没有异常
        print("\n运行成功.")
    except Exception as e:
        print(f"\n遇到异常: {e}")
        # 这里捕获并打印了任何未处理的异常，以便更好地调试