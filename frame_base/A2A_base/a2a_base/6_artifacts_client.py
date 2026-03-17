# courseware/a2a_demo/test_client.py
import asyncio
from python_a2a import A2AClient

async def main():
    # 1. 初始化两个专家 Agent 的客户端
    ticket_client = A2AClient("http://127.0.0.1:5010")

    print("[主控客户端日志] 初始化完成，准备开始任务...")
    print("-" * 50)
    #预订火车票
    ticket_query = "预订一张从北京到上海的火车票"
    print(f"[主控客户端日志]预订票务 -> '{ticket_query}'")
    ticket_result = ticket_client.ask(ticket_query)
    print(f"[主控客户端日志] 收到票务预订结果: {ticket_result}")
    print("-" * 50)

    print("[主控客户端日志] 所有任务完成！")

if __name__ == "__main__":
    print("请确保 agent_server在运行 正在运行...")
    asyncio.run(main())
"""
# ask 方法的等价实现（伪代码）
def ask(self, text):
    # 1. 创建并发送 Task
    message = Message(content=TextContent(text=text), role=MessageRole.USER)
    task = Task(message=message.to_dict())
   response = self._send_http_request(task.to_dict())
    
    # 2. 获取第一个 artifact 的第一个 part ⭐关键⭐
    first_part = response.artifacts[0]["parts"][0]
    
    # 3. 根据 part 的类型格式化输出
    if first_part["type"] == "function_response":
        # 如果是函数响应，返回格式化的字符串
       return f"Function '{first_part['name']}' returned: {\n  {json.dumps(first_part['response'], indent=2)}\n}"
    elif first_part["type"] == "text":
        # 如果是文本，直接返回
       return first_part["text"]
    else:
        # 其他类型，返回字符串表示
       return str(first_part)

✅ 是的，client.ask() 只能获得 parts 列表中第一个字典的结果
✅ 如果要获取所有 parts，必须使用 send_task_async() 或类似方法
✅ 这是设计上的权衡：简洁性 vs 完整性
"""
