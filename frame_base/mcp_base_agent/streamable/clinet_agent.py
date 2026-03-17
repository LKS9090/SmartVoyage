
# MCP client that connects to a Streamable-HTTP-based MCP server, loads tools, and runs a chat loop using DeepSeek LLM.
import os
import sys
import json
import warnings
import logging
import asyncio
from typing import Optional, List
from langchain_openai import ChatOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
# 抑制特定警告
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 提高日志级别以捕获更多信息
    format='[客户端] %(asctime)s - %(levelname)s - %(message)s'
)

# 实例化 DeepSeek LLM，设置确定性输出
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key="sk-8d633094dd79409fad02d1aa83c6c84c",
    base_url="https://api.deepseek.com/v1",
    temperature=0,
    max_tokens=4096,
)
# MCP 服务器的 Streamable-HTTP 连接地址
server_url = "http://127.0.0.1:8001/mcp"

# 全局 MCP 会话对象（用于工具适配器）
mcp_client = None

# 主异步函数：连接服务器，加载工具，创建 agent，运行交互循环
async def run_agent():
    global mcp_client
    try:
        logging.info(f"准备连接到 Streamable-HTTP 服务器: {server_url}")
        async with streamablehttp_client(server_url) as (read, write, _):
            logging.info("连接已成功建立！")
            async with ClientSession(read, write) as session:
                try:
                    await session.initialize()
                    logging.info("会话初始化成功，可以开始加载工具。")
                    mcp_client = type("MCPClientHolder", (), {"session": session})()

                    # 加载 MCP 工具
                    tools = await load_mcp_tools(session)
                    logging.info(f"成功加载工具: {[tool.name for tool in tools]}")

                    # 创建 agent 的提示模板
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", "你是一个乐于助人的助手，能够调用工具回答用户问题。"),
                        ("human", "{input}"),
                        ("placeholder", "{agent_scratchpad}"),
                    ])

                    # 创建工具调用 agent
                    agent = create_tool_calling_agent(llm, tools, prompt)

                    # 创建 agent 执行器
                    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

                    print("MCP 客户端已启动！输入 'quit' 退出。")
                    while True:
                        query = input("\nQuery: ").strip()
                        if query.lower() == "quit":
                            break
                        # 发送用户查询到 agent 并打印格式化响应
                        logging.info(f"处理用户查询: {query}")
                        response = await agent_executor.ainvoke({"input": query})
                        try:
                            formatted = json.dumps(response, indent=2, ensure_ascii=False)
                        except Exception:
                            formatted = str(response)
                        print("\nResponse:")
                        print(formatted)
                except Exception as e:
                    logging.error(f"会话初始化或工具调用时发生错误: {e}", exc_info=True)
                    raise
    except Exception as e:
        logging.error(f"连接服务器时发生错误: {e}", exc_info=True)
        logging.error(f"请确认服务端脚本已启动并运行在 {server_url}")
        raise

    logging.info("客户端任务完成，连接已关闭。")

# 入口点：运行异步 agent 循环
if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except Exception as e:
        logging.error(f"客户端运行失败: {e}", exc_info=True)