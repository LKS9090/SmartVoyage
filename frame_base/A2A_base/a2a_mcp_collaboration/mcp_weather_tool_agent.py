# courseware/a2a_mcp_collaboration/mcp_weather_tool_agent.py
import uvicorn
from python_a2a.mcp import FastMCP, create_fastapi_app

mcp = FastMCP(name="WeatherTool")

@mcp.tool(name="get_weather", description="获取城市天气")
def get_weather(city: str) -> str:
    print(f"[MCP 工具 Agent 日志] 收到工具调用，查询城市: {city}")
    if city == "北京":
        return "北京今天阳光明媚，29°C"
    return f"找不到 {city} 的天气"

if __name__ == "__main__":
    app = create_fastapi_app(mcp)
    print("[MCP 工具 Agent] 已启动，在 http://127.0.0.1:6005")
    uvicorn.run(app, host="127.0.0.1", port=6005)

"""
┌─────────────────────────────────────────────────────────────┐
│ 层级 1: A2A Client (main_client.py)                         │
│ A2AClient("http://127.0.0.1:8005")                          │
│ client.ask("请帮我查一下北京的天气")                        │
└─────────────────────────────────────────────────────────────┘
                        ↓ HTTP POST /task/send
┌─────────────────────────────────────────────────────────────┐
│ 层级 2: A2A Server (a2a_main_agent.py)                      │
│ MainAgentServer.handle_task(task)                           │
│ 1. 解析查询："请帮我查一下北京的天气"                       │
│ 2. 决策：包含"天气" → 需要调用 MCP 工具                     │
│ 3. 调用：mcp_client.call_tool("get_weather", city="北京")   │
└─────────────────────────────────────────────────────────────┘
                        ↓ MCP 协议调用
┌─────────────────────────────────────────────────────────────┐
│ 层级 3: MCP Server (mcp_weather_tool_agent.py)              │
│ FastMCP 工具服务器                                          │
│ 1. 接收：POST /tools/call                                   │
│ 2. 路由：找到 get_weather 函数                              │
│ 3. 执行：get_weather(city="北京")                           │
│ 4. 返回："北京今天阳光明媚，29°C"                           │
└─────────────────────────────────────────────────────────────┘

"""