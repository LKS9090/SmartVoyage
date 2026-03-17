import os
import sys
import json
import warnings
import logging
import asyncio
from typing import Optional, List

from langchain_openai import ChatOpenAI
from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env (e.g., GEMINI_API_KEY)

# Suppress specific warnings
warnings.filterwarnings('ignore')

# Instantiate DeepSeek LLM with deterministic output
llm = ChatOpenAI(
    model="deepseek-chat",
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
async def run_agent():
    global mcp_client
    async with sse_client(url=server_url) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            mcp_client = type("MCPClientHolder", (), {"session": session})()
            tools = await load_mcp_tools(session)

            print("tools==========")

            print( tools)
            print(type(tools))

            # Create prompt template for the agent
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个乐于助人的助手，能够调用工具回答用户问题。"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])

            # Create tool-calling agent
            agent = create_tool_calling_agent(llm, tools, prompt)

            # Create agent executor
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

            print("MCP Client Started! Type 'quit' to exit.")
            while True:
                query = input("\nQuery: ").strip()
                if query.lower() == "quit":
                    break
                # Send user query to agent and print formatted response
                response = await agent_executor.ainvoke({"input": query})
                try:
                    formatted = json.dumps(response, indent=2, ensure_ascii=False)
                except Exception:
                    formatted = str(response)
                print("\nResponse:")
                print(formatted)
    return

# Entry point: run the async agent loop
if __name__ == "__main__":
    asyncio.run(run_agent())