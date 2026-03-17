import asyncio
from python_a2a import A2AClient, Task, Message, MessageRole, TextContent
import json

async def main():
    # 初始化票务代理客户端（忽略天气客户端以简化测试）
    ticket_client = A2AClient("http://127.0.0.1:5010")

    print("[主控客户端日志] 初始化完成，准备开始任务...")
    print("-" * 50)

    # 任务：预订火车票
    ticket_query = "预订一张从北京到上海的火车票"
    print(f"[主控客户端日志] 任务：预订票务 -> '{ticket_query}'")

    # 创建消息
    message = Message(
        content=TextContent(text=ticket_query),
        role=MessageRole.USER
    )

    # 创建任务
    task = Task(
        id="task-123",
        message=message.to_dict()
    )

    try:
        # 使用 send_task 获取完整 Task 响应
        ticket_result = await ticket_client.send_task_async(task)
        print("[主控客户端日志] 收到票务预订完整结果：")
        print(json.dumps(ticket_result.to_dict(), indent=4, ensure_ascii=False))

        # 解析 artifacts 中的 parts
        print("\n[主控客户端日志] 解析 artifacts 中的 parts：")
        for artifact in ticket_result.artifacts:
            if "parts" in artifact:
                for part in artifact["parts"]:
                    part_type = part.get("type")
                    if part_type == "text":
                        print(f"Text 结果: {part.get('text')}")
                    elif part_type == "error":
                        print(f"Error 消息: {part.get('message')}")
                    elif part_type == "function_response":
                        print(f"Function Response: name={part.get('name')}, response={part.get('response')}")
                    else:
                        print(f"未知类型: {part}")
    except Exception as e:
        print(f"[主控客户端日志] 错误：{str(e)}")

    print("-" * 50)
    print("[主控客户端日志] 所有任务完成！")

if __name__ == "__main__":
    print("请确保 ticket_agent.py 正在运行...")
    asyncio.run(main())



""""
注意：
根本是 ask 方法只提取 part的第一个结果，
而 send_task_async 或 send_task 返回完整 Task，包括 artifacts。
"""