# client_raw.py
import asyncio
import json
import logging
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from python_a2a.mcp import MCPClient
from python_a2a.mcp import FastMCP, text_response
from python_a2a.langchain import to_langchain_tool
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Instantiate DeepSeek LLM with deterministic output
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key="sk-8d633094dd79409fad02d1aa83c6c84c",
    base_url="https://api.deepseek.com",
    temperature=0,
    max_tokens=4096,
)
async def test_mcp_tools():
    # 连接到服务端，端口 8000
    client = MCPClient("http://localhost:8010")
    try:
        # 步骤 1：获取可用工具列表
        tools = await client.get_tools()

        # Convert MCP tool to LangChain
        get_weather_tool = to_langchain_tool("http://localhost:8010", "get_weather")
        query_high_frequency_question = to_langchain_tool("http://localhost:8010", "query_high_frequency_question")
        tools=[get_weather_tool,query_high_frequency_question]

        # Create prompt template for the agent
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "你是一个乐于助人的助手，能够调用工具回答用户问题。对于天气查询，确保用户提供城市名称；对于高频问题，直接调用工具获取结果。工具不需要传参。"),
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
    except Exception as e:
        logger.error(f"MCP 客户端出错：{str(e)}", exc_info=True)
    finally:
        await client.close()

async def main():
    await test_mcp_tools()

if __name__ == "__main__":
    asyncio.run(main())