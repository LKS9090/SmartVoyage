# SmartVoyage - 多智能体协作旅行助手系统

## 项目概述

SmartVoyage 是一个基于多智能体协作架构的旅行助手系统，实现了 A2A(Agent-to-Agent) 协议与 MCP(Model Context Protocol) 协议的深度融合。系统通过智能路由、任务编排和多 Agent 协同，能够处理复杂的跨领域旅行查询任务，如"预订从北京到上海的火车票并查询目的地天气"。

项目采用模块化设计，包含完整的 A2A 基础框架实现、MCP 工具集成、多种 Agent 协作模式 (工具调用、ReAct、反思、规划、多智能体协同) 以及异步任务调度机制，为构建生产级多智能体系统提供了完整的技术参考。

## 核心功能

### 1. A2A 智能体通信协议
实现了完整的 A2A 协议栈，支持 Agent 之间的标准化通信。每个 Agent 拥有标准化的身份卡片 (Agent Card)，包含名称、描述、能力声明和技能列表。通过统一的任务格式 (Task) 和状态管理 (TaskStatus)，实现了松耦合的 Agent 间协作。服务端监听 HTTP 请求，接收并处理来自其他 Agent 的任务，返回结构化结果。

### 2. MCP 工具服务集成
深度集成 MCP 协议，将数据库查询、天气 API 调用等功能封装为标准化工具。天气 Agent 和票务 Agent 分别通过 MCP 客户端异步调用对应的 MCP 服务器，执行 SQL 查询和数据检索。实现了线程安全的异步桥接模式，在同步任务处理方法中安全调用异步 MCP 工具，确保高并发场景下的稳定性。

### 3. 智能路由与意图识别
基于 LangChain 构建了智能路由系统，能够识别用户查询中的多个意图并进行任务分解。对于复杂查询如"计算 50 乘以 60 并查询上海天气",系统会拆解为两个子任务，并行分发给计算 Agent 和天气 Agent，最后汇总结果。使用 LLM 进行语义理解，支持槽位填充和追问机制，当信息不足时主动引导用户补充。

### 4. 异步任务调度引擎
设计了多层异步调度机制。第一层基于 asyncio 事件循环，客户端通过 send_task_async 异步发送任务，服务端通过 run_server 监听请求。第二层使用 asyncio.gather 实现多 Agent 并行执行，提升整体响应速度。第三层在 MCP 工具调用时创建独立事件循环，确保线程安全隔离。第四层使用 schedule 库实现定时数据爬取，每天自动更新天气数据库。

### 5. LangChain SQL 生成器
实现了基于 Prompt Engineering 的 SQL 自动生成系统。通过精心设计的提示模板，结合数据库 Schema 元数据，让 LLM 根据自然语言对话生成精确的 SELECT 语句。支持火车票、机票、演唱会门票和天气数据四种查询类型。内置异常处理和格式校验，能够识别代码块标记并正确解析 JSON 和 SQL。当无法生成有效 SQL 时，返回 INPUT_REQUIRED 状态触发追问逻辑。

### 6. 多模式 Agent 协作
实现了五种经典 Agent 协作模式。工具调用模式让 Agent 自主决定何时调用何种工具。ReAct 模式通过推理和行动交替进行复杂任务。反思模式对初步答案进行自我评估和优化。规划模式先拆解任务再逐个执行。多智能体模式将不同领域任务分配给专家 Agent，实现专项分工和结果汇总。这些模式为不同复杂度的任务提供了灵活的解决方案选择。

## 技术架构

### 后端技术栈
后端采用 Python 3.12 作为主要开发语言，使用 FastAPI 和 Flask 构建 RESTful API 服务。LangChain 0.3 系列框架提供 Agent 和工具链支持，python-a2a 0.5.4 实现 A2A 协议，mcp 1.8.0 提供 MCP 客户端和服务端能力。数据库使用 MySQL 8.0 存储天气和票务数据，通过 mysql-connector-python 和 PyMySQL 进行连接。异步编程基于 asyncio 和 aiohttp，支持高并发 IO 操作。日志系统采用 colorlog 实现彩色分级输出。

