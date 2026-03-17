# multi_intents.py
# 核心功能：演示一个能够处理多意图查询的主控 Agent。
# 流程：用户查询 -> LLM分解子查询 -> 路由到不同的专家Agent -> 并行执行 -> 收集并展示结果。

# 步骤1：导入所需的库和模块
import asyncio  # 1.1 导入 asyncio 库，用于实现异步和并发操作
from python_a2a import AgentNetwork, AIAgentRouter, A2AClient, Task, Message, MessageRole, TextContent, TaskState, \
    TaskStatus  # 1.2 从 python_a2a 库导入 Agent 协作所需的核心类和对象
from langchain_openai import ChatOpenAI  # 1.3 导入 LangChain 的 ChatOpenAI，用于与大语言模型交互
from langchain_core.prompts import PromptTemplate  # 1.4 导入 LangChain 的 PromptTemplate，用于定义提示模板
from langchain_core.output_parsers import StrOutputParser  # 1.5 导入 LangChain 的 StrOutputParser，用于解析 LLM 输出为字符串
import json  # 1.6 导入 json 库，用于处理 JSON 格式的数据
import uuid  # 1.7 导入 uuid 库，用于生成唯一的任务 ID
from time import sleep  # 1.8 导入 sleep 函数，用于模拟处理延迟
from config import Config  # 1.9 导入自定义的 Config 类，用于加载配置信息
import re  # 1.10 导入 re 模块，用于正则表达式处理

# 步骤2：初始化配置和LLM
# 2.1 从配置文件加载配置
conf = Config()  # 2.1.1 实例化 Config 类，获取配置数据

# 2.2 配置 LLM 用于分解查询
decompose_llm = ChatOpenAI(  # 2.2.1 创建 ChatOpenAI 实例作为分解器 LLM
    model=conf.model_name,  # 2.2.2 指定使用的模型名称，如 'deepseek-chat'
    api_key=conf.api_key,  # 2.2.3 设置 API 密钥
    base_url=conf.api_url,  # 2.2.4 设置 API 基础 URL
    temperature=0,  # 2.2.5 设置温度为 0，确保输出稳定
    streaming=True  # 2.2.6 启用流式处理
)

# 2.3 定义分解查询的提示模板
decompose_prompt = PromptTemplate.from_template(""" 
# 2.3.1 使用 PromptTemplate 创建分解提示
将以下用户查询分解为独立的子查询，每个子查询对应一个单一意图。 
# 2.3.2 提示LLM进行任务分解
返回 JSON 格式的列表：{{"sub_queries": ["子查询1", "子查询2", ...]}} # 2.3.3 指定LLM的输出格式为JSON
示例： # 2.3.4 提供一个示例
查询: "预订票,查天气" # 2.3.5 示例输入
输出: {{"sub_queries": ["预订票", "查天气"]}} # 2.3.6 示例输出
查询: {query} # 2.3.7 将用户的实际查询作为变量传入
""")

# 2.4 构建分解链
decompose_chain = decompose_prompt | decompose_llm | StrOutputParser()  # 2.4.1 将提示模板、LLM和输出解析器串联成一个LangChain链


