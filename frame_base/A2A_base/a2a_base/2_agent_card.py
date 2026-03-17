from python_a2a import A2AServer, run_server, AgentCard, AgentSkill, TaskStatus, TaskState
# 创建一个代理技能
ticket_skill = AgentSkill(
    name="book_ticket",
    description="预订火车票的技能",
    examples=["预订从上海到北京的火车票"],
    input_modes=["text/plain"],
    output_modes=["text/plain"]
)
# 创建代理卡片
agent_card = AgentCard(
    name="TicketAgent",
    description="一个可以预订票务的代理",
    url="http://127.0.0.1:5009",
    version="1.0.0",
    skills=[ticket_skill],
    capabilities={"streaming": True}
)
# 打印代理卡片的字典表示（用于序列化）
print(agent_card)
print(agent_card.to_dict())