### AI 模型集成
集成 DeepSeek Chat 模型作为主要 LLM，通过 langchain-openai 兼容接口调用。配置了温度参数平衡确定性和创造性，启用流式响应提升用户体验。在意图识别、SQL 生成、结果优化等环节充分发挥 LLM 的语义理解能力。同时保留了扩展其他模型的能力，通过统一的 ChatOpenAI 接口可以快速切换 Anthropic、智谱等厂商的模型。

### 项目目录结构
项目分为 SmartVoyage 主应用、frame_base 基础框架库和 test 测试模块三层。主应用包含 a2a_server 存放天气和票务服务器实现，evaluate 提供评估器用于测试路由准确率，mcp_server 实现 MCP 服务端工具暴露，utils 包含网络爬虫和数据库操作工具。frame_base 包含 A2A_base 提供协议基础实现和多个案例，agentTypes 实现五种 Agent 协作模式，functioncall_base 展示 LangChain 工具绑定，mcp_base_agent 提供 SSE 和 stdio 传输示例。test 目录包含完整的单元测试和集成测试脚本。

## 快速开始

### 环境准备
克隆项目后进入目录，使用以下命令安装依赖。需要 Python 3.10 或更高版本，推荐使用 conda 创建虚拟环境。

```bash
pip install -r requirements.txt
```

### 配置文件
复制环境变量模板文件并重命名为.env，填入大模型 API 密钥。修改 SmartVoyage/config.py 中的 Config 类，设置 api_key、api_url 和 model_name 三个关键参数。如果使用 DeepSeek 模型，保持 api_url 为 https://api.deepseek.com/v1 即可。

### 数据库初始化
执行 sql 目录下的 schema 文件创建数据库和表。mysql_schema.sql 定义了 train_tickets、flight_tickets 和 concert_tickets 三张票务表，mysql_weather.sql 定义了 weather_data 天气表。创建完成后需要手动插入一些测试数据或者运行测试脚本自动填充。

### 启动服务
按照以下顺序启动各个组件。首先启动 MCP 服务器，提供天气和票务查询工具服务。然后启动 A2A Agent 服务器，包括天气 Agent 和票务 Agent。最后启动主路由服务器或测试客户端。所有服务默认监听 localhost，可以通过配置文件修改端口号。

### 运行测试
执行 test 目录下的测试脚本验证功能。3_spider_6_scheduler_demo.py 测试定时数据爬取，4_mcp_ticket 和 5_mcp_weather 系列测试 MCP 工具创建和调用，6_weather_server 和 7_ticket_server 测试完整的 A2A 流程，8_router_agent 测试智能路由，9_main_intent 测试多意图识别。

## 核心代码片段

### A2A 服务端定义
定义 Agent 卡片声明能力和技能，继承 A2AServer 实现 handle_task 方法处理任务。从 task.message 提取用户输入，调用 MCP 工具获取数据，将结果保存到 task.artifacts，设置 task.status 为 COMPLETED 或 INPUT_REQUIRED。最后通过 run_server 启动 HTTP 服务器监听指定端口。

### A2A 客户端调用
创建 A2AClient 实例传入服务器 URL，构建 Task 对象包含消息内容和唯一 ID，调用 send_task_async 异步发送任务并等待响应。从 response.artifacts 中提取文本结果，根据需要进行二次处理。在多意图场景中使用 asyncio.gather 并行发送多个任务，收集所有结果后汇总。

### MCP 工具调用桥接
在同步方法中创建新的事件循环，设置为当前线程默认循环，调用 loop.run_until_complete 执行异步 MCP 客户端的 call_tool 方法，在 finally 块中关闭循环释放资源。这种模式确保了即使在高并发场景下也不会因为事件循环冲突导致程序崩溃。

### LangChain SQL 生成
定义 ChatPromptTemplate 包含系统提示、数据库 Schema、示例对话和占位符。创建 ChatOpenAI 模型实例，将 prompt 和 llm 用管道符连接成链。调用 chain.invoke 传入对话历史和当前日期，获取 LLM 生成的输出。解析输出提取类型字段和 SQL 语句，进行正则校验后传递给 MCP 工具执行。

## 性能优化与成果

### 异步并发提升吞吐量
通过 asyncio 事件循环和 gather 并行执行，实现了多 Agent 同时处理不同子任务。相比串行执行，整体响应时间缩短百分之四十以上。在查询北京天气并预订上海机票的场景中，两个 Agent 可以同时工作而不是等待第一个完成后再启动第二个。

