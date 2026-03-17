from python_a2a import AgentNetwork
network = AgentNetwork(name="MyNetwork")
network.add("TicketAgent", "http://127.0.0.1:5010")
"""
这一行完成了 A2A 的连接建立！
底层发生了什么：
def add(self, agent_name, agent_url):
    # 1. 创建 A2AClient（A2A 协议的客户端）
    client = A2AClient(base_url=agent_url)
    
    # 2. 获取 AgentCard（对方的名片/能力描述）
    card = client.get_agent_card()  # HTTP GET http://127.0.0.1:5010/.well-known/agent-card
    
    # 3. 保存到注册表
    self.agents[agent_name] = client
    self.agent_cards[agent_name] = card

"""
client = network.get_agent("TicketAgent")

print(client.ask("预订一张从北京到上海的火车票"))

print("agent network=============")
print(network.agent_cards)