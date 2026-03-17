# courseware/a2a_mcp_collaboration/test_client.py
import asyncio
from python_a2a import A2AClient

async def main():
    # 客户端只知道主控 Agent 的存在
    main_agent_client = A2AClient("http://127.0.0.1:8005")
    
    print("[主客户端日志] 准备向主控 Agent 发送任务...")
    query = "请帮我查一下北京的天气"
    
    # 发起 A2A 调用
    result = main_agent_client.ask(query)
    
    print(f"[主客户端日志] 收到最终结果: '{result}'")

if __name__ == "__main__":
    print("请确保 mcp_weather_tool_agent.py 和 a2a_main_agent.py 正在运行...")
    asyncio.run(main())
