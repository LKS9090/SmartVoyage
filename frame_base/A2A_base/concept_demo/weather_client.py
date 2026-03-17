# courseware/a2a_demo/test_client.py
import asyncio
from python_a2a import A2AClient
from python_a2a import AgentNetwork, A2AClient, Task, Message, MessageRole, TextContent
import uuid
async def main():
    # 1. 初始化两个专家 Agent 的客户端
    weather_client = A2AClient("http://127.0.0.1:5099")

    print("[主控客户端日志] 初始化完成，准备开始任务...")
    print("-" * 50)

    # 2. 任务一：查询天气
    weather_query = "帮我查下北京的天气"
    print(f"[主控客户端日志] 任务一：查询天气 -> '{weather_query}'")
    weather_result = weather_client.ask(weather_query)
    print(f"[主控客户端日志] 收到天气查询结果: {weather_result}")
    print("-" * 50)

    # 2. 测试异步任务
    #构建请求消息
    message_weather = Message(content=TextContent(text=weather_query), role=MessageRole.USER)
    task_weather = Task(id="task-" + str(uuid.uuid4()), message=message_weather.to_dict())
    result_task=await weather_client.send_task_async(task_weather)
    print(f"[主控客户端日志] 收到天气查询结果: {result_task}")

if __name__ == "__main__":
    print("请确保 weather_agent.py 和 ticket_agent.py 正在运行...")
    asyncio.run(main())
