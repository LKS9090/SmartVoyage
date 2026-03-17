import json
import logging
import time
from typing import Dict, List, Any
import re
from datetime import datetime
import pytz
from python_a2a import A2AClient, AgentNetwork, AIAgentRouter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from SmartVoyage.config import Config  # 假设config路径与main.py一致

# 设置日志（与main.py保持一致）
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化配置（与main.py一致）
conf = Config()
LLM_MODEL = conf.model_name
OPENAI_API_KEY = conf.api_key
OPENAI_API_URL = conf.api_url

# 步骤1: 定义Prompt模板（与main.py完全一致，确保意图识别和总结逻辑相同）
# 1.1 意图识别Prompt
intent_prompt = ChatPromptTemplate.from_template(
    """
系统提示：您是一个专业的旅行意图识别专家，基于用户查询和对话历史，识别意图并提取槽位。严格遵守规则：
- 支持意图：['weather' (天气查询), 'flight' (机票查询), 'train' (高铁/火车票查询), 'concert' (演唱会票查询), 'attraction' (景点推荐)] 或其组合（如 ['weather', 'flight']）。
- 如果意图超出范围，返回意图 'out_of_scope'。
- 提取槽位：
  - weather: city (城市，多个用逗号分隔), date (日期，支持'今天'/'明天'/'后天'/'未来X天'，转换为YYYY-MM-DD或范围)。
  - flight/train: departure_city (出发城市), arrival_city (到达城市), date (日期), seat_type (座位类型，如'经济舱'/'硬卧')。
  - concert: city (城市), artist (艺人), date (日期), ticket_type (票务类型，如'看台、VIP')。
  - attraction: city (城市), preferences (偏好，如'历史'/'自然')。
- 如果意图为组合，只提取公共槽位，并在后续处理中分别填充。
- 如果槽位缺失，返回 'missing_slots' 列表和追问消息,不得回复空信息。
- 对于weather：如果无city，默认['北京','上海','广州','深圳']；无date，默认今天。
- 输出严格为JSON：{{"intents": ["intent1", "intent2"], "slots": {{"intent1": {{"slot1": "value1"}}, "intent2": {{"slot2": "value2"}}}}, "missing_slots": {{"intent1": ["slot1"]}}, "follow_up_message": "追问消息"}}。不要添加额外文本！
- 当前日期：{current_date} (Asia/Shanghai)。
- 基于整个对话历史填充槽位，优先最新查询。

对话历史：{conversation_history}
用户查询：{query}
    """
)

# 1.2 响应评估Prompt（保持原样，用于LLM质量评分）
response_eval_prompt = ChatPromptTemplate.from_template(
    """
系统提示：你是一个专业的AI助手评估员。请根据用户查询和智能体响应，以及提供的评分标准，对响应进行评估。

评分标准：
1. 流畅性：回答是否自然、通顺，没有语法错误或奇怪的表述。
2. 准确性：回答中的信息是否准确，没有编造或错误。
3. 帮助性：回答是否真正解决了用户的问题。

用户查询: {user_query}
智能体响应: {agent_response}

请以JSON格式返回你的评估结果，包括总分（1-5分，float类型）和简短的评估理由。不要包含任何额外文本。
示例输出:
{{"score": 4.5, "reason": "回答流畅，信息基本准确，但缺少部分细节。"}}
    """
)

# 1.3 天气总结Prompt（从main.py复制，确保一致）
summarize_weather_prompt = ChatPromptTemplate.from_template(
    """
系统提示：您是一位专业的天气预报员，以生动、准确的风格总结天气信息。基于查询和结果：
- 核心：城市、日期、温度范围、天气描述、湿度、风向、降水。
- 如果结果为空，提示“未找到数据，请确认城市/日期，不得编造。”
- 语气：专业预报，如“根据最新数据，北京2025-07-31的天气预报为...”。
- 保持中文，100-150字。
- 如果查询无关，返回“请提供天气相关查询。”

查询：{query}
结果：{raw_response}
    """
)