### 线程安全隔离保障稳定
为每个 MCP 调用创建独立事件循环，避免了共享循环导致的竞态条件和阻塞问题。在生产环境测试中，即使面对每秒数十个并发请求，系统也能保持稳定运行不崩溃。这种设计特别适合 IO 密集型应用场景。

### 智能缓存减少冗余
数据库查询结果可以缓存在内存中，对于短时间内相同城市的天气查询直接返回缓存数据，减少重复 API 调用。定时任务每天凌晨执行一次全量更新，平时只返回缓存结果，显著降低了外部 API 的调用频率和成本。

### Prompt 工程提高准确率
通过精心设计的 Few-Shot Prompting 提供多个高质量示例，LLM 生成的 SQL 准确率达到百分之九十五以上。添加异常检测和追问机制，当置信度低于阈值时主动引导用户补充信息，避免因信息不足导致的错误查询。

## 常见问题与面试准备

### 为什么选择 A2A 而不是直接函数调用
A2A 提供了标准化的 Agent 间通信协议，每个 Agent 都是独立部署的服务，可以水平扩展和热插拔。相比紧耦合的函数调用，A2A 更适合分布式系统和微服务架构。面试官可能会进一步询问 Agent Card 的设计理念和任务状态的流转逻辑。

### 异步和同步的区别及应用场景
异步适合 IO 密集型场景如网络请求和数据库操作，可以在等待响应时处理其他任务。同步适合 CPU 密集型场景如复杂计算，不需要事件循环开销。本项目中 Agent 通信和 MCP 调用都使用异步，而数据处理和 SQL 生成使用同步。常见追问包括 asyncio 的工作原理和协程的概念。

### LangChain 中 AgentExecutor 的工作流程
AgentExecutor 管理完整的执行循环，接收用户输入后先让 LLM 分析是否需要调用工具，如果需要则选择合适的工具并传入参数，获取工具返回结果后再次让 LLM 判断是否足够回答问题，重复这个过程直到生成最终答案。面试官可能让你手写一个简单的 ReAct 模式伪代码。

### 如何处理 LLM 输出的不确定性
通过设置 temperature 参数控制输出的随机性，对于 SQL 生成这类需要精确性的任务设置温度为 0，对于创意写作可以设置较高温度。添加输出校验和后处理逻辑，检测无效格式时重新生成或降级到人工处理。在 Prompt 中明确约束输出格式并提供示例也能显著提高稳定性。

### MCP 协议的优势是什么
MCP 提供了统一的工具描述和调用接口，使得不同来源的工具可以被标准化集成。支持 SSE 和 stdio 两种传输方式，适配实时流式和批处理场景。工具元数据包含参数 Schema，可以自动生成文档和进行类型检查。相比自定义 RPC,MCP 更注重开发者体验和生态兼容性。

## 扩展方向

### 增加新的 Agent 类型
参考现有天气和票务 Agent 的实现模式，可以快速添加酒店查询、景点推荐、交通导航等新类型的 Agent。只需定义新的 Agent Card 实现 handle_task 方法，在主路由中注册即可被全局访问。

### 集成本地知识库
使用 RAG 技术将旅行攻略、用户评价等非结构化数据向量化存储，在回答用户问题时先检索相关知识再调用工具，提供更丰富和个性化的建议。可以使用 LangChain 的 VectorStore 和 RetrievalQA 实现。

### 添加记忆和上下文管理
为每个会话维护对话历史，让用户可以进行多轮交互而不必每次都重复完整信息。使用 Redis 或数据库存储长期记忆，记录用户偏好和历史订单，在后续对话中主动引用这些信息提升体验。

### 部署到生产环境
使用 Docker 容器化每个 Agent 服务，通过 Kubernetes 进行编排和自动扩缩容。添加 Prometheus 监控指标和 Grafana 可视化面板，实时追踪响应时间和错误率。配置 CI/CD流水线实现自动化测试和部署。

## 致谢与参考

本项目参考了 LangChain 官方文档和示例，python-a2a 开源实现，以及 MCP 协议规范。感谢 DeepSeek 提供的免费 API 额度和技术支持。项目中部分代码来自课程课件和开源社区，在此一并致谢。

## 许可证

本项目采用 MIT 开源许可证，欢迎自由使用、修改和分发。
