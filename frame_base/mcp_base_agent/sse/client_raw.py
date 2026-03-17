import warnings
import asyncio
from langchain_openai import ChatOpenAI
from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_mcp_adapters.tools import load_mcp_tools

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env (e.g., GEMINI_API_KEY)

# Suppress specific warnings
warnings.filterwarnings('ignore')

# MCP server URL for SSE connection
server_url = "http://localhost:8001/sse"

# Global holder for the active MCP session (used by tool adapter)
mcp_client = None


# Main async function: connect, load tools, create agent, run chat loop
async def run():
    global mcp_client
    async with sse_client(url=server_url) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            mcp_client = type("MCPClientHolder", (), {"session": session})()
            tools = await load_mcp_tools(session)
            print("tool调用==============",tools)
            response=await session.call_tool("get_weather", arguments={})
            print(response)


# Entry point: run the async agent loop
if __name__ == "__main__":
    asyncio.run(run())