# 1.4 票务总结Prompt（从main.py复制，确保一致）
summarize_ticket_prompt = ChatPromptTemplate.from_template(
    """
系统提示：您是一位专业的旅行顾问，以热情、精确的风格总结票务信息。基于查询和结果：
- 核心：出发/到达、时间、类型、价格、剩余座位。
- 如果结果为空，提示“未找到数据，请确认条件，不得编造。”
- 语气：顾问式，如“为您推荐北京到上海的机票选项...”。
- 保持中文，100-150字。
- 如果查询无关，返回“请提供票务相关查询。”

查询：{query}
结果：{raw_response}
    """
)

# 1.5 景点推荐Prompt（从main.py复制，确保一致）
attraction_prompt = ChatPromptTemplate.from_template(
    """
系统提示：您是一位旅行专家，基于用户查询生成景点推荐。规则：
- 推荐3-5个景点，包含描述、理由、注意事项。
- 基于槽位：城市、偏好。
- 语气：热情推荐，如“推荐您在北京探索故宫...”。
- 备注：内容生成，仅供参考。
- 保持中文，150-250字。

查询：{query}
槽位：{slots}
    """
)


class AgentEvaluator:
    def __init__(self):
        """步骤2: 初始化评估器（与main.py的初始化逻辑一致，添加LLM和网络）"""
        # 2.1 初始化LLM（与main.py一致）
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_URL,
            temperature=0
        )
        # 2.2 初始化意图链和评估链
        self.intent_chain = intent_prompt | self.llm
        self.eval_chain = response_eval_prompt | self.llm
        self.summarize_weather_chain = summarize_weather_prompt | self.llm
        self.summarize_ticket_chain = summarize_ticket_prompt | self.llm
        self.attraction_chain = attraction_prompt | self.llm
        # 2.3 初始化Agent网络和路由器（与main.py一致，但评估时优先使用network.get_agent）
        self.network = AgentNetwork(name="Travel Assistant Network")
        self.network.add("Weather Query Assistant", "http://localhost:5005")
        self.network.add("Ticket Query Assistant", "http://localhost:5006")
        llm_client = A2AClient("http://localhost:6666")
        self.router = AIAgentRouter(
            llm_client=llm_client,
            agent_network=self.network
        )
        # 2.4 存储代理URL（与main.py一致，用于日志）
        self.agent_urls = {
            "Weather Query Assistant": "http://localhost:5005",
            "Ticket Query Assistant": "http://localhost:5006"
        }

    def simulate_response(self, user_query: str, current_date: str) -> str:
        """步骤3: 模拟main.py的端到端响应生成（核心修复：使用network.get_agent().ask）"""
        # 3.1 意图识别（与main.py一致）
        intent_response = self.intent_chain.invoke({
            "conversation_history": "",  # 测试用例无历史
            "query": user_query,
            "current_date": current_date
        }).content.strip()
        logger.info(f"意图识别原始响应: {intent_response}")
        # 3.2 清理并解析JSON（与main.py一致）
        intent_response = re.sub(r'^```json\s*|\s*```$', '', intent_response).strip()
        try:
            intent_output = json.loads(intent_response)
            intents = intent_output.get("intents", [])
            slots = intent_output.get("slots", {})
            missing_slots = intent_output.get("missing_slots", {})
            follow_up_message = intent_output.get("follow_up_message", "")
            logger.info(f"解析意图输出: {intent_output}")
        except json.JSONDecodeError as json_err:
            logger.error(f"JSON解析失败: {json_err}")
            return f"意图识别失败：{str(json_err)}。请重试。"

        # 3.3 处理out_of_scope或missing_slots（与main.py一致）
        if "out_of_scope" in intents:
            return "您好!我是AI旅行助手SmartVoyage，专注于旅行相关的信息和服务，比如火车票、高铁票、演唱会门票、天气查询、景点推荐等。如果您有任何旅行方面的需求，请随时告诉我，我会尽力为您提供帮助!"
        elif missing_slots:
            return follow_up_message or "请提供更多信息以完成查询。"

        # 3.4 生成多意图响应（与main.py一致，逐个处理）
        responses = []
        routed_agents = []
        for intent in intents:
            if intent == "attraction":
                # 3.4.1 直接生成景点推荐
                rec_response = self.attraction_chain.invoke({
                    "query": user_query,
                    "slots": json.dumps(slots.get(intent, {}), ensure_ascii=False)
                }).content.strip()
                responses.append(rec_response)
            else:
                # 3.4.2 确定代理名称
                agent_name = "Weather Query Assistant" if intent == "weather" else "Ticket Query Assistant" if intent in ["flight", "train", "concert"] else None
                if not agent_name:
                    responses.append("暂不支持此意图。")
                    continue
                # 3.4.3 构建查询字符串（与main.py一致，处理槽位）
                intent_slots = slots.get(intent, {})
                if intent == "weather":
                    if not intent_slots.get("city"):
                        intent_slots["city"] = "北京,上海,广州,深圳"  # 默认城市
                    if not intent_slots.get("date"):
                        intent_slots["date"] = current_date  # 默认今天
                    query_str = f"{intent_slots['city']} {intent_slots['date']}"
                else:
                    query_str = f"{intent} {intent_slots.get('departure_city', '')} {intent_slots.get('arrival_city', '')} {intent_slots.get('date', current_date)} {intent_slots.get('seat_type', '')}".strip()
                    if intent == "concert":
                        query_str = f"演唱会 {intent_slots.get('city', '')} {intent_slots.get('artist', '')} {intent_slots.get('date', current_date)} {intent_slots.get('ticket_type', '')}".strip()
                # 3.4.4 调用代理（修复：使用network.get_agent().ask，与main.py一致）
                try:
                    agent = self.network.get_agent(agent_name)
                    raw_response = agent.ask(query_str)
                    logger.info(f"{agent_name} 原始响应: {raw_response}")
                except Exception as e:
                    logger.error(f"代理调用失败 {agent_name}: {str(e)}")
                    raw_response = "代理服务暂不可用。"
                # 3.4.5 总结响应（与main.py一致）
                if agent_name == "Weather Query Assistant":
                    sum_response = self.summarize_weather_chain.invoke({
                        "query": query_str,
                        "raw_response": raw_response
                    }).content.strip()
                else:
                    sum_response = self.summarize_ticket_chain.invoke({
                        "query": query_str,
                        "raw_response": raw_response
                    }).content.strip()
                responses.append(sum_response)
                routed_agents.append(agent_name)

        # 3.6 组合最终响应（与main.py一致）
        final_response = "\n\n".join(responses)
        if routed_agents:
            final_response = f"**路由至：{', '.join(set(routed_agents))}**\n\n" + final_response
        return final_response

    def evaluate_test_cases(self, test_cases: List[Dict[str, Any]]):
        """步骤4: 运行测试用例并评估（整合simulate_response，计算指标）"""
        # 4.1 初始化结果统计
        results = {
            "total_tests": len(test_cases),
            "correct_intent": 0,
            "correct_response_keywords": 0,
            "latency_sum": 0.0,
            "llm_score_sum": 0.0,
            "failures": []
        }
        current_date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')

        # 4.2 逐个运行测试用例
        for i, case in enumerate(test_cases):
            user_query = case["query"]
            expected_intent = case["expected_intent"]
            expected_keywords = case.get("expected_keywords", [])

            logger.info(f"--- 运行测试用例 {i + 1}/{results['total_tests']}: {user_query} ---")

            start_time = time.time()
            try:
                # 4.2.1 意图识别评估（独立于响应生成）
                intent_response = self.intent_chain.invoke({
                    "conversation_history": "",
                    "query": user_query,
                    "current_date": current_date
                }).content.strip()
                intent_response = re.sub(r'^```json\s*|\s*```$', '', intent_response).strip()
                intent_output = json.loads(intent_response)
                detected_intents = intent_output.get("intents", [])
                is_correct_intent = (expected_intent in detected_intents)
                if is_correct_intent:
                    results["correct_intent"] += 1

                # 4.2.2 端到端响应生成（使用simulate_response）
                final_response = self.simulate_response(user_query, current_date)
                latency = time.time() - start_time
                results["latency_sum"] += latency

                # 4.2.3 关键词匹配（简单字符串包含检查）
                is_correct_response = all(keyword in final_response for keyword in expected_keywords)
                if is_correct_response:
                    results["correct_response_keywords"] += 1

                # 4.2.4 LLM辅助质量评估
                llm_eval_response = self.eval_chain.invoke({
                    "user_query": user_query,
                    "agent_response": final_response
                }).content.strip()
                llm_eval_response = re.sub(r'^```json\s*|\s*```$', '', llm_eval_response).strip()
                llm_eval_output = json.loads(llm_eval_response)
                llm_score = llm_eval_output.get("score", 0.0)
                results["llm_score_sum"] += llm_score

                logger.info(f"预期意图: {expected_intent}, 实际意图: {detected_intents}, 意图匹配: {is_correct_intent}")
                logger.info(f"响应: {final_response.strip()}")
                logger.info(f"响应时间: {latency:.2f} 秒")
                logger.info(f"LLM评估分数: {llm_score:.1f}/5.0, 理由: {llm_eval_output.get('reason')}")

                # 4.2.5 记录失败
                if not is_correct_intent or not is_correct_response:
                    results["failures"].append({
                        "query": user_query,
                        "expected_intent": expected_intent,
                        "detected_intents": detected_intents,
                        "final_response": final_response,
                        "reason": "Intent or keyword mismatch"
                    })

            except Exception as e:
                logger.error(f"测试用例 {user_query} 失败: {str(e)}")
                results["failures"].append({
                    "query": user_query,
                    "reason": f"Exception: {str(e)}"
                })
                latency = time.time() - start_time
                results["latency_sum"] += latency  # 即使失败也计时

        return results

    def print_summary(self, results: Dict[str, Any]):
        """步骤5: 打印评估总结报告（与原版一致，但添加更多细节）"""
        # 5.1 计算平均值
        total_tests = results['total_tests']
        avg_latency = results['latency_sum'] / total_tests if total_tests > 0 else 0
        avg_llm_score = results['llm_score_sum'] / total_tests if total_tests > 0 else 0

        # 5.2 打印报告
        print("\n\n--- 智能体评估报告 ---")
        print(f"总测试用例: {total_tests}")
        print(f"意图识别准确率: {results['correct_intent'] / total_tests:.2%} ({results['correct_intent']}/{total_tests})")
        print(f"响应关键词匹配率: {results['correct_response_keywords'] / total_tests:.2%} ({results['correct_response_keywords']}/{total_tests})")
        print(f"平均响应时间: {avg_latency:.2f} 秒")
        print(f"LLM评估平均分: {avg_llm_score:.2f}/5.0")

        # 5.3 打印失败详情
        if results['failures']:
            print(f"\n--- 失败详情 ({len(results['failures'])}/{total_tests}) ---")
            for failure in results['failures']:
                print(f"查询: {failure['query']}")
                print(f"原因: {failure['reason']}")
                if 'final_response' in failure:
                    print(f"最终响应: {failure['final_response'][:100]}...")  # 截断显示
                print("-" * 20)


