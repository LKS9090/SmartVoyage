from python_a2a import AIAgentRouter, AgentNetwork
from langchain_openai import ChatOpenAI
from config import Config
conf=Config()
from python_a2a import AgentNetwork



network = AgentNetwork(name="MyNetwork")
network.add("TicketAgent", "http://127.0.0.1:5010")
llm = ChatOpenAI(model=conf.model_name,base_url=conf.api_url,api_key=conf.api_key,temperature=0)
router = AIAgentRouter(llm_client=llm, agent_network=network)
agent_name, confidence = router.route_query("预订票")
print(agent_name, confidence)

"""
┌─────────────────────────────────────────────────────────┐
│ Step 1: 构建路由 Prompt                                 │
├─────────────────────────────────────────────────────────┤
│ 可用的 Agent：                                          │
│ - TicketAgent: 票务代理                                 │
│   Skills: [book_ticket]                                 │
│                                                         │
│ 用户查询：预订票                                        │
│                                                         │
│ 请返回 JSON 格式的选中 Agent...                         │
└─────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: 调用 LLM 进行推理                               │
├─────────────────────────────────────────────────────────┤
│ LLM 思考：                                              │
│ "预订票" → 匹配到 TicketAgent 的 book_ticket 技能       │
│ 置信度：0.95                                            │
│ 理由：查询明确提到票务预订                              │
└─────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: 解析 LLM 响应                                   │
├─────────────────────────────────────────────────────────┤
│ 返回：                                                  │
│ {                                                       │
│   "agent_name": "TicketAgent",                          │
│   "confidence": 0.95,                                   │
│   "reason": "查询匹配票务技能"                          │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────┐
│ Step 4: 返回路由结果                                    │
├─────────────────────────────────────────────────────────┤
│ agent_name = "TicketAgent"                              │
│ confidence = 0.95                                       │
└─────────────────────────────────────────────────────────┘


"""