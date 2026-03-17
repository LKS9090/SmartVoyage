from python_a2a import A2AServer, run_server, AgentCard, AgentSkill, TaskStatus, TaskState

# 定义代理卡片
ticket_card = AgentCard(
    name="TicketAgentServer",
    description="票务代理",
    url="http://127.0.0.1:5009",
    skills=[AgentSkill(name="book_ticket", description="预订票务")]
)

# 自定义 A2AServer 子类（简化）
class TicketServer(A2AServer):
    def __init__(self):
        super().__init__(agent_card=ticket_card)# 把卡片挂到服务器上


    def handle_task(self, task):
        print(f"[{self.agent_card.name}] 收到任务====: {task}")
        task.status = TaskStatus(state=TaskState.COMPLETED)
        print(f"[{self.agent_card.name}] 任务完成====: {task}")
        return task

# 启动服务器
if __name__ == "__main__":
    server = TicketServer()
    print(f"[{server.agent_card.name}] 启动成功，服务地址: {server.agent_card.url}")
    run_server(server, host="127.0.0.1", port=5009, debug=False)

"""
[TicketAgentServer] 收到任务====: Task(id='d7f4bc49-4f09-4793-ab46-6be98d7f129c', 
session_id='1e401e4f-29ce-4883-9263-fa08a52b4345', status=TaskStatus(state=<TaskState.SUBMITTED: 
'submitted'>, message=None, timestamp='2026-03-10T14:04:40.263717'), 
message={'content': {'text': '我想预订从上海到北京的火车票', 'type': 'text'}, 
'role': 'user', 'message_id': '26ec5409-73c8-4d2d-b1a1-697e63c4feb9'}, history=[], artifacts=[], metadata={})
"""