if __name__ == "__main__":
    # 步骤6: 定义测试用例集（调整以匹配main.py逻辑，修正"input_required"为"out_of_scope"）
    # 6.1 基本功能测试
    test_cases = [
        {"query": "北京明天天气如何？", "expected_intent": "weather", "expected_keywords": ["北京", "天气"]},
        {"query": "帮我查一下明天广州到上海的机票，经济舱", "expected_intent": "flight", "expected_keywords": ["上海", "广州", "机票"]},
        {"query": "想看明天刀郎在深圳的演唱会,需要VIP", "expected_intent": "concert", "expected_keywords": ["刀郎", "演唱会"]},
        {"query": "北京比较经典的景点推荐，文化方面的", "expected_intent": "attraction", "expected_keywords": ["故宫", "北京"]},  # 假设生成中包含这些关键词

        # 6.2 鲁棒性测试
        {"query": "请问上海的天气？", "expected_intent": "weather", "expected_keywords": ["上海", "天气"]},
        {"query": "你好，你可以做什么？", "expected_intent": "out_of_scope", "expected_keywords": ["SmartVoyage", "AI旅行助手"]},  # 假设生成中包含这些关键词", "expected_intent": "out_of_scope", "expected_keywords": ["SmartVoyage", "服务"]},  # 调整为out_of_scope，关键词匹配欢迎消息

        # 6.3 多意图测试
        {"query": "北京的天气和明天去上海的高铁票，二等座", "expected_intent": "weather", "expected_keywords": ["北京", "上海", "二等座"]},  # 至少匹配weather意图
    ]

    # 6.4 运行评估
    evaluator = AgentEvaluator()
    evaluation_results = evaluator.evaluate_test_cases(test_cases)
    evaluator.print_summary(evaluation_results)