from python_a2a import A2AServer, AgentCard, AgentSkill, TaskStatus, TaskState,A2AClient

# 定义代理卡片
ticket_card = AgentCard(
    name="TicketAgentServer",
    description="票务代理",
    url="http://127.0.0.1:5009",
    skills=[AgentSkill(name="book_ticket", description="预订票务")]
)
# 自定义 A2AServer 子类
class TicketServer(A2AServer):
    def __init__(self):
        super().__init__(agent_card=ticket_card)

    def handle_task(self, task):# 这是服务器最重要的方法！每个请求都会调用它
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task

# 创建实例（不启动，仅测试）
server = TicketServer()
print("代理名称：", server.agent_card.name)