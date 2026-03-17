# courseware/a2a_demo/test_client.py
import asyncio
from python_a2a import A2AClient

async def main():
    # 1. 初始化两个专家 Agent 的客户端
    weather_client = A2AClient("http://127.0.0.1:5008")
    ticket_client = A2AClient("http://127.0.0.1:5009")

    print("[主控客户端日志] 初始化完成，准备开始任务...")
    print("-" * 50)

    # 2. 任务一：查询天气
    weather_query = "帮我查下北京的天气"
    print(f"[主控客户端日志] 任务一：查询天气 -> '{weather_query}'")
    weather_result = weather_client.ask(weather_query)
    print(f"[主控客户端日志] 收到天气查询结果: {weather_result}")
    print("-" * 50)

    # 3. 任务二：预订火车票
    ticket_query = "预订一张从北京到上海的火车票"
    print(f"[主控客户端日志] 任务二：预订票务 -> '{ticket_query}'")
    ticket_result = ticket_client.ask(ticket_query)
    print(f"[主控客户端日志] 收到票务预订结果: {ticket_result}")
    print("-" * 50)

    print("[主控客户端日志] 所有任务完成！")

if __name__ == "__main__":
    print("请确保 weather_agent.py 和 ticket_agent.py 正在运行...")
    asyncio.run(main())
