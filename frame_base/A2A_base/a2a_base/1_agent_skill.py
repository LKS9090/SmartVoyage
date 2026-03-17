from python_a2a import  AgentSkill
# 定义一个代理技能
ticket_skill = AgentSkill(
    name="book_ticket",
    description="预订火车票的技能",
    examples=["预订从上海到北京的火车票"],
    input_modes=["text/plain"],  # ⬅️ 输入模式 表示这个技能只能接收纯文本字符串作为输入
    output_modes=["text/plain"]  # ⬆️ 输出模式
)

print(ticket_skill)
print(ticket_skill.to_dict())