# 步骤3：主函数，执行多意图协作流程
async def main():
    # 3.1 创建 AgentNetwork
    network = AgentNetwork(name="TravelAgentNetwork")  # 3.1.1 实例化 AgentNetwork，作为管理Agent的中心

    # 3.2 添加专家代理到网络中
    network.add("TicketAgent", "http://127.0.0.1:5009")  # 3.2.1 添加票务代理的名称和URL
    network.add("WeatherAgent", "http://127.0.0.1:5008")  # 3.2.2 添加天气代理的名称和URL

    # 3.3 打印网络初始化信息
    print("[主控日志] AgentNetwork 初始化完成，已添加代理：")  # 3.3.1 打印提示信息
    for agent_info in network.list_agents():  # 3.3.2 遍历并打印网络中的所有Agent信息
        print(json.dumps(agent_info, indent=4, ensure_ascii=False))  # 3.3.3 格式化打印Agent的JSON信息
    print("-" * 50)  # 3.3.4 打印分隔线

    # 3.4 创建 AIAgentRouter
    router = AIAgentRouter(  # 3.4.1 实例化 AIAgentRouter
        llm_client=A2AClient("http://localhost:5555"),  # 3.4.2 连接到LLM服务器，用于路由决策
        agent_network=network  # 3.4.3 将 AgentNetwork 实例传递给路由器，以便它能知道有哪些 Agent 可用
    )

    # 3.5 定义测试查询列表（包括多意图）
    queries = [  # 3.5.1 定义一个包含不同查询的列表
        "帮我查下北京的天气",  # 3.5.2 单意图查询1
        "预订一张从北京到上海的火车票",  # 3.5.3 单意图查询2
        "预订一张从北京到上海的火车票,查询一下北京天气"  # 3.5.4 多意图查询
    ]

    # 3.6 循环处理每个查询
    for query in queries:  # 3.6.1 遍历查询列表
        print(f"[主控日志] 用户查询: '{query}'")  # 3.6.2 打印当前处理的查询

        # 3.7 使用 LLM 分解查询为子查询
        try:  # 3.7.1 使用 try-except 块处理可能的分词错误
            decompose_response = decompose_chain.invoke({"query": query})  # 3.7.2 调用分解链，将查询传给LLM进行分解
            decompose_response = re.sub(r'^```json\n|\n```$', '',
                                        decompose_response.strip())  # 3.7.3 使用正则表达式清理LLM输出中的JSON标记
            decompose_data = json.loads(decompose_response)  # 3.7.4 将清理后的字符串解析为JSON对象
            sub_queries = decompose_data.get("sub_queries", [query])  # 3.7.5 从JSON中获取子查询列表，如果失败则使用原始查询
        except Exception as e:  # 3.7.6 捕获并处理异常
            print(f"[主控日志] 分解错误: {str(e)}，使用原始查询")  # 3.7.7 打印错误信息
            sub_queries = [query]  # 3.7.8 发生错误时，将原始查询作为唯一的子查询
        print(f"[主控日志] query分解子任务结果: {sub_queries}")
        # 3.8 收集子查询任务
        tasks = []  # 3.8.1 创建一个空列表，用于存放所有要并行执行的异步任务
        agent_names = []  # 3.8.2 创建一个空列表，用于记录每个任务对应的Agent名称
        confidences = []  # 3.8.3 创建一个空列表，用于记录路由的置信度
        for sub_query in sub_queries:  # 3.8.4 遍历所有分解出的子查询
            agent_name, sub_confidence = router.route_query(sub_query)  # 3.8.5 调用路由器，为每个子查询选择最合适的Agent
            print(f"[主控日志] 子查询 '{sub_query}' 路由结果: {agent_name} (置信度: {sub_confidence})")  # 3.8.6 打印路由结果
            if agent_name and sub_confidence >= 0.5:  # 3.8.7 如果找到合适的Agent且置信度足够高
                agent_client = network.get_agent(agent_name)  # 3.8.8 从网络中获取该Agent的客户端实例
                if agent_client:  # 3.8.9 检查客户端是否成功获取
                    message = Message(  # 3.8.10 创建一个A2A消息对象
                        content=TextContent(text=sub_query),  # 3.8.11 消息内容为子查询
                        role=MessageRole.USER  # 3.8.12 消息角色为用户
                    )
                    task = Task(  # 3.8.13 创建一个A2A任务对象
                        id="task-" + str(uuid.uuid4()),  # 3.8.14 生成唯一的任务ID
                        message=message.to_dict()  # 3.8.15 将消息对象转换为字典格式
                    )
                    tasks.append(agent_client.send_task_async(task))  # 3.8.16 将异步发送任务的协程添加到任务列表中，这里异步并没有
                    agent_names.append(agent_name)  # 3.8.17 记录Agent名称
                    confidences.append(sub_confidence)  # 3.8.18 记录置信度

        # 3.9 计算整体置信度
        confidence = sum(confidences) / len(confidences) if confidences else 0.1  # 3.9.1 计算所有子查询置信度的平均值
        print("===========所有子查询置信度的平均值==============")
        print(confidence)
        print(f"[主控日志] 分解为子查询: {sub_queries} (置信度: {confidence:.2f})")  # 3.9.2 打印分解后的子查询和整体置信度

        # 3.10 并行执行任务
        if tasks:  # 3.10.1 检查任务列表是否非空
            results = await asyncio.gather(*tasks, return_exceptions=True)  # 3.10.2 使用 asyncio.gather 并行执行所有任务，并收集结果
            print("[主控日志]检查query拆解任务之后的所有 任务结果:")
            print( results)
            # 3.11 处理和打印任务结果
            for i, result in enumerate(results):  # 3.11.1 遍历所有任务结果
                if isinstance(result, Exception):  # 3.11.2 检查结果是否是异常（任务执行失败）
                    print(f"[主控日志] {agent_names[i]} 处理错误: {str(result)}")  # 3.11.3 打印错误信息
                else:  # 3.11.4 任务成功完成
                    print(f"[主控日志] {agent_names[i]} 收到完整响应：")  # 3.11.5 打印成功接收的提示
                    print(json.dumps(result.to_dict(), indent=4, ensure_ascii=False))  # 3.11.6 格式化打印完整的A2A任务响应

                    # 3.12 解析 artifacts 中的 parts
                    print(f"\n[主控日志] {agent_names[i]} 解析 artifacts 中的 parts：")  # 3.12.1 打印解析提示
                    for artifact in result.artifacts:  # 3.12.2 遍历任务响应中的所有 artifacts
                        if "parts" in artifact:  # 3.12.3 检查是否存在 parts 字段
                            for part in artifact["parts"]:  # 3.12.4 遍历 parts 列表
                                part_type = part.get("type")  # 3.12.5 获取 part 的类型
                                if part_type == "text":  # 3.12.6 如果类型是文本
                                    print(f"Text 结果: {part.get('text')}")  # 3.12.7 打印文本内容
                                elif part_type == "error":  # 3.12.8 如果类型是错误
                                    print(f"Error 消息: {part.get('message')}")  # 3.12.9 打印错误消息
                                elif part_type == "function_response":  # 3.12.10 如果类型是函数响应
                                    print(
                                        f"Function Response: name={part.get('name')}, response={part.get('response')}")  # 3.12.11 打印函数响应信息
                                else:  # 3.12.12 其他未知类型
                                    print(f"未知类型: {part}")  # 3.12.13 打印未知类型内容
        else:  # 3.13 如果任务列表为空
            print("[主控日志] 未找到合适代理")  # 3.13.1 打印未找到合适代理的提示

        print("-" * 50)  # 3.14 打印分隔线
        sleep(1)  # 3.15 暂停1秒，避免请求过快


# 步骤4：程序入口
if __name__ == "__main__":  # 4.1 检查是否为主程序入口
    print("请确保 ticket_agent.py 和 weather_agent.py 正在运行...")  # 4.2 打印运行前提示
    asyncio.run(main())  # 4.3 运行主